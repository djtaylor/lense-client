import sys
import json
import requests

# Lense Libraries
from lense.common import config
from lense.client.base import APIBase
from lense.common.http import HEADER, MIME_TYPE, PATH, parse_response, error_response

class APIConnect(object):
    """
    Factory class used to construct an API connection object using the APIBase class. If supplying
    an API key, a token will be retrieved then passed off to the APIBase class.
    """
    def __init__(self, user, group, api_key=None, api_token=None, cli=False):
        
        # API connection attributes
        self.api_user  = user       # API user
        self.api_group = group      # API group
        self.api_key   = api_key    # API key
        self.api_token = api_token  # API token
        
        # Is this being run from the command line client
        self.cli       = cli
        
        # Token response
        self.token_rsp = None
        
        # Configuration
        self.conf      = config.parse()

        # Server URL
        self.api_url   = '%s://%s:%s' % (self.conf.server.proto, self.conf.server.host, self.conf.server.port)

    def _get_token_headers(self):
        """
        Construct request authorization headers for a token request.
        """
        return {
            HEADER.CONTENT_TYPE: MIME_TYPE.APPLICATION.JSON,
            HEADER.ACCEPT:       MIME_TYPE.TEXT.PLAIN,
            HEADER.API_USER:     self.api_user,
            HEADER.API_KEY:      self.api_key,
            HEADER.API_GROUP:    self.api_group 
        }

    def _get_token(self):
        """
        Retrieve an authorization token if not supplied.
        """
        
        # If a token is already supplied
        if self.api_token:
            return True
        
        # Authentication URL
        auth_url       = '%s/%s' % (self.api_url, PATH.GET_TOKEN)
        
        # Get an API token
        self.token_rsp = parse_response(requests.get(auth_url, headers=self._get_token_headers()))
    
        # Load the response body
        self.token_rsp['body'] = json.loads(self.token_rsp['body'])
    
        # If token request looks OK
        if self.token_rsp['code'] == 200:
            
            # Load the authorization token
            self.api_token = self.token_rsp['body']['token']
        
            # Token retrieval OK
            return True
        
        # Failed to retrieve a token
        else:
            return False
    
    def construct(self):
        """
        Construct and return the API connection and parameters objects.
        """
        
        # Require an API key or token
        if not self.api_key and not self.api_token:
            error_response('Must supply either an API key or a token to make a request', cli=self.cli)
        
        # Retrieve a token if not supplied
        if not self._get_token():
            error_response('Failed to retrieve API token', response=self.token_rsp, cli=self.cli)  
            
        # API connector parameters
        self.params = {
            'user':  self.api_user,
            'group': self.api_group,
            'token': self.api_token,
            'url':   self.api_url,
            'key':   self.api_key
        }
            
        # Return the API client
        return APIBase(
            user  = self.api_user, 
            group = self.api_group,
            token = self.api_token, 
            url   = self.api_url,
            cli   = self.cli
        ), self.params