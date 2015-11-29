import json
import requests

# Lense Libraries
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
            
            # Extract the error message
            msg = parsed['body'] if not isinstance(parsed['body'], dict) else parsed['body']['message']
            
            # Return an error response
            error_response(msg, response=parsed, cli=self.cli)

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