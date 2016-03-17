import json
import requests
from os.path import isfile
from exceptions import ValueError

# Lense Libraries
from lense.client import TOKEN_CACHE
from lense.common.http import HEADER, MIME_TYPE, PATH, HTTP_GET, HTTP_POST, HTTP_PUT

class ClientREST(object):
    """
    Class object for handling HTTP interactions with the API server
    on behalf of the client.
    """
    endpoint = '{0}://{1}:{2}'.format(
        LENSE.CONF.engine.proto, 
        LENSE.CONF.engine.host, 
        LENSE.CONF.engine.port
    )
    
    def __init__(self, user, group, key):
        
        # API user / group / key / token
        self.user     = user
        self.group    = group
        self.key      = key
        
        # API user token
        self.token    = self._get_token()
        
    def _get_endpoint(self):
        """
        Get the endpoint for the API server.
        """
        host  = LENSE.CONF.engine.host
        proto = LENSE.CONF.engine.proto
        port  = LENSE.CONF.engine.port
        
        # API server endpoint
        return '{0}://{1}:{2}'.format(proto, host, port)
        
    def _get_token(self):
        """
        Get a token for the API user.
        """
        
        # Has the token been cached
        if isfile(TOKEN_CACHE):
            with open(TOKEN_CACHE, 'r') as f:
                return f.read()
                
        # Request a token
        token = self.request(PATH.GET_TOKEN, HTTP_GET, data=None, extract='token')
        
        # Cache the token
        with open(TOKEN_CACHE, 'w') as f:
            f.write(token)
        
    def headers(self):
        """
        Get request headers.
        """
        return {
            HEADER.CONTENT_TYPE: MIME_TYPE.APPLICATION.JSON,
            HEADER.ACCEPT: MIME_TYPE.APPLICATION.JSON,
            HEADER.API_USER: self.user,
            HEADER.API_GROUP: self.group,
            HEADER.API_TOKEN: getattr(self, 'token', None),
            HEADER.API_KEY: self.key
        }
        
    def request(self, path, method, data, extract=False, ensure=True):
        """
        Make a request to the API endpoint.
        
        :param   path: The request path
        :type    path: str
        :param method: The request method
        :type  method: str
        :param   data: Optional request data
        :type    data: dict
        """
        method_handler = getattr(requests, method.lower())
        request_url    = '{0}/{1}'.format(self.endpoint, path)
        
        # Make the request
        response = method_handler(request_url, **self.request_params(method, data))
        
        # Make sure the response is OK
        if ensure:
            LENSE.CLIENT.ensure_request(response.status_code,
                value = 200,
                error = 'Request failed: HTTP {0}: {1}'.format(response.status_code, ClientREST.get_error(response)),
                debug = 'Request OK: path={0}, method={1}, user={2}, group={3}'.format(path, method, self.user, self.group),
                code  = response.status_code)
            
        # Return directly to the caller
        else:
            return LENSE.CLIENT.response(ClientREST.get_data(response), response.status_code) 
        
        # If extracting and returning a data key
        if extract:
            return LENSE.CLIENT.ensure(ClientREST.get_data(response, extract),
                isnot = None,
                error = 'Failed to extract key "{0}" from response data'.format(extract),
                code  = 500)
            
        # Return response data
        return LENSE.CLIENT.response(ClientREST.get_data(response), response.status_code)
    
    def request_params(self, method, data):
        """
        Construct request parameters to pass to Python requests module.
        """
        
        # Data key / data
        data_key = 'data' if method in [HTTP_POST, HTTP_PUT] else 'params'
    
        # Base parameters
        params   = { 'headers': self.headers() }
    
        # If data provided
        if data:
            params[data_key] = ClientREST.load_data(data_key, data)
    
        # Return request parameters
        return params
    
    @classmethod
    def load_data(cls, data_key, data_obj):
        """
        Load data argument into a JSON structure.
        """
        return json.loads(data_obj) if data_key == 'params' else data_obj
    
    @classmethod
    def get_error(cls, response):
        """
        Extract error message from an HTTP response.
        
        :param response: The Python requests response object
        :type  response: object
        """
        try:
            response_json = response.json()
            
            # Return the error message
            return LENSE.CLIENT.ensure(response_json.get('error', False),
                error = 'Could not find error message in HTTP response',
                code  = 500)
        except ValueError as e:
            return 'Internal server error. Please check Apache logs on the API server'
        
    @classmethod
    def get_data(cls, response, key=None, default=None):
        """
        Extract data from an HTTP response.
        
        :param response: The Python requests response object
        :type  response: object
        :param      key: Extract a key from data
        :type       key: str
        """
        response_json = response.json()
        
        # If the data key is present
        if 'data' in response_json:
            data = response_json.get('data')
            
            # Extract a specific key
            if key:
                return data.get(key, default)
            return data
            
        # No data found
        return {}
    
    @classmethod
    def request_anonymous(cls, path, method, data, extract=False):
        """
        Make an anonymous request to the API server.
        """
        method_handler = getattr(requests, method.lower())
        request_url    = '{0}/{1}'.format(cls.endpoint, path)
        
        # Make the request
        response = method_handler(request_url, headers={
            HEADER.CONTENT_TYPE: MIME_TYPE.APPLICATION.JSON,
            HEADER.ACCEPT: MIME_TYPE.TEXT.PLAIN
        }, params=data)
        
        # Make sure the response is OK
        LENSE.CLIENT.ensure_request(response.status_code,
            value = 200,
            error = 'Request failed: HTTP {0}: {1}'.format(response.status_code, cls.get_error(response)),
            debug = 'Request OK: path={0}, method={1}, user=anonymous, group=anonymous'.format(path, method),
            code  = response.status_code)
        
        # If extracting and returning a data key
        if extract:
            return LENSE.CLIENT.ensure(cls.get_data(response, extract),
                isnot = None,
                error = 'Failed to extract key "{0}" from response data'.format(extract),
                code  = 500)
            
        # Return response data
        return LENSE.CLIENT.response(cls.get_data(response), response.status_code)
    
    @classmethod
    def construct(cls, user, group, key):
        """
        Class method for constructing the client REST interface.
        """
        LENSE.CLIENT.REST = cls(user, group, key)