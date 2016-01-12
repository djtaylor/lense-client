from json import loads as json_loads
from argparse import ArgumentParser, RawTextHelpFormatter

class ClientArgs_CLI(object):
    """
    Construct arguments passed to the Lense client via the command line.
    """
    def __init__(self):
        self._args = {}
    
        # Construct command line arguments
        self._construct()
    
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
    
    def _desc(self):
         return ("Lense API Client\n\n"
                 "A utility designed to handle interactions with the Lense API client manager.\n"
                 "Supports most of the API endpoints available.\n")
    
    def _command_help(self):
        return ("Available Commands: lense [command] [options]\n"
                "> request: Make a request to the Lense API engine\n")
    
    def _construct(self):
        """
        Construct the argument parser.
        """
        
        # Create a new argument parsing object and populate the arguments
        self.parser = ArgumentParser(description=self._desc(), formatter_class=RawTextHelpFormatter)
        self.parser.add_argument('command', help=self.command_help())
        
        # Load client switches
        self.parser.add_argument('-p', '--path', help='The request path relative to the API server', action='append')
        self.parser.add_argument('-m', '--method', help='The request method to use', action='append')
        self.parser.add_argument('-d', '--data', help='Any additional data to pass with the API request', action='append')
        self.parser.add_argument('-u', '--user', help='The API user to authenticate with if not set as the environment variable "LENSE_API_USER"', action='append')
        self.parser.add_argument('-g', '--group', help='The API user group to authenticate with if not set as the environment variable "LENSE_API_GROUP"', action='append')
        self.parser.add_argument('-k', '--key', help='The API key to authenticate with if not set as the environment variable "LENSE_API_KEY"', action='append')
        
        # Parse CLI arguments
        argv.pop(0)
        self._args = vars(self.parser.parse_args(argv))