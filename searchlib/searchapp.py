import threading

from jinja2 import Environment, FileSystemLoader, select_autoescape

from tinyapp.app import TinyApp, TinyRequest
from tinyapp.handler import ReqHandler
import tinyapp.auth

class SearchApp(TinyApp):
    """SearchApp: The TinyApp class.
    """
    
    def __init__(self, config, hanclasses):
        TinyApp.__init__(self, hanclasses)

        self.approot = config['Search']['AppRoot']
        self.template_path = config['Search']['TemplateDir']

        # Thread-local storage for various things which are not thread-safe.
        self.threadcache = threading.local()

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

