from json import loads as json_loads
from argparse import ArgumentParser, RawTextHelpFormatter

class LenseClientArgs(object):
    """
    Class object for constructing command line or module level arguments.
    """
    def __init__(self):
        self._args = {}
    
    def list(self):
        """
        Return a list of argument keys.
        """
        return self._args.keys()
    
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
        return _val if not use_json else json_loads(_val)
    
    def _return_help(self):
         return ("Lense API Client\n\n"
                 "A utility designed to handle interactions with the Lense API client manager.\n"
                 "Supports most of the API endpoints available.\n")
    
    def parse_mod(self):
        pass
    
    def parse_cli(self):
        """
        Construct the argument parser.
        """
        
        # Create a new argument parsing object and populate the arguments
        self.parser = ArgumentParser(description=self._return_help(), formatter_class=RawTextHelpFormatter)
        self.parser.add_argument('module', help=self.help_prompt())
        self.parser.add_argument('action', nargs='?', help="The action to perform against the endpoint", action='append')
        
        # Load client switches
        self.parser.add_argument('-u', '--api-user', help='The API user to authenticate with if not set as the environment variable "LENSE_API_USER"', action='append')
        self.parser.add_argument('-g', '--api-group', help='The API user group to authenticate with if not set as the environment variable "LENSE_API_GROUP"', action='append')
        self.parser.add_argument('-k', '--api-key', help='The API key to authenticate with if not set as the environment variable "LENSE_API_KEY"', action='append')
        self.parser.add_argument('-d', '--api-data', help='Optional data to pass during the API request, must be a valid JSON string', action='append')
        self.parser.add_argument('-l', '--list', help='Show supported actions for a specified module', action='store_true')
        
        # Parse CLI arguments
        argv.pop(0)
        self._args = vars(self.parser.parse_args(argv))
    
    @classmethod
    def construct(cls, cli):
        """
        Construct the arguments class object.
        
        :param cli: Is this being called from the command line
        :type  cli: bool
        :rtype: LenseClientArgs
        """
        args = cls()
        

class ClientArgs(ClientModules):
    """
    Class object for handling command line arguments.
    """
    def __init__(self, cli):
        super(ClientArgs, self).__init__()

        # Arguments parser / object
        self.parser  = None
        self._args   = {}
        
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
        self.parser = ArgumentParser(description=self._return_help(), formatter_class=RawTextHelpFormatter)
        self.parser.add_argument('module', help=self.help_prompt())
        self.parser.add_argument('action', nargs='?', help="The action to perform against the endpoint", action='append')
        
        # Load client switches
        self.parser.add_argument('-u', '--api-user', help='The API user to authenticate with if not set as the environment variable "LENSE_API_USER"', action='append')
        self.parser.add_argument('-g', '--api-group', help='The API user group to authenticate with if not set as the environment variable "LENSE_API_GROUP"', action='append')
        self.parser.add_argument('-k', '--api-key', help='The API key to authenticate with if not set as the environment variable "LENSE_API_KEY"', action='append')
        self.parser.add_argument('-d', '--api-data', help='Optional data to pass during the API request, must be a valid JSON string', action='append')
        self.parser.add_argument('-l', '--list', help='Show supported actions for a specified module', action='store_true')
        
        # Parse CLI arguments
        argv.pop(0)
        self._args = vars(self.parser.parse_args(argv))
        
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
        return _val if not use_json else json_loads(_val)