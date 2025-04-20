#!/usr/bin/env python3

import sys
import os
import logging, logging.handlers
import threading

from tinyapp.handler import ReqHandler
from searchlib.searchapp import SearchApp

class han_Home(ReqHandler):
    def do_get(self, req):
        tem = self.app.getjenv().get_template('search.html')
        yield tem.render(approot=self.app.approot)

handlers = [
    ('', han_Home),
]

appinstance = None
config = None
initlock = threading.Lock()

def create_appinstance(environ):
    """Read the configuration and create the TinyApp instance.
    
    We have to do this when the first application request comes in,
    because the config file location is stored in the WSGI environment,
    which is passed in to application(). (It's *not* in os.environ,
    unless we're calling this from the command line.)
    """
    global config, appinstance

    with initlock:
        # To be extra careful, we do this under a thread lock. (I don't know
        # if application() can be called by two threads at the same time, but
        # let's assume it's possible.)
        
        if appinstance is not None:
            # Another thread did all the work while we were grabbing the lock!
            return

        ###
        config = {
            'Search': {
                'SearchIndexDir': '/Users/zarf/src/ifarch/ifarchive-search/searchindex',
                'AppRoot': '/search',
                'LogFile': '/Users/zarf/src/ifarch/ifarchive-search/out.log',
                'TemplateDir': '/Users/zarf/src/ifarch/ifarchive-search/templates',
            }
        }
        ###
    
        # Set up the logging configuration.
        # (WatchedFileHandler allows logrotate to rotate the file out from
        # under it.)
        logfilepath = config['Search']['LogFile']
        loghandler = logging.handlers.WatchedFileHandler(logfilepath)
        logging.basicConfig(
            format = '[%(levelname).1s %(asctime)s] %(message)s',
            datefmt = '%b-%d %H:%M:%S',
            level = logging.INFO,
            handlers = [ loghandler ],
        )
        
        # Create the application instance itself.
        appinstance = SearchApp(config, handlers)

    # Thread lock is released when we exit the "with" block.

def application(environ, start_response):
    """The exported WSGI entry point.
    Normally this would just be appinstance.application, but we need to
    wrap that in order to call create_appinstance().
    """
    if appinstance is None:
        create_appinstance(environ)
    return appinstance.application(environ, start_response)


if __name__ == '__main__':
    import searchlib.cli
    create_appinstance(os.environ)
    searchlib.cli.run(appinstance)
