#-*-coding: utf-8 -*-
# ingest.py
# Injests a lite twitter data stream into the local neo4j graphdb.

import logging
from ConfigParser import SafeConfigParser
import tweetstream
import urllib
from neo4jrestclient.client import GraphDatabase

default_config_location = "ingest.conf"
sample_config_location = "ingest.conf.sample"

class Ingestion:
    """Each instance represents one ingestion action.  Intended to be used as a
singleton, though that is not enforced."""


    def __init__(self, url="", dryrun=False):
        self.db = None 
        self.tagIndex = None

        self.dryrun = dryrun

        if (not dryrun):
            logging.info('Accessing neo4j db at "' + url + '"')
            self.db = GraphDatabase(url)
            self.tagIndex = self.db.nodes.indexes.get("hashtags")
            self.userIndex = self.db.nodes.indexes.get("users")
            self.urlIndex = self.db.nodes.indexes.get("urls")

        #Initialize Counts
        self.tweets = 0
        self.tweets_with_hashtags = 0
        self.tweets_with_mentions = 0
        self.tweets_with_links = 0
        self.not_tweets = 0

    def index_item(self, index, item):
        found = index["uid"][item]
        logging.debug(found)
        node = None
        if (len(found) < 1):
            node = self.db.nodes.create(uid=item)
            index.add("uid", item, node)
            logging.debug("Created node for %s" % item)
        else:
            node = found[0]
            logging.debug("Found node for %s" % item)

        return node

    def link(self, nodeA, relationship, bNodes):
        for nodeB in bNodes:
            if (nodeA is not nodeB):
                nodeA.relationships.create(relationship,nodeB)

    @staticmethod
    def normalize_username(username):
        #We're going to make all usernames lowercase.  Later, we may also
        #store the username as twitter intends for it to be seen, but this
        #is handy for uid purposes.
        username = username.strip().lower()
        if username[0] != "@":
            username = "@" + username
        return username
        
    def process_tweet(self,tweet):
        """Link entities in neo4j"""
        tag_nodes = []
        user_nodes = []
        url_nodes = []
        entities = tweet["entities"]

        # Check to make sure there is at least one relationship
        if (len(entities["hashtags"]) + len(entities["user_mentions"])
                + len(entities["urls"]) <= 2):
            return

        #Gather each entity, ensure existence in neo4j
        for tag in entities['hashtags']:
            #We want to ignore case in tags.
            tag_text = "#" + tag["text"].lower()
            tag_nodes.append(self.index_item(self.tagIndex, tag_text))

        for user in entities['user_mentions']:
            user_text = self.normalize_username(user["screen_name"])
            user_nodes.append(self.index_item(self.userIndex, user_text))

        for url in entities['urls']:
#             print url["url"]
            try:
                long_url = urllib.urlopen(url["url"])
            except IOError: 
                print "IOError in url proccessing." 
            else:
                if long_url.getcode() == 200:
                    url_nodes.append(self.index_item(self.urlIndex, long_url.url))
                else: 
                    url_nodes.append(self.index_item(self.urlIndex, url["url"]))

        if tag_nodes:
            self.tweets_with_hashtags += 1

        if user_nodes:
            self.tweets_with_mentions += 1

        if url_nodes:
            self.tweets_with_links += 1

        #Potential Relationships to be graphed..  need to decide if 
        #All entities collected (nodes created/found), now we draw edges.
        #User -> Posted -> Hashtag
        #User -> Posted -> URL
        #User -> Posted -> User
        #
        #User -> RT'd -> User  (Directional Relationship)
        #RT'd user -> Posted(Update) -> Hashtag, URL, User
        #Hashtag -> PostedWith -> Hashtag
        #Hashtag -> Tagged -> User (Even if the user is being RT'd?)
        #Hashtag -> Tagged -> URL
        #URL -> PostedWith -> URL
        #URL -> Tagged -> Hashtag
        #URL -> PostedWith -> User (Again, even if the user is being RT'd?)
        #User -> PostedWith -> User (not for RTs)
        #User -> PostedWith -> URL
        #User -> Tagged -> Hashtag

        # It's probably not too useful to keep track of who's posting, because
        # we get such a small % of tweets.  We can always put this back if we
        # need to.
        #
        # If there are entities to link to: link the author to each one.
        # author_name = self.normalize_username(tweet["user"]["screen_name"])
        # author = self.index_item(self.userIndex, author_name)
        # self.link(author, "Posted", tag_nodes)
        # self.link(author, "Posted", url_nodes)
        # self.link(author, "Posted", user_nodes)

        # For each entity we've gathered, link it with all the other entities.
        for tag in tag_nodes:
            self.link(tag, "PostedWith", tag_nodes)
            self.link(tag, "PostedWith", url_nodes)
            self.link(tag, "PostedWith", user_nodes)

        for url in url_nodes:
            self.link(url, "PostedWith", tag_nodes)
            self.link(url, "PostedWith", url_nodes)
            self.link(url, "PostedWith", user_nodes)
            
        for user in user_nodes:
            self.link(user, "PostedWith", tag_nodes)
            self.link(user, "PostedWith", url_nodes)
            self.link(user, "PostedWith", user_nodes)

                #All entities collected (nodes created/found), now we draw edges.
                #User -> Posted -> Hashtag
                #User -> Posted -> URL
                #User -> Posted -> User
                #User -> RT'd -> User
                #RT'd user -> RT'dBy -> User
                #RT'd user -> Posted(Update) -> Hashtag, URL, User
                #Hashtag -> PostedWith -> Hashtag
                #Hashtag -> PostedWith -> User (Not if the user is being RT'd)
                #Hashtag -> PostedWith -> URL
                #URL -> PostedWith -> URL
                #URL -> PostedWith -> Hashtag
                #URL -> PostedWith -> User (Again, not if the user is being RT'd)
                #User -> PostedWith -> User (not for RTs)
                #User -> PostedWith -> URL
                #User -> PostedWith -> Hashtag

    def process_twitter_stream(self,username, password):
    
        #Initialize Connection to twitter
        stream = tweetstream.SampleStream(username, password)

        #process tweets until an exception or a keyboard interrupt
        try:
            for tweet in stream:
                #Verify a valid tweet
                if "entities" not in tweet:
                    self.not_tweets += 1
                    continue #Stop processing this not-a-tweet, goto next.

                self.tweets += 1
                
                #DEBUG CODE
                #print tweet
                #print ""
                logging.info(tweet["text"])
                logging.debug(tweet)

                #print "User: %s" % tweet["user"]["screen_name"]
                #print "Mentions/replies: %s" % tweet["entities"]["user_mentions"]
                #print "Tags: %s" % hashtags
                #print "Urls: %s" % tweet["entities"]["urls"]

                #print "Checking for hashtag existance:" 

                if (not self.dryrun):
                    self.process_tweet(tweet)

        except KeyboardInterrupt:
            lines = self.tweets + self.not_tweets
            print "Stats:"
            print "%d lines" % lines
            print "%d tweets" % self.tweets
            print "%d tweets with hashtags" % self.tweets_with_hashtags
            print
            print "%.2f%% of lines were invalid (not tweets)" % (100*(1 - (float(self.tweets)/lines)))
            print "%.2f%% of tweets had hashtags" % (100*(float(self.tweets_with_hashtags) / self.tweets))
            print "%.2f%% of tweets had mentions" % (100*(float(self.tweets_with_mentions) / self.tweets))
            print "%.2f%% of tweets had links" % (100*(float(self.tweets_with_links) / self.tweets))

    #End process_tweets()
#End class Ingestion
    
# Main Program
if __name__ == "__main__":
    # We only use these libraries when running as a script.
    from os import sys
    import argparse

    # Parse Arguments
    argparser = argparse.ArgumentParser(description="Ingests twitter's streaming/sample feed.")
    argparser.add_argument('-c', '--config',
        help="config file to use. Defaults to " + default_config_location + ".",
        action="store")
    argparser.add_argument('-d', '--dry',
        help="perform a dry run, no database access. (Implies -v)",
        action="store_true")
    argparser.add_argument('-v', help="verbose", action="store_true")
    argparser.add_argument('--debug',
        help="enable debugging code. (Implies -v)",
        action="store_true")
    args = argparser.parse_args()

    # Logical conclusion of args
    if args.dry:
        args.v = True

    if args.config is None:
       args.config = default_config_location

    #Load Config
    config = SafeConfigParser()
    try :
        fp = open(args.config)
        config.readfp(fp)
        fp.close()
    except Exception as e:
        print "Error loading", args.config + ":", e, e.message
        print "If unsure how to config, see", sample_config_location
        sys.exit(1)


    # Set up Logging
    logging_level = logging.WARNING
    if (args.debug):
        logging_level = logging.DEBUG
    elif (args.v):
        logging_level = logging.INFO

    logging.basicConfig(level=logging_level)

    while True:
        #The Ingestion Action
        db = Ingestion(config.get("neo4j", "db_url"),
             dryrun=args.dry)
        try:
            db.process_twitter_stream(config.get("twitter", "username"),
                              config.get("twitter", "password"))
        except tweetstream.ConnectionError:
            print "ConnectionError caught."
