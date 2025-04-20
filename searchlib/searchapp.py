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

        # Thread-local storage for various things which are not thread-safe.
        self.threadcache = threading.local()
