# graph.py
#
# Since we're not writing to the graph database through the web interface (at
# least not right now), we're just doing a GUI over DB.  This modules
# represents the basic read capabilities of the database.

from neo4jrestclient.client import GraphDatabase

# We can initialize the connection settings at the module level, so we don't
# have to do it everywhere else. --TCG
db = GraphDatabase('http://localhost:7474/db/data')
tagIndex = db.nodes.indexes.get("hashtags")
userIndex = db.nodes.indexes.get("users")
urlIndex = db.nodes.indexes.get("urls")

# This class would more accurately be called Node, but that might cause a naming
# conflict with the neo4jrestclient modules. --TCG
#class Hashtag(object):
#    """
#    Defines a single node. (For now, just a hashtag node)
#    """
#    def __init__(self, node):
#        self.node = node

# Following the command pattern for now.  It's probably overkill.
class NodeLookup(object):
    """
    Find a node by it's uid. (it's name)
    """
    def __init__(self, query):
        self.query = query

    def execute(self):
        fromindex = tagIndex['uid'][self.query]
        if (len(fromindex) < 1):
            raise KeyError("Node " + self.query + " not found.")

        node = fromindex[0]
        return node
