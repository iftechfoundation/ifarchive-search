import threading

from jinja2 import Environment, FileSystemLoader, select_autoescape
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.qparser.dateparse import DateParserPlugin

from tinyapp.app import TinyApp, TinyRequest
from tinyapp.handler import ReqHandler
import tinyapp.auth


class SearchApp(TinyApp):
    """SearchApp: The TinyApp class.
    """
    
    def __init__(self, config, hanclasses):
        TinyApp.__init__(self, hanclasses)

        self.searchindexdir = config['Search']['SearchIndexDir']
        self.approot = config['Search']['AppRoot']
        self.template_path = config['Search']['TemplateDir']

        # Thread-local storage for various things which are not thread-safe.
        self.threadcache = threading.local()

        self.searchindex = open_dir(self.searchindexdir)
        self.queryparser = QueryParser('description', self.searchindex.schema)
        self.queryparser.add_plugin(DateParserPlugin(free=True))

    def getjenv(self):
        """Get or create a jinja template environment. These are
        cached per-thread.
        """
        jenv = getattr(self.threadcache, 'jenv', None)
        if jenv is None:
            jenv = Environment(
                loader = FileSystemLoader(self.template_path),
                extensions = [
                ],
                autoescape = select_autoescape(),
                keep_trailing_newline = True,
            )
            jenv.globals['approot'] = self.approot
            #jenv.globals['appcssuri'] = self.app_css_uri
            self.threadcache.jenv = jenv
        return jenv

    def getsearcher(self):
        """Get or create a Whoosh searcher. These are cached per-thread.
        """
        searcher = getattr(self.threadcache, 'searcher', None)
        if searcher is None:
            # Create a new one
            searcher = self.searchindex.searcher()
        else:
            # Refresh it if the index files have changed
            searcher = searcher.refresh()
        # Either way, it's new (or might be) so we re-cache it
        self.threadcache.searcher = searcher
        return searcher
