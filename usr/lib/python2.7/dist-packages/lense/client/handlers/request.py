import json
from itertools import imap
from collections import OrderedDict

# Lense Libraries
from lense.client import SUPPORT_CACHE
from lense.client.args.options import OPTIONS
from lense.client.handlers.base import ClientHandler_Base

def get_commands():
    """
    Return a list of supported commands from the cache file.
    """
    commands = {}
    with open(SUPPORT_CACHE, 'r') as f:
        cache   = json.loads(f.read())
        longest = max(imap(len, cache))
        for name, attrs in cache.iteritems():
            indent = longest - len(name) + 1
            commands[name] = {
                "help": "{0}{1}".format(' ' * indent, attrs['desc'])
            }
    return OrderedDict(sorted(commands.items()))

class ClientHandler_Request(ClientHandler_Base):
    """
    Class object for managing API requests.
    """
    id      = 'request'
    
    # Command description
    desc    = {
        "title": "Lense API Request",
        "summary": "Make a request to the Lense API",
        "usage": "lense request [command] [options]"
    }
    
    # Supported options
    options = [
        {
            "short": "d",
            "long": "data",
            "help": "Pass additional data as a quoted JSON string: --data '{\"key\":\"value\"}'",
            "action": "store"
        },
        {
            "short": "i",
            "long": "info",
            "help": "Print information about the specified request command.",
            "action": "store_true"
        },
        {
            "short": "r",
            "long": "raw",
            "help": "Dump the raw JSON output from the server to stdout.",
            "action": "store_true"
        }
    ] + OPTIONS
    
    # Supported commands
    commands = get_commands()
    
    def __init__(self):
        super(ClientHandler_Request, self).__init__(self.id)
        
        # Raw output / command information
        self.raw  = LENSE.CLIENT.ARGS.get('raw', False)
        self.info = LENSE.CLIENT.ARGS.get('info', False)
        
    def command_info(self):
        """
        Print supported command information and exit.
        """
        info = LENSE.CLIENT.support.get(self.command)
        print '\nName:   {0}'.format(info['name'])
        print 'UUID:   {0}'.format(info['uuid'])
        print 'Desc:   {0}'.format(info['desc'])
        print 'Path:   {0}'.format(info['path'])
        print 'Method: {0}\n'.format(info['method'])
        
    def default(self):
        """
        Default command handler.
        """
        if not self.command in self.commands:
            LENSE.die('Unsupported command: {0}'.format(self.command))
        
        # If printing command info
        if self.info: return self.command_info()
        
        # User / group / key
        auth = {
            'user': LENSE.CLIENT.ARGS.get('user'),
            'group': LENSE.CLIENT.ARGS.get('group'),
            'key': LENSE.CLIENT.ARGS.get('key')
        }
        
        # Make sure required authentication parameters are set
        for k,v in auth.iteritems():
            if not v: LENSE.die('Missing required parameter "{0}", not found in arguments or environment'.format(k))
        
        # Construct REST client
        LENSE.CLIENT.REST.construct(**auth)
        
        # Request parameters
        params = {
            'path': LENSE.CLIENT.support.get(self.command)['path'],
            'method': LENSE.CLIENT.support.get(self.command)['method'],
            'data': LENSE.CLIENT.ARGS.get('data')
        }
        
        # Make the request
        response = LENSE.CLIENT.REST.request(**params)
        
        # OK
        if response.code == 200:
            LENSE.CLIENT.http_response(response, self.raw)
        LENSE.CLIENT.http_error(response, self.raw)