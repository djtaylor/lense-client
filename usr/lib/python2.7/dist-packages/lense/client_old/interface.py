from __future__ import print_function
import json
from copy import copy
from os import environ
from sys import exit, argv
from traceback import print_exc
from argparse import ArgumentParser, RawTextHelpFormatter

# Lense Libraries
from lense.common import init_project
from lense.client import ClientArgs, ClientModules, ClientAPI

class CLIClient(ClientModules):
    """
    Command line interface for making API requests.
    """
    def __init__(self):
        super(CLIClient, self).__init__()
    
        # API client and connection parameters
        self.client  = None
        self.connect = None
    
        # Arguments / modules objects
        self.args    = ClientArgs()
    
        # API connection attributes
        self._get_api_env()
    
    def _get_api_env(self):
        """
        Look for API connection environment variables.
        """
        
        # Look for environment connection variables
        # If any are found, store them and return
        _api = {}
        for k,v in {
            'api_user':  'LENSE_API_USER',
            'api_key':   'LENSE_API_KEY',
            'api_group': 'LENSE_API_GROUP'
        }.iteritems():
            if v in environ:
                self.args.set(k, environ[v])
    
    def _connect_api(self):
        """
        Establish an API connection using the client libraries.
        """

        # Look for any required arguments
        for a in ['api_user', 'api_group', 'api_key']:
            if not self.args.get(a):
                LENSE.die('Missing required argument "{0}"'.format(a))

        # Connection parameters
        params = {
            'user': self.args.get('api_user'), 
            'group': self.args.get('api_group'), 
            'api_key': self.args.get('api_key'), 
            'cli': True    
        }
        
        # Create the API client and connection objects
        self.client, self.connect = ClientAPI(**params).construct()
    
        # If token retrieval/connection failed
        if not self.client:
            LENSE.die('HTTP {0}: {1}'.format(self.connect['code'], self.connect['body'].get('error', 'An unknown error occurred')))
    
    def _list_actions(self, module):
        """
        List support actions for a module.
        """
        if self.args.get('list'):
            print('\nSupported actions for module "{0}":\n'.format(module.path))
            for a in module.actions():
                print('> {0}'.format(a))
            print('')
            exit(0)
    
    def interface(self):
        """
        Handle any command line arguments.
        """
        
        # Unsupported module
        if not self.getmod(self.args.get('module')):
            LENSE.die('\nUnsupported module "{0}"\n'.format(self.args.get('module')), pre=self.args.parser.print_help)
        
        # Handle incoming requests
        try:
            
            # Make an API connection
            self._connect_api()
            
            # Target module / action
            module = self.getmod(self.args.get('module'))(self.client)
            action = self.args.get('action')
            
            # If listing module actions
            self._list_actions(module)                
            
            # Unsupported module action
            if not action in module.actions():
                LENSE.die([
                    'Unsupported module action: {0}'.format(action),
                    'Supported actions are: {0}'.format(', '.join(module.actions()))
                ], pre=self.args.parser.print_help())

            # Get the client request method
            request = getattr(module, action)
            
            # If retrieving a token
            if (module.path == 'token') and (action == 'get'):
                response = {
                    'code': 200,
                    'body': {'token': self.connect.get('token') }
                }
            
            # Other request
            else:
                response = request(self.args.get('api_data', use_json=True))
            
            # Response attributes
            r_code   = response.get('code')
            r_body   = response.get('body')
            
            # Print the response
            print('HTTP {0}: {1}'.format(r_code, r_body if not isinstance(r_body, (list, dict)) else json.dumps(r_body)))
    
        # Error in handling arguments
        except Exception as e:
            print_exc()
            LENSE.die(str(e))