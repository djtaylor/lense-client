from __future__ import print_function
import os
import re
import sys
import json
import argparse
import importlib
import traceback
from copy import copy

# Lense Libraries
from lense.common.vars import CONFIG
from lense.client.manager import APIConnect
from lense.common.utils import format_action
from lense.common.objects import JSONObject
from lense.client.module import ClientModules

# Client modules
MODULES = ClientModules()

class ClientArgs(object):
    """
    Class object for handling command line arguments.
    """
    def __init__(self):

        # Arguments parser / object
        self.parser  = None
        self._args   = None
        
        # Construct arguments
        self._construct()
        
    def _json_load_recursive(self, json_str):
        """
        Process a string as many times as needed to make a pure Python object.
        """
        
        # If the argument is empty
        if not json_str: return None
        
        # If the argument is already an object
        if isinstance(json_str, dict):
            return json_str
        
        # Initial data load
        json_data = json.loads(json_str)
        
        # Recurse if not fully converted
        if not isinstance(json_data, dict):
            return self._json_load_recursive(json_data)
        return json_data
        
    def list(self):
        """
        Return a list of argument keys.
        """
        return self._args.keys()
        
    def _return_help(self):
         return ("Lense API Client\n\n"
                 "A utility designed to handle interactions with the Lense API client manager.\n"
                 "Supports most of the API endpoints available.\n")
        
    def _construct(self):
        """
        Construct the argument parser.
        """
        
        # Create a new argument parsing object and populate the arguments
        self.parser = argparse.ArgumentParser(description=self._return_help(), formatter_class=argparse.RawTextHelpFormatter)
        self.parser.add_argument('module', help=MODULES.help_prompt())
        self.parser.add_argument('action', nargs='?', help="The action to perform against the endpoint", action='append')
        
        # Load client switches
        self.parser.add_argument('-u', '--api-user', help='The API user to authenticate with if not set as the environment variable "LENSE_API_USER"', action='append')
        self.parser.add_argument('-g', '--api-group', help='The API user group to authenticate with if not set as the environment variable "LENSE_API_GROUP"', action='append')
        self.parser.add_argument('-k', '--api-key', help='The API key to authenticate with if not set as the environment variable "LENSE_API_KEY"', action='append')
        self.parser.add_argument('-d', '--api-data', help='Optional data to pass during the API request, must be a valid JSON string', action='append')
        self.parser.add_argument('-l', '--list', help='Show supported actions for a specified module', action='store_true')
        
        # Parse CLI arguments
        sys.argv.pop(0)
        self._args = vars(self.parser.parse_args(sys.argv))
        
    def set(self, k, v):
        """
        Set a new argument or change the value.
        """
        self._args[k] = v
        
    def get(self, k, default=None, use_json=False):
        """
        Retrieve an argument passed via the command line.
        """
        
        # Get the value from argparse
        _raw = self._args.get(k)
        _val = (_raw if _raw else default) if not isinstance(_raw, list) else (_raw[0] if _raw[0] else default)
        
        # Return the value
        return _val if not use_json else self._json_load_recursive(_val)

class CLIClient(object):
    """
    Command line interface for making API requests.
    """
    def __init__(self):
    
        # API client and connection parameters
        self.client  = None
        self.connect = None
    
        # Arguments / modules objects
        self.args    = ClientArgs()
    
        # API connection attributes
        self._get_api_env()
    
    def _die(self, msg, code=None, pre=None, post=None):
        """
        Print on stderr and die with optional exit code.
        """
        
        # Optional pre-failure method
        if pre and callable(pre):
            pre()
        
        # Write the error message to stderr
        if isinstance(msg, list):
            for l in msg:
                sys.stderr.write(l)
        else:
            sys.stderr.write('{0}\n'.format(msg))
        
        # Optional post-failure method
        if post and callable(post):
            post()
        
        # Exit with the optional code
        sys.exit(code if (code and isinstance(code, int)) else 1)
    
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
            if v in os.environ:
                self.args.set(k, os.environ[v])
    
    def _connect_api(self):
        """
        Establish an API connection using the client libraries.
        """

        # Look for any required arguments
        for a in ['api_user', 'api_group', 'api_key']:
            if not self.args.get(a):
                self._die('Missing required argument "{0}"'.format(a))

        # Connection parameters
        params = {
            'user': self.args.get('api_user'), 
            'group': self.args.get('api_group'), 
            'api_key': self.args.get('api_key'), 
            'cli': True    
        }
        
        # Create the API client and connection objects
        self.client, self.connect = APIConnect(**params).construct()
    
        # If token retrieval/connection failed
        if not self.client:
            self._die('HTTP {0}: {1}'.format(self.connect['code'], self.connect['body'].get('error', 'An unknown error occurred')))
    
    def _list_actions(self, module):
        """
        List support actions for a module.
        """
        if self.args.get('list'):
            print('\nSupported actions for module "{0}":\n'.format(module.path))
            for a in module.actions():
                print('> {0}'.format(a))
            print('')
            sys.exit(0)
    
    def interface(self):
        """
        Handle any command line arguments.
        """
        
        # Unsupported module
        if not MODULES.get(self.args.get('module')):
            self._die('\nUnsupported module "{0}"\n'.format(self.args.get('module')), pre=self.args.parser.print_help)
        
        # Handle incoming requests
        try:
            
            # Make an API connection
            self._connect_api()
            
            # Target module / action
            module = MODULES.get(self.args.get('module'))(self.client)
            action = self.args.get('action')
            
            # If listing module actions
            self._list_actions(module)                
            
            # Unsupported module action
            if not action in module.actions():
                self._die([
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
            traceback.print_exc()
            self._die(str(e))
            
def cli():
    """
    Entry point method for the 'lense' command line utility.
    """
    CLIClient().interface()