import json
import requests
from sys import exit
from os import environ

# Lense Libraries
from lense.common import init_project
from lense.client.args import ClientArgs_CLI
from lense.client.params import ClientParams
from lense.common.http import HEADER, MIME_TYPE, PATH

class _ClientHandler(ClientParams):
    """
    Base class for both CLI and module client interfaces.
    """
    def __init__(self, cli=False):
        super(_ClientHandler, self).__init__()
        
        # CLI flag
        self.cli      = cli
        
        # User attributes
        self.user     = None
        self.group    = None
        self.key      = None
        self.token    = None
    
        # Request attributes
        self.path     = None
        self.method   = None
        self.data     = None
    
        # Server endpoint
        self.endpoint = None
    
        # Initialize commons
        init_project('CLIENT')

        # Bootstrap methods
        self._bootstrap()
        
    def _bootstrap(self):
        """
        Run bootstrap after commons has been initialized.
        """
        host  = LENSE.CONF.engine.host
        proto = LENSE.CONF.engine.proto
        port  = LENSE.CONF.engine.port
        
        # API server endpoint
        self.endpoint = '{0}://{1}:{2}'.format(proto, host, port)

    def _get_headers(self, token=None, key=None):
        """
        Construct request headers.
        """
        headers = {
            HEADER.CONTENT_TYPE: MIME_TYPE.APPLICATION.JSON,
            HEADER.ACCEPT: MIME_TYPE.TEXT.PLAIN,
            HEADER.API_USER: self.user,
            HEADER.API_GROUP: self.group 
        }
        
        # Token
        if token:
            headers[HEADER.API_TOKEN] = token
        
        # Key
        if key:
            headers[HEADER.API_KEY] = key

        # Return headers
        return headers

    def _http_response(self, content):
        """
        Show an HTTP response.
        """
        if self.cli:
            try:
                content = '\n\n{0}\n'.format(json.dumps(content, indent=2))
            except:
                pass
            LENSE.FEEDBACK.success('HTTP 200: {0}'.format(content))
            exit(0)

    def _http_error(self, code, error):
        """
        Show an error response.
        """
        if self.cli:
            LENSE.FEEDBACK.error('HTTP {0}: {1}'.format(code, error))
            exit(code)

    def _get_token(self):
        """
        Attempt to retrieve an API token for the user.
        """
        
        # Token already supplied
        if self.token:
            return True

        # Get an API token
        token_url = '{0}/{1}'.format(self.endpoint, PATH.GET_TOKEN)
        response  = requests.get(token_url, headers=self._get_headers(key=self.key))
    
        # If token request looks OK
        if response.status_code == 200:
            
            # Store and cache the token
            self.token = response.json()['data']['token']
            return True
        
        # Token retrieval failed
        self._http_error(response.status_code, response.json()['error'])

    def load_args(self, **kwargs):
        """
        Load attributes from child object.
        
        :param attrs: Argument attributes to load
        :type  attrs: dict
        """
        
        # Make sure required arguments are present
        for arg in self.manifest['options']:
            key      = arg['long']
            required = arg.get('required', False)
            value    = kwargs.get(key, None)
            use_json = arg.get('json', False)
            values   = arg.get('values', [])
            
            # Make sure required arguments are set
            if required and not value:
                LENSE.die('Missing required argument: {0}'.format(key))
        
            # If the argument supports only certain values
            if values and not value in values:
                LENSE.die('Unsupported value "{0}" for argument "{1}", options are: {2}'.format(value, key, ', '.join(values)))
        
            # Set the argument attribute
            setattr(self, key, value if not use_json else (None if not value else json.loads(value)))

    def request(self):
        """
        Make a request to the API server.
        
        :param   path: The request path
        :type    path: str
        :param method: The request method
        :type  method: str
        :param   data: Additional request data
        :type    data: dict
        """
        request_url    = '{0}/{1}'.format(self.endpoint, self.path)
        request_method = getattr(requests, self.method.lower())
        
        # Make the request
        response = request_method(request_url, headers=self._get_headers(token=self.token), params=self.data)
        
        # Request OK
        if response.status_code == 200:
            return self._http_response(response.json()['data'])
        
        # Request failed
        self._http_error(response.status_code, response.json()['error'])

    def run(self):
        """
        Common method for running the client handler.
        """
        
        # Retrieve a token
        self._get_token()
        
        # Return the request response
        return self.request()

class ClientHandler_CLI(_ClientHandler):
    """
    Class for handling command line requests to the Lense client libraries.
    """
    def __init__(self):
        super(ClientHandler_CLI, self).__init__(cli=True)

        # Load arguments
        self.load_args(**ClientArgs_CLI.parse())

class ClientHandler_Mod(_ClientHandler):
    """
    Class for handling module requests to the Lense client libraries.
    """
    def __init__(self, **kwargs):
        super(ClientHandler_Mod, self).__init__()
        
        # Load arguments
        self.load_args(**kwargs)