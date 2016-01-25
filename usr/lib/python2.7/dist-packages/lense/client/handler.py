import json
import requests
from sys import exit
from os import environ, path, unlink

# Lense Libraries
from lense.common import init_project
from lense.client.args import ClientArgs_CLI
from lense.client.common import ClientCommon
from lense.common.exception import ClientError
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

    def _load_data(self):
        """
        Load request data if supplied.
        """
        if self.kwargs.get('data', False):
            return json.loads(self.kwargs.get('data'))
        return None

    def print_response(self, content, code=200):
        """
        Print a successfull HTTP response.
        """
        try:
            content = '\n\n{0}\n'.format(json.dumps(content, indent=2))
        except:
            pass
        LENSE.FEEDBACK.success('HTTP {0}: {1}'.format(code, content))
        exit(0)

    def print_error_and_die(self, message, code):
        """
        Print a ClientError and quit the program.
        """
        LENSE.FEEDBACK.error('HTTP {0}: {1}'.format(code, message))
        exit(code)

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

        # Return the client
        return self

    def request(self, **kwargs):
        """
        Make a request to the API server.
        """
        path   = self.kwargs.get('path', self.path)
        method = self.kwargs.get('method', self.method)
        data   = self._get_data()
        
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
        self.authorize().run()

class ClientHandler_Mod(ClientHandler):
    """
    Class for handling module requests to the Lense client libraries.
    """
    def __init__(self, **kwargs):
        super(ClientHandler_Mod, self).__init__()
        
        # Load arguments
        self.kwargs = kwargs