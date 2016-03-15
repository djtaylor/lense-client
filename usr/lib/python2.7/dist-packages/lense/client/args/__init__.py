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
    for handler, cls in Client_Handlers().all().iteritems():
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
    def __init__(self, desc, opts, cmds, base):
        self.desc = desc
        self.opts = opts
        self.cmds = cmds
        self.base = base
    
         # Arguments interface / container
        self.interface = ClientArgsInterface(opts=opts, cmds=cmds)
        self.container = {}
    
        # Parse command line arguments
        self._parse()
    
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

    def filter(self, filter=None):
        """
        Convert a SQLite filter string into a query object.
        
        :param filter: The filter string to parse
        :type  filter: str
        :rtype: str
        """
        filter = self.get('filter', filter)
        
        # No filter found
        if not filter:
            return ''
        
        # SQL operators and comparison strings
        sql_operators = ['&&', '||']
        sql_comparisons = {
            '=': '=',
            '==': '==',
            '~=': 'LIKE',
            '!=': '!=',
            '>': '>',
            '>=': '>=',
            '<': '<',
            '<=': '<=',
            '<>': '<>',
            '!<': '!<',
            '!>': '!>'
        }
        
        # Query array / string
        qa = []
        qs = ''
    
        def _parse_match(match, step):
            """
            Parse a SQL match string into an array.
            
            :param match: The SQL match string
            :type  match: str
            :rtype: list
            """
            for f,q in sql_comparisons.iteritems():
                regex = re.compile(r'(^[^{0}]*){0}([^{0}]*$)'.format(re.escape(f)))
                if regex.match(match):
                    left  = regex.sub(r'\g<1>', match)
                    right = regex.sub(r'\g<2>', match)
                    return [step, left, q, right]
    
        def _parse_operators(query, src, step='WHERE'):
            """
            Parse SQL query operators.
            
            :param query: The query object
            :type  query: OrderedDict
            :param   src: The query string to parse
            :type    src: str
            :step   step: The operator to use for the next step
            :type   step: str
            """
            
            # Parse the next operator
            if any(x in src for x in sql_operators):
                op_pos = [src.find('&&'), src.find('||')]
                op_cur = ' AND' if (op_pos[0] > op_pos[1]) else ' OR'
                op_cut = min(int(s) for s in op_pos if (s > 0))
                op_nxt = src[op_cut + 2:]
                op_key = step
                
                # Store the current match
                query.append(_parse_match(src[:op_cut], op_key))
                    
                # Parse the next match
                return _parse_operators(query, op_nxt, op_cur)
            
            # Done parsing operators
            else:
                query.append(_parse_match(src, step))
            
        # Construct the query array
        _parse_operators(qa, filter)
        
        # Construct and return the query string
        for qo in qa:
            qs += '{0} {1} {2} \'{3}\''.format(qo[0], qo[1], qo[2], qo[3])
        return qs
    
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
         return "{0}\n\n{1}.\n".format(self.desc['title'], self.desc['summary'])
    
    def _parse(self):
        """
        Parse command line arguments.
        """
            
        # Create a new argument parsing object and populate the arguments
        self.parser = ArgumentParser(description=self._desc(), formatter_class=RawTextHelpFormatter, usage=self.desc['usage'])
        self.parser.add_argument('command', help=self.interface.commands.help())
        
        # Base command specific arguments
        if self.base:
            self.parser.add_argument('target', nargs='?', default=None, help='Target command for help')

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
    def construct(cls, desc=ClientArgs_Base.desc, opts=ClientArgs_Base.options, cmds=ClientArgs_Base.commands, base=True):
        """
        Method for constructing and returning an arguments handler.
        
        :param desc: The description for the command
        :type  desc: dict
        :param opts: Any options the command takes
        :type  opts: list
        :param cmds: Additional subcommands
        :type  cmds: dict
        """
        LENSE.CLIENT.ARGS = cls(desc, opts, cmds, base)