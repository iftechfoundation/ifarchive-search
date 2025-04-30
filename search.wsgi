#!/usr/bin/env python3

"""
Search: Web app for IF Archive search

See tinyapp/app.py for how the underlying web app framework works.

This file (search.wsgi) is installed as /var/ifarchive/wsgi-bin/search.wsgi.
It can also be run to perform some command-line operations:

  python3 /var/ifarchive/wsgi-bin/search.wsgi
"""

import sys
import os
import configparser
import logging, logging.handlers
import threading

from whoosh.searching import TimeLimit

from tinyapp.handler import ReqHandler
from searchlib.searchapp import SearchApp
from searchlib.util import filehash, search_page_timeout

class han_Home(ReqHandler):
    def do_get(self, req):
        tem = self.app.getjenv().get_template('help.html')
        yield tem.render(approot=self.app.approot)
        
    def do_post(self, req):
        # Some forms 'searchstr'; some use 'searchbar' for IFDB compatibility.
        # We accept either form field name.
        searchstr = req.get_input_field('searchstr', '')
        if not searchstr:
            searchstr = req.get_input_field('searchbar', '')
        searchstr = searchstr.strip()

        pagelen = self.app.pagelen
        try:
            pagenum = int(req.get_input_field('pagenum', 1))
            pagenum = max(1, pagenum)
        except:
            pagenum = 1

        if not searchstr:
            tem = self.app.getjenv().get_template('help.html')
            yield tem.render(approot=self.app.approot, searchstr=searchstr)
            return

        if not self.app.queryparser or not self.app.searchindex:
            tem = self.app.getjenv().get_template('help.html')
            yield tem.render(approot=self.app.approot, searchstr=searchstr, message='The search index has not yet been built.')
            return

        try:
            query = self.app.queryparser.parse(searchstr)
        except Exception as ex:
            req.logwarning('search "%s" failed (%s)', searchstr, ex)
            tem = self.app.getjenv().get_template('help.html')
            yield tem.render(approot=self.app.approot, searchstr=searchstr, message='Your search query could not be parsed.')
            return

        try:
            with self.app.getsearcher() as searcher:
                results = search_page_timeout(searcher, query, pagenum, pagelen=pagelen, timeout=self.app.querytimeout)
                    
                resultcount = len(results)
                runtime = results.results.runtime

                pagestr = '' if (pagenum == 1) else ('page %d, ' % (pagenum,))
                req.loginfo('search "%s" (%d results, %s%.04f sec)', searchstr, resultcount, pagestr, runtime)
                
                resultobjs = []
                for res in results:
                    obj = dict(res.fields())
                    if obj.get('type') == 'dir':
                        obj['isdir'] = True
                    if 'date' in obj:
                        obj['datestr'] = obj['date'].strftime('%Y-%b-%d')
                    if 'path' in obj:
                        path = obj['path']
                        pathhead, _, pathtail = path.rpartition('/')
                        obj['pathhead'] = pathhead
                        obj['pathtail'] = pathtail
                        # We don't include the server for annoying urlencode reasons
                        if obj.get('type') == 'dir':
                            obj['url'] = 'indexes/if-archive/'+path
                        else:
                            dirname, _, filename = path.rpartition('/')
                            obj['url'] = 'indexes/if-archive/'+dirname
                            obj['urlfrag'] = filehash(filename)
                    resultobjs.append(obj)
    
                correctstr = None
                corrected = searcher.correct_query(query, searchstr)
                if corrected.query != query and corrected.string != searchstr:
                    correctstr = corrected.string
    
                result = res = None
                # end of searcher scope
                
        except TimeLimit as ex:
            req.logwarning('search "%s" timed out', searchstr)
            tem = self.app.getjenv().get_template('help.html')
            yield tem.render(approot=self.app.approot, searchstr=searchstr, message='Your search query took too long.')
            return

        pagecount = ((resultcount+pagelen-1) // pagelen)
        prevavail = (pagenum > 1)
        nextavail = (pagenum < pagecount)
        showmin = (pagenum-1) * pagelen + 1
        showmax = min(showmin+pagelen-1, resultcount)
                
        tem = self.app.getjenv().get_template('result.html')
        yield tem.render(approot=self.app.approot, searchstr=searchstr, correctstr=correctstr, results=resultobjs, resultcount=resultcount, pagenum=pagenum, pagecount=pagecount, prevavail=prevavail, nextavail=nextavail, showmin=showmin, showmax=showmax)

# We only have one handler.
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

        # The config file contains all the paths and settings used by the app.
        # The location is specified by the IFARCHIVE_CONFIG env var (if
        # on the command line) or the "SetEnv IFARCHIVE_CONFIG" line (in the
        # Apache WSGI environment).
        configpath = '/var/ifarchive/lib/ifarch.config'
        configpath = environ.get('IFARCHIVE_CONFIG', configpath)
        if not os.path.isfile(configpath):
            raise Exception('Config file not found: ' + configpath)
        
        config = configparser.ConfigParser()
        config.read(configpath)
        
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
