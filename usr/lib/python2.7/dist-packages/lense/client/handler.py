import requests
from json import loads as json_loads

# Lense Libraries
from lense.common import init_project
from lense.client.args import ClientArgs_CLI
from lense.common.http import HEADER, MIME_TYPE, PATH

class _ClientHandler(object):
    """
    Base class for both CLI and module client interfaces.
    """
    def __init__(self):
        """
        :param client_type: cli or mod
        :type  client_type: str
        """
        
        # User attributes
        self.user   = None
        self.group  = None
        self.key    = None
        self.token  = None
    
        # Request attributes
        self.path   = None
        self.method = None
        self.data   = None
    
        # Initialize commons
        init_project('CLIENT')

        # API server endpoint
        self.endpoint = '{0}://{1}:{2}'.format(LENSE.CONF.engine.proto, LENSE.CONF.engine.host, LENSE.CONF.engine.port)

    def _validate(self):
        """
        Validate client attributes prior to running.
        """
        for k in ['user', 'group', 'path', 'method']:
            if not hasattr(self, k) or not getattr(self, k, None):
                raise Exception('Missing required argument: {0}'.format(k))

    def _get_token_headers(self):
        """
        Construct request authorization headers for a token request.
        """
        return {
            HEADER.CONTENT_TYPE: MIME_TYPE.APPLICATION.JSON,
            HEADER.ACCEPT: MIME_TYPE.TEXT.PLAIN,
            HEADER.API_USER: self.user,
            HEADER.API_KEY: self.key,
            HEADER.API_GROUP: self.group 
        }

    def load_args(self, **kwargs):
        """
        Load attributes from child object.
        
        :param attrs: Argument attributes to load
        :type  attrs: dict
        """
        for k,v in kwargs.iteritems():
            if hasattr(self, k):
                setattr(self, k, v if not k == 'data' else json_loads(v))

    def _get_token(self):
        """
        Attempt to retrieve an API token for the user.
        """
        
        # Token already supplied
        if self.token:
            return True

        # Get an API token
        token_url = '{0}/{1}'.format(self.endpoint, PATH.GET_TOKEN)
        response  = requests.get(token_url, headers=self._get_token_headers())
    
        # If token request looks OK
        if response.status_code == 200:
            self.token = response.json()['data']
            return True
        print response.text

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
        print 'User: {0}'.format(self.user)
        print 'Group: {0}'.format(self.group)
        print 'Key: {0}'.format(self.key)
        print 'Token: {0}'.format(self.token)
        print 'Path: {0}'.format(self.path)
        print 'Method: {0}'.format(self.method)
        print 'Data: {0}'.format(self.data)

    def run(self):
        """
        Common method for running the client handler.
        """
        self._validate()
        
        # Retrieve a token
        self._get_token()
        
        # Return the request response
        return self.request()

class ClientHandler_CLI(_ClientHandler):
    """
    Class for handling command line requests to the Lense client libraries.
    """
    def __init__(self):
        super(ClientHandler_CLI, self).__init__()

        # Load arguments
        args = ClientArgs_CLI()
        self.load_args(**args.dict())

class ClientHandler_Mod(_ClientHandler):
    """
    Class for handling module requests to the Lense client libraries.
    """
    def __init__(self, **kwargs):
        super(ClientHandler_Mod, self).__init__()
        
        # Load arguments
        self.load_args(**kwargs)