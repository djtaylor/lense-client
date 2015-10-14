from __future__ import print_function
import os
import re
import sys
import json
import argparse
import importlib
from copy import copy

# Lense Libraries
from lense.common.vars import LENSE_CONFIG
from lense.client.manager import APIConnect
from lense.common.utils import format_action
from lense.common.objects import JSONObject

# Load the client mapper
MAP_JSON = JSONObject()
MAP_JSON.from_file(LENSE_CONFIG.MAPPER)

class _CLIModules(object):
    """
    Class object for handling interface modules.
    """
    def __init__(self):
        
        # Internal modules
        self._modules    = {}
        
        # Help prompt
        self.help_prompt = None
        
        # Construct the modules object
        self._construct()
        
    def _construct(self):
        """
        Return a list of supported module arguments.
        """
        
        # Modules help menu
        help_prompt = ''
        
        # Grab the base module path
        mod_base = MAP_JSON.search('base')
        
        # Process each module definition
        for mod in MAP_JSON.search('modules'):
            self._modules[mod['id']] = {}
            
            # Load the interface module
            iface_mod = '{0}.{1}'.format(mod_base, mod.get('module'))
            
            # Load the interface request handler
            re_mod   = importlib.import_module(iface_mod)
            re_class = getattr(re_mod, mod.get('class'))
            
            # Load the public classes for the interface module
            for attr in dir(re_class):
                if not re.match(r'^__.*$', attr):
                    self._modules[mod.get('id')][attr] = getattr(re_class, attr)
            
            # Add the module to the help menu
            help_prompt += format_action(mod.get('id'), mod.get('desc'))
        
        # Set the help prompt
        self.help_prompt = help_prompt
        
    def get(self, module):
        """
        Get a modules attributes.
        """
        return self._modules.get(module, None)
        
    def list(self):
        """
        Return a list of available modules. 
        """
        return self._modules.keys()

class _CLIArgs(object):
    """
    Class object for handling command line arguments.
    """
    def __init__(self, mod_help=None):

        # Arguments parser / object
        self.parser  = None
        self._args   = None
        
        # Module help prompt
        self._mhelp  = mod_help
        
        # Construct arguments
        self._construct()
        
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
        self.parser.add_argument('module', help=self._mhelp)
        self.parser.add_argument('action', nargs='?', help="The action to perform against the endpoint", action='append')
        
        # Load arguments
        for arg in MAP_JSON.search('args'):
            self.parser.add_argument(arg['short'], arg['long'], help=arg['help'], action=arg['action'])
      
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
        return _val if not use_json else json.dumps(_val)

class CLIClient(object):
    """
    Command line interface for making API requests.
    """
    def __init__(self):
    
        # API client and connection parameters
        self.client  = None
        self.connect = None
    
        # Arguments / modules objects
        self.modules = _CLIModules()
        self.args    = _CLIArgs(mod_help=self.modules.help_prompt)
    
        # Module attributes
        self._mod_id = None
        self._module = None
        self._action = None
        self._method = None
    
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

        # Connection parameters
        params = {
            'user': self.args.get('api_user'), 
            'group': self.args.get('api_group'), 
            'api_key': self.args.get('api_key'), 
            'cli': True    
        }
        
        # Create the API client and connection objects
        self.client, self.connect = APIConnect(**params).construct(self._module.get('api', False))
    
        # If token retrieval/connection failed
        if not self.client:
            self._die('HTTP {0}: {1}'.format(self.connect['code'], self.connect['body'].get('error', 'An unknown error occurred')))
    
    def _list_actions(self, module):
        """
        List support actions for a module.
        """
        if self.args.get('list'):
            print('\nSupported actions for module "{0}":\n'.format(self._module))
            for k in self._public_keys():
                print('> {0}'.format(k))
            print('')
            sys.exit(0)
    
    def _get_module(self):
        """
        Get module attributes.
        """
        
        # Module ID
        self._mod_id = self.args.get('module')
        
        # Module attributes / action / method
        self._module = self.modules.get(self._mod_id)
        self._action = self.args.get('action', '_default')
        self._method = self._module.get(self._action, None)
    
    def _public_keys(self):
        """
        Return the public keys for a module.
        """
        if '_default' in self._module:
            mod_public = copy(self._module)
            del mod_public['_default']
            return mod_public.keys()
        return self._module.keys()
    
    def interface(self):
        """
        Handle any command line arguments.
        """
        
        # Handle incoming requests
        try:
            
            # Unsupported module argument
            if not self.args.get('module') in self.modules.list():
                self._die('\nUnsupported module argument "{0}"\n'.format(self.args.get('module')), pre=self.args.parser.print_help)
            
            # Get module attributes
            self._get_module()
            
            # Make a conditional API connection
            self._connect_api()
            
            # Look for any required arguments
            for r in MAP_JSON.search('modules/{0}/args/required'.format(self._mod_id), default=[]):
                if not self.args.get(r):
                    self._die('Missing required argument "{0}"'.format(r))
            
            # If listing module actions
            self._list_actions(self.args.get('module'))                
            
            # If no method found
            if not self._method:
                err = '\nUnsupported module action "{0}"\n'.format(self.args.get('action'))
                err += 'Supported actions are: {0}\n'.format(json.dumps(', '.join(self._public_keys())))
                self._die(err, pre=self.args.parser.print_help)

            # Get the client module method
            mod_object = getattr(self.client, self.args.get('module'))
            mod_method = getattr(mod_object, self._action)
            
            # If submitting extra API request data
            response = mod_method(self.args.get('api_data', use_json=True))
            
            # Response attributes
            r_code   = response.get('code')
            r_body   = response.get('body')
            
            # Print the response
            print('HTTP {0}: {1}'.format(r_code, r_body if not isinstance(r_body, (list, dict)) else json.dumps(r_body)))
    
        # Error in handling arguments
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._die(str(e))
            
def cli():
    """
    Entry point method for the 'lense' command line utility.
    """
    CLIClient().interface()