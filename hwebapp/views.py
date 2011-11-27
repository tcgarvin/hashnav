from pyramid.view import view_config
import hwebapp
from urllib import quote_plus #for the hack below

@view_config(name='', renderer='templates/homePage.pt', context=hwebapp.resources.Root)
def front_page(request):
    # Here, we do the url-encoding, though it should probably be handled by
    # either the template or by javascript, depending on the circumstances.
    return {"search_term": quote_plus("#thinksocial")};

@view_config(name='', renderer='json', context=hwebapp.resources.Hashtag)
def view_tag(context, request):
    print "In get_neighbors()"
    returnable = {'nodes': [], 'links':[]}
    returnable['nodes'].append({'name': context.node['uid'], 'group': 1})
    
    return returnable

#@view_config(name='test_json', renderer='json', context=hwebapp.resources.API)
#def test_json(context, request):
#    return {"Works": "True"}

@view_config(name='neighbors', renderer='json', context=hwebapp.resources.Hashtag)
def get_neighbors(context, request):
    neighbors = set()
    rels = context.node.relationships.outgoing()
    for r in rels:
        neighbors.add(r.start['uid'])

    return neighbors

@view_config(name='neighborhood', renderer='json', context=hwebapp.resources.Hashtag)
def get_neighborhood(context, request):
    returnable = {'nodes': [], 'links':[]}
    returnable['nodes'].append({'name': context.node['uid'], 'group': 1})
    rels = context.node.relationships.outgoing()

    cur = 1
    for r in rels:
        returnable['nodes'].append({'name': r.end['uid'], 'group': 2})
        returnable['links'].append({'source': cur, 'target': 0, 'value':1})
        cur += 1

    return returnable
