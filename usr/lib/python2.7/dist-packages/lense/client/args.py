from sys import argv
from os import environ
from json import loads as json_loads
from argparse import ArgumentParser, RawTextHelpFormatter

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
    def __init__(self, short, long, help, action='store'):
        """
        :param  short: Option short key
        :type   short: str
        :param   long: Option long key
        :type    long: str
        :param   help: Option help prompt
        :type    help: str
        :param action: Argparse action
        :type  action: str
        """
        self.short  = '-{0}'.format(short)
        self.long   = '--{0}'.format(long)
        self.help   = help
        self.action = action

class ClientArgsInterface(object):
    """
    Load client arguments from the manifest.
    """
    def __init__(self):
        self.manifest = self._load_manifest()

        # Commands / options
        self.commands = None
        self.options  = []

        # Construct client arguments
        self._construct()

    def _load_manifest(self):
        """
        Load the arguments manifest.
        """
        manifest_file = '/usr/share/lense/client/args.json'

        # Try to load the manifest
        try:
            return json_loads(open(manifest_file, 'r').read())
        except Exception as e:
            LENSE.die('Failed to load arguments manifest: {0}'.format(e.message))

    def _construct(self):
        """
        Construct client commands and options.
        """
        
        # Commands
        self.commands = ClientArg_Commands(self.manifest['commands'])
        
        # Options
        for a in self.manifest['options']:
            self.options.append(ClientArg_Option(short=a['short'], long=a['long'], help=a['help'], action=a['action']))

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