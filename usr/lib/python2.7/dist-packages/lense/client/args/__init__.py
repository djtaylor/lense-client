import re
from os import environ
from sys import argv, exit
from json import loads as json_loads
from argparse import ArgumentParser, RawTextHelpFormatter

# Lense Libraries
from lense.client.handlers import ClientHandlers
from lense.client.args.options import OPTIONS

def get_base_commands():
    """
    Return base command attributes.
    """
    commands = {
        "help": "Get help for a specific command: lense help <command>"
    }
    for handler, cls in ClientHandlers().all().iteritems():
        commands[handler] = cls.desc['summary']
    return commands

class ClientArgs_Base(object):
    """
    Argument attributes for the base Lense client interface.
    """
    
    # Description
    desc       = {
        "title": "Lense Client",
        "summary": "Lense platform command line utilities.",
        "usage": "\n> lense [command] [subcommand] [options]\n> lense help [target]"
    }
    
    # Target / options / commands
    use_target = True
    options    = []
    commands   = get_base_commands()
    
class ClientArg_Commands(object):
    """
    Wrapper class for storing command attributes.
    """
    def __init__(self, cmds):
        self._cmds = cmds
        
    def keys(self):
        """
        Return a listing of handler command keys.
        """
        return self._cmds.keys()
    
    def help(self):
        """
        Return the handlers help prompt
        """
        cmds_str = ''
        for cmd, help in self._cmds.iteritems():
            if isinstance(help, str):
                cmds_str += "> {0}: {1}\n".format(cmd, help)
            else:
                cmds_str += "> {0}: {1}\n".format(cmd, help['help'])
        return ("Available Commands:\n{0}\n".format(cmds_str))

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
        """
        
        # Argparse options
        self.short    = '-{0}'.format(opts['short'])
        self.long     = '--{0}'.format(opts['long'])
        self.help     = opts['help']
        self.action   = opts['action']

class ClientArgsInterface(object):
    """
    Load client arguments from the manifest.
    """
    def __init__(self, opts, cmds):
        self._opts = opts
        self._cmds = cmds
        
        # Commands / options
        self.commands = ClientArg_Commands(cmds)
        self.options  = []
    
        # Options
        for opt in self._opts:
            self.options.append(ClientArg_Option(**opt))
    
class ClientArgs(object):
    """
    Public class object for constructing arguments object for base
    and sub-commands.
    """
    def __init__(self, desc, opts, cmds, objs, base):
        self.desc = desc
        self.opts = opts
        self.cmds = cmds
        self.objs = objs
        self.base = base
    
        # Arguments interface / container
        self.interface = ClientArgsInterface(opts=opts, cmds=cmds)
        self.container = {}
    
        # Parse command line arguments
        self._parse()
    
        # Scan environment variables
        self._getenv()
    
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
    
    def _getenv(self):
        """
        Look for API connection environment variables.
        """
        
        # If calling with sudo, merge sudo user environment
        if LENSE.CLIENT.as_sudo:
            user_env  = '/home/{0}/.lense/env.sh'.format(LENSE.CLIENT.sysuser)
            env_regex = re.compile(r'^export (LENSE_[^=]*)=\"([^"]*)\"$')
            
            # Get API environment variables
            with open(user_env, 'r') as f:
                for line in f.readlines():
                    if line.startswith('export LENSE'):
                        env_key = env_regex.sub(r'\g<1>', line.lstrip().rstrip())
                        env_val = env_regex.sub(r'\g<2>', line.lstrip().rstrip())
        
                        # Update environment
                        environ[env_key] = env_val
        
        # Look for Lense API environment variables
        for k,v in {
            'user':  'LENSE_API_USER',
            'key':   'LENSE_API_KEY',
            'group': 'LENSE_API_GROUP'
        }.iteritems():
            if v in environ and not self.container.get(k, None):
                self.set(k, environ[v])
    
    def _desc(self):
         return "{0}\n\n{1}.\n".format(self.desc['title'], self.desc['summary'])
    
    def _parse(self):
        """
        Parse command line arguments.
        """
            
        # Create a new argument parsing object and populate the arguments
        self.parser = ArgumentParser(description=self._desc(), formatter_class=RawTextHelpFormatter, usage=self.desc['usage'])
        
        # Only parse commands if supported
        if self.interface.commands.keys():
            self.parser.add_argument('command', help=self.interface.commands.help())
        
        # Base command specific arguments
        if self.base:
            self.parser.add_argument('target', nargs='?', default=None, help='Target command for help')

        # Load module objects
        if self.objs:
            for k,a in self.objs.iteritems():
                self.parser.add_argument(k, nargs='?', default=None, help=a['help'])

        # Load client switches
        for arg in self.interface.options:
            self.parser.add_argument(arg.short, arg.long, help=arg.help, action=arg.action)
        
        # No parameters given
        if len(argv) == 1:
            self.help()
            exit(0)
        
        # Parse base command options
        argv.pop(0)
        self.container = vars(self.parser.parse_args(argv))
    
    def help(self):
        """
        Print the help prompt.
        """
        self.parser.print_help()
    
    @staticmethod
    def handlers():
        """
        Return a list of supported handlers.
        """
        return [h for h in LENSE.CLIENT.HANDLERS.all().keys()]
    
    @classmethod
    def construct(cls, 
        desc = ClientArgs_Base.desc, 
        opts = ClientArgs_Base.options, 
        cmds = ClientArgs_Base.commands, 
        objs = None, 
        base = True):
        """
        Method for constructing and returning an arguments handler.
        
        :param desc: The description for the command
        :type  desc: dict
        :param opts: Any options the command takes
        :type  opts: list
        :param cmds: Additional subcommands
        :type  cmds: dict
        """
        LENSE.CLIENT.ARGS = cls(desc, opts, cmds, objs, base)