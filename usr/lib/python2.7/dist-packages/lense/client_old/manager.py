import sys
import json
import requests
from os import environ
from os.path import expanduser, isfile

# Lense Libraries
from lense.common import config
from lense.client.base import APIBase
from lense.client import error_response
from lense.common.http import HEADER, MIME_TYPE, PATH

class ClientAPI(object):
    def __init__(self, user, group, api_key=None, api_token=None, cli=False):
        
        # API connection attributes
        self.api_user    = user       # API user
        self.api_group   = group      # API group
        self.api_key     = api_key    # API key
        self.api_token   = api_token  # API token
        
        # Is this being run from the command line client
        self.cli         = cli
        
        # Token response / cache file
        self.token_rsp   = None
        self.token_cache = 'LENSE_API_TOKEN'
        
        # Configuration
        self.conf        = config.parse('CLIENT')

        # Server URL
        self.api_url     = '{0}://{1}:{2}'.format(self.conf.engine.proto, self.conf.engine.host, self.conf.engine.port)

    def _cache_token_exists(self):
        """
        Check if the token cache exists and contains a non empty string.
        """
        if environ.get(self.token_cache, None):
            return True
        return False

    def _cache_token_get(self):
        """
        Retrieve a cached token string.
        """
        token_env = environ.get(self.token_cache, None)
        
        # If the token is set
        if token_env:
            return token_env
        
        # No cached token
        return False

    def _cache_token_set(self, token):
        """
        Cache the token if running from the command line.
        """
        
        # Set the environment variable
        environ[self.token_cache] = token
        
        # Return the token
        return token

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
        
        # If a token is cached
        if self._cache_token_exists():
            self.api_token = self._cache_token_get()
            return True
        
        # Authentication URL
        auth_url       = '{0}/{1}'.format(self.api_url, PATH.GET_TOKEN)
        
        # Get an API token
        self.token_rsp = requests.get(auth_url, headers=self._get_token_headers())
    
        # If token request looks OK
        if self.token_rsp.status_code == 200:
            token_data     = self.token_rsp.json()['data']
            self.api_token = self._cache_token_set(token_data['token'])
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