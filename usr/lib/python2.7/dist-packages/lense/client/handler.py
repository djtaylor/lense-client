import json
import requests
from sys import exit
from os import environ, path, unlink

# Lense Libraries
from lense.client.args import ClientArgs_CLI
from lense.client.common import ClientCommon
from lense.common.http import HEADER, MIME_TYPE, PATH
from lense.client.rest import RESTInterface

class ClientHandler(ClientCommon):
    """
    Base class for both CLI and module client interfaces.
    """
    def __init__(self):
        super(ClientHandler, self).__init__()
        
        # Client command
        self.command  = None
        
        # User attributes
        self.user     = None
        self.group    = None
        self.key      = None
        self.token    = None
    
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

    def load_args(self, **kwargs):
        """
        Load attributes from child object.
        
        :param attrs: Argument attributes to load
        :type  attrs: dict
        """
        
        # Store the command
        self.command = kwargs.get('command')
        
        # Make sure required arguments are present
        for arg in self.manifest['options']:
            key      = arg['long']
            required = arg.get('required', False)
            value    = kwargs.get(key, None)
            use_json = arg.get('json', False)
            values   = arg.get('values', [])
            commands = arg.get('commands', [])
            
            # Do the arguments apply to the current command
            if self.command in commands:
            
                # Make sure required arguments are set
                if required and not value:
                    LENSE.die('Missing required argument: {0}'.format(key))
            
                # If the argument supports only certain values
                if values and not value in values:
                    LENSE.die('Unsupported value "{0}" for argument "{1}", options are: {2}'.format(value, key, ', '.join(values)))
        
            # Set the argument attribute
            setattr(self, key, value if not use_json else (None if not value else json.loads(value)))

        # Bootstrap after loading arguments
        self._bootstrap()

    def request(self, **kwargs):
        """
        Make a request to the API server.
        """
        path   = kwargs.get('path', self.path)
        method = kwargs.get('method', self.method)
        data   = kwargs.get('data', self.data)
        
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
        init_project('CLIENT')
        super(ClientHandler_CLI, self).__init__()

        # Load arguments
        self.load_args(**ClientArgs_CLI.parse())

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

class ClientHandler_Mod(ClientHandler):
    """
    Class for handling module requests to the Lense client libraries.
    """
    def __init__(self, **kwargs):
        super(ClientHandler_Mod, self).__init__()
        
        # Load arguments
        self.load_args(**kwargs)