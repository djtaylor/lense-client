from sys import argv
from os import environ
from json import loads as json_loads
from argparse import ArgumentParser, RawTextHelpFormatter

# Lense Libraries
from lense.client.params import ClientParams

class ClientArg_Commands(object):
    """
    Wrapper class for storing command attributes.
    """
    def __init__(self, commands):
        self.commands = commands
        
    def keys(self):
        """
        Return a listing of command keys.
        """
        keys = []
        for c in self.commands:
            keys.append(c['key'])
        return keys
    
    def help(self):
        """
        Return the commands help prompt
        """
        commands_str = ''
        for cmd in self.commands:
            commands_str += "> {0}: {1}\n".format(cmd['key'], cmd['help'])
        return ("Available Commands:\n{0}".format(commands_str))

class ClientArg_Option(object):
    """
    Wrapper class for storing option attributes.
    """
    def __init__(self, **opts):
        """
        :param    short: Option short key
        :type     short: str
        :param     long: Option long key
        :type      long: str
        :param     help: Option help prompt
        :type      help: str
        :param   action: Argparse action
        :type    action: str
        :param required: Is this option required or not
        :type  required: bool
        :param     json: Convert option value to JSON
        :type      json: bool
        """
        
        # Argparse options
        self.short    = '-{0}'.format(opts['short'])
        self.long     = '--{0}'.format(opts['long'])
        self.help     = opts['help']
        self.action   = opts['action']

        # Validation options
        self.required = opts.get('required', False)
        self.json     = opts.get('json', False)

class ClientArgsInterface(ClientParams):
    """
    Load client arguments from the manifest.
    """
    def __init__(self):
        super(ClientArgsInterface, self).__init__()

        # Commands / options
        self.commands = None
        self.options  = []

        # Construct client arguments
        self._construct()

    def _construct(self):
        """
        Construct client commands and options.
        """
        
        # Commands
        self.commands = ClientArg_Commands(self.manifest['commands'])
        
        # Options
        for opts in self.manifest['options']:
            self.options.append(ClientArg_Option(**opts))

class ClientArgs_CLI(object):
    """
    Construct arguments passed to the Lense client via the command line.
    """
    def __init__(self):
    
        # Arguments interface / container
        self.interface = ClientArgsInterface()
        self.container = {}
    
        # Construct command line arguments
        self._construct()
    
    def _getenv(self):
        """
        Look for API connection environment variables.
        """
        for k,v in {
            'user':  'LENSE_API_USER',
            'key':   'LENSE_API_KEY',
            'group': 'LENSE_API_GROUP'
        }.iteritems():
            if v in environ:
                self.set(k, environ[v])
    
    def list(self):
        """
        Return a list of argument keys.
        """
        return self.container.keys()
    
    def dict(self):
        """
        Return a dictionary of argument key/values.
        """
        return self.container
    
    def set(self, k, v):
        """
        Set a new argument or change the value.
        """
        self.container[k] = v
        
    def get(self, k, default=None, use_json=False):
        """
        Retrieve an argument passed via the command line.
        """
        
        # Get the value from argparse
        _raw = self.container.get(k)
        _val = (_raw if _raw else default) if not isinstance(_raw, list) else (_raw[0] if _raw[0] else default)
        
        # Return the value
        return _val if not use_json else json_loads(_val)
    
    def _desc(self):
         return ("Lense API Client\n\n"
                 "A utility designed to handle interactions with the Lense API client manager.\n"
                 "Supports most of the API endpoints available.\n")
    
    def _construct(self):
        """
        Construct the argument parser.
        """
        
        # Create a new argument parsing object and populate the arguments
        self.parser = ArgumentParser(description=self._desc(), formatter_class=RawTextHelpFormatter)
        self.parser.add_argument('command', help=self.interface.commands.help())
        
        # Load client switches
        for arg in self.interface.options:
            self.parser.add_argument(arg.short, arg.long, help=arg.help, action=arg.action)
            
        # Parse CLI arguments
        argv.pop(0)
        self.container = vars(self.parser.parse_args(argv))
        
        # Scan environment variables
        self._getenv()
        
    @classmethod
    def parse(cls):
        """
        Shortcut method for parsing CLI arguments and returning a dictionary.
        This assumes the calling object does not need an instance of this
        class, just arguments as a dictionary.
        """
        return cls().dict()