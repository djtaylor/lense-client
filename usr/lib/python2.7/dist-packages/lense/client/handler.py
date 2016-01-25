import json
import requests
from sys import exit
from os import environ, path, unlink

# Lense Libraries
from lense.common import init_project
from lense.client.args import ClientArgs_CLI
from lense.client.common import ClientCommon
from lense.common.exceptions import ClientError
from lense.common.http import HEADER, MIME_TYPE, PATH
from lense.client.rest import RESTInterface

class ClientHandler(ClientCommon):
    """
    Base class for both CLI and module client interfaces.
    """
    def __init__(self):
        super(ClientHandler, self).__init__()
        
        # Client command / keyword arguments
        self.command  = None
        self.kwargs   = None
        
        # User attributes
        self.user     = None
        self.group    = None
        self.key      = None
    
        # Request attributes
        self.path     = None
        self.method   = None
        self.data     = None
        
        # REST interface
        self.rest     = None

    def _bootstrap(self):
        """
        Bootstrap methods after loading arguments.
        """
        self.rest = RESTInterface(self.user, self.group, self.key)

    def _load_data(self, data):
        return json.loads(data) if data else None

    def http_response(self, content, code=200):
        """
        Print a successfull HTTP response.
        """
        try:
            content = '\n\n{0}\n'.format(json.dumps(content, indent=2))
        except:
            pass
        LENSE.FEEDBACK.success('HTTP {0}: {1}'.format(code, content))
        exit(0)

    def http_error(self, message, code):
        """
        Print an HTTP request error.
        """
        LENSE.FEEDBACK.error('HTTP {0}: {1}'.format(code, message))
        exit(code)

    def error(self, message):
        """
        Print a ClientError message.
        """
        LENSE.FEEDBACK.error(message)
        exit(1)

    def authorize(self):
        """
        Public method for authorizing a user account.
        """
        for k in ['user', 'group', 'key']:
            if not self.kwargs.get(k, False):
                raise ClientError('Missing required authorization key: {0}'.format(k))
        
        # User attributes
        self.user  = self.kwargs.get('user')
        self.group = self.kwargs.get('group')
        self.key   = self.kwargs.get('key')

        # Store the command
        self.command = self.kwargs.get('command')

        # Bootstrap the client
        self._bootstrap()

    def request(self, **kwargs):
        """
        Make a request to the API server.
        """
        
        # Load request attributes
        path   = kwargs.get('path', self.kwargs.get('path', None))
        method = kwargs.get('method', self.kwargs.get('method', None))
        data   = self._load_data(kwargs.get('data', self.kwargs.get('data', None)))
        
        # Path / method required
        if not path or not method:
            raise ClientError('Request attributes "path" and "method" required')
        
        # Make the API request
        return self.rest.request(path, method, data)

    def noop(self):
        return True

    def run(self):
        """
        Common method for running the client handler.
        """
        commands = {
            'request': self.request,
            'cache': self.noop,
            'support': self.noop
        }
        
        # Run the command
        if self.command in commands:
            return commands[self.command]()
        
        # Unsupported command
        LENSE.die("Unsupported command: {0}".format(self.command))

class ClientHandler_CLI(ClientHandler):
    """
    Class for handling command line requests to the Lense client libraries.
    """
    def __init__(self):
        
        # Initialize the project
        init_project('CLIENT')
        
        # Run the parent client class
        super(ClientHandler_CLI, self).__init__()

    def bootstrap(self):
        """
        Public method for bootstrapping the client.
        """
        self.kwargs = ClientArgs_CLI.parse()
        
        # Authorize the user account run the client
        self.authorize()
        self.run()

class ClientHandler_Mod(ClientHandler):
    """
    Class for handling module requests to the Lense client libraries.
    """
    def __init__(self, **kwargs):
        super(ClientHandler_Mod, self).__init__()
        
        # Load arguments
        self.kwargs = kwargs