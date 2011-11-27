from hwebapp.graph import NodeLookup

# This class would more accurately be called Node, but that might cause a naming
# conflict with the neo4jrestclient modules. --TCG
class Hashtag(object):
    """
    Context for a single node. (For now, just a hashtag node)
    """
    def __init__(self, node):
        print "Accessing " + str(node)
        self.node = node

class HashtagLookup(object):
    """
    The "get tag by it's uid (name)" part of the api.
    """
    def __getitem__(self,query):
        nl = NodeLookup(query)
        return Hashtag(nl.execute())
    

class API(object):
    """
    Placeholder.  Nothing happens unless you give a query
    """
    queries = {"tag": HashtagLookup}

    def __getitem__(self, query):
        return self.queries[query]()

class Root(object):
    site = {"api": API}

    def __init__(self, request):
        self.request = request

    def __getitem__(self, branch):
        return self.site[branch]()
