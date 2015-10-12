import sys
import json
import requests
import importlib

# Lense Libraries
from lense.common.vars import LENSE_CONFIG
from lense.common.http import HEADER, MIME_TYPE, parse_response, error_response

class APIBase(object):
    """
    The base class inherited by API path specific classes. This class provides access to
    command methods to GET and POST data to the API server.
    """
    def __init__(self, user=None, group=None, token=None, url=None, cli=False):

        # API User / Group / Token / URL / Headers
        self.API_USER    = user
        self.API_TOKEN   = token
        self.API_GROUP   = group
        self.API_URL     = url
        self.API_HEADERS = self._construct_headers()

        # Command line flag
        self.cli         = cli

        # Construct the API map
        self._construct_map()

    def _construct_headers(self):
        """
        Construct the request authorization headers.
        """
        return {
            HEADER.CONTENT_TYPE: MIME_TYPE.APPLICATION.JSON,
            HEADER.ACCEPT:       MIME_TYPE.TEXT.PLAIN,
            HEADER.API_USER:     self.API_USER,
            HEADER.API_TOKEN:    self.API_TOKEN,
            HEADER.API_GROUP:    self.API_GROUP
        }

    def _construct_map(self):
        """
        Method to construct the API request objects.
        """

        # Load the mapper JSON manifest
        map_json = None
        with open(LENSE_CONFIG.MAPPER, 'r') as f:
            map_json = json.loads(f.read())

        # Set the modules base
        mod_base = map_json['base']
        
        # Load each module
        for mod in map_json['modules']:
            api_mod = '{0}.{1}'.format(mod_base, mod['module'])
            
            # Load the API endpoint handler
            ep_mod   = importlib.import_module(api_mod)
            ep_class = getattr(ep_mod, mod['class'])
            ep_inst  = ep_class(self)
            
            # Set the internal attribute
            setattr(self, mod['id'], ep_inst)

    def _return(self, response):
        """
        Parse and return the response.
        """
        
        # Parse the response
        parsed = parse_response(response)
        
        # Parse the body
        try:
            parsed['body'] = json.loads(parsed['body'])
        except:
            pass
        
        # If there was an error during the request
        if parsed['code'] != 200:
            error_response(parsed['body']['message'], response=parsed, cli=self.cli)

        # Return a successfull response
        return parsed
    
    def _delete(self, path, data={}):
        """
        Wrapper method to make DELETE requestes to an API utility.
        """
        
        # Set the request URL to the API endpoint path
        get_url = '{0}/{1}'.format(self.API_URL, path)
        
        # POST the request and get the response
        response = requests.delete(get_url, headers=self.API_HEADERS, params=data)
        
        # Return a response
        return self._return(response)

    def _put(self, path, data={}):
        """
        Wrapper method to make PUT requests to an API utility.
        """
        
        # Set the request URL to the API endpoint path
        get_url = '{0}/{1}'.format(self.API_URL, path)
        
        # POST the request and get the response
        response = requests.put(get_url, headers=self.API_HEADERS, params=data)
        
        # Return a response
        return self._return(response)

    def _get(self, path, data={}):
        """
        Wrapper method to make GET requests to an API utility.
        """
        
        # Set the request URL to the API endpoint path
        get_url = '{0}/{1}'.format(self.API_URL, path)
        
        # POST the request and get the response
        response = requests.get(get_url, headers=self.API_HEADERS, params=data)
        
        # Return a response
        return self._return(response)

    def _post(self, path, data={}):
        """
        Wrapper method to make POST requests an API utility.
        """
        
        # Set the request URL to the API endpoint path
        post_url = '{0}/{1}'.format(self.API_URL, path)
        
        # POST the request and get the response
        response = requests.post(post_url, headers=self.API_HEADERS, data=json.dumps(data))
        
        # Return a response
        return self._return(response)