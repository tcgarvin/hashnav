from pyramid.config import Configurator
from hwebapp.resources import Root

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=Root, settings=settings)
    config.add_static_view('static', 'hwebapp:static', cache_max_age=3600)
    #config.add_view('hwebapp.views.my_view',
    #                context='hwebapp:resources.Root',
    #                renderer='hwebapp:templates/staticData.pt')
    config.scan()
    return config.make_wsgi_app()
