import os
import re
import sys
import json
import argparse
import importlib

# Lense Libraries
from lense.common.vars import C_CLIENT, C_MAPPER
from lense.client.manager import APIConnect
from lense.common.utils import format_action
from lense.common.objects import JSONObject

# Load the client mapper
MAP_JSON = JSONObject()
MAP_JSON.from_file(C_MAPPER)

class _CLIModules(object):
    """
    Class object for handling interface modules.
    """
    def __init__(self):
        
        # Internal modules object
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
            self._modules[mod['id']] = []
            
            # Load the interface module
            iface_mod = '%s.%s' % (mod_base, mod.get('module'))
            
            # Load the interface request handler
            re_mod   = importlib.import_module(iface_mod)
            re_class = getattr(re_mod, mod.get('class'))
            
            # Load the public classes for the interface module
            for attr in dir(re_class):
                if not re.match(r'^__.*$', attr):
                    self._modules[mod.get('id')].append(attr)
            
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
        _raw = self._args.get(k, default)
        _val = _raw if not isinstance(_raw, list) else _raw[0]
        
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
        sys.stderr.write('%s\n' % msg)
        
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
            'api_user':  'CS_API_USER',
            'api_key':   'CS_API_KEY',
            'api_group': 'CS_API_GROUP'
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
        self.client, self.connect = APIConnect(**params).construct()
    
        # If token retrieval/connection failed
        if not self.client:
            self._die('HTTP %s: %s' % (self.connect['code'], self.connect['body'].get('error', 'An unknown error occurred')))
    
    def interface(self):
        """
        Handle any command line arguments.
        """
        
        # Handle incoming requests
        try:
        
            # Argument errors
            for a in MAP_JSON.search('args'):
                if a.get('required') and not self.args.get(a['id']):
                    self._die('Missing required argument "%s"' % a['id'])
            
            # Establish the API connection
            self._connect_api()
            
            # Unsupported module argument
            if not self.args.get('module') in self.modules.list():
                self._die('\nUnsupported module argument "%s"\n' % self.args.get('module'), pre=self.args.parser.print_help)
            
            # Module attributes / action / method
            module = self.modules.get(self.args.get('module'))
            action = self.args.get('action', '_default')
            method = module.get(action, None)
            
            # If listing module actions
            if self.args.get('list'):
                print '\nSupported actions for module "%s":\n' % self.args.get('module')
                for a in module:
                    print '> %s' % a
                print ''
                sys.exit(0)
            
            # If no method found
            if not method:
                err = '\nUnsupported module action "%s"' % self.args.get('action')
                err += 'Supported actions are: %s\n' % json.dumps(module)
                self._die(err, pre=self.args.parser.print_help)

            # Get the client module method
            mod_object = getattr(self.client, self.args.get('module'))
            mod_method = getattr(mod_object, action)
            
            # If submitting extra API request data
            response = mod_method(self.args.get('api_data', use_json=True))
            
            # Response attributes
            r_code   = response.get('code')
            r_body   = response.get('body')
            
            # Print the response
            print 'HTTP %s: %s' % (r_code, r_body if not isinstance(r_body, (list, dict)) else json.dumps(r_body))
    
        # Error in handling arguments
        except Exception as e:
            self._die(str(e))
            
def cli():
    """
    Entry point method for the 'lense' command line utility.
    """
    CLIClient().interface()