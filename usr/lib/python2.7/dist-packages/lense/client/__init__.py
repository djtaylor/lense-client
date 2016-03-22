from sys import argv, exit
from os.path import dirname, realpath, expanduser

# Lense Libraries
from lense.common.exceptions import ClientError, RequestError

# Global attributes
CLIENT_HOME   = expanduser('~/.lense')
SUPPORT_CACHE = '{0}/support.cache.json'.format(CLIENT_HOME)
TOKEN_CACHE   = '{0}/token.cache.json'.format(CLIENT_HOME)

class LenseClient(object):
    """
    Public class for invoking the CLI client.
    """ 
    @classmethod
    def _run_handler(cls, handler):
        """
        Private method for loading subcommand handler.
        """
        argv.pop(0)
        
        # Load the command handler
        command = LENSE.CLIENT.ensure(LENSE.CLIENT.HANDLERS.get(argv[0]),
            isnot = None,
            error = 'Cannot load unsupported command: {0}'.format(argv[0]),
            code  = 1)
    
        # Run the target command
        return command().run()
    
    @classmethod
    def run(cls):
        """
        Public method for running Lense client utilities.
        """
        try:
            
            # Bootstrap the client
            LENSE.CLIENT.bootstrap()
            
            # Supported handlers
            handlers = LENSE.CLIENT.ARGS.handlers()
            
            # Pass to handler
            if (len(argv) > 1) and (argv[1] in handlers):
                cls._run_handler(argv[1])
                
            # Base commands
            else:
                
                # Construct base argument parser
                LENSE.CLIENT.ARGS.construct()
                
                # If getting help for a command
                if LENSE.CLIENT.ARGS.get('command') == 'help':
                    
                    # Get the target handler
                    target = LENSE.CLIENT.ensure(LENSE.CLIENT.ARGS.get('target'),
                        isnot = None,
                        error = 'Usage: lense help [command]',
                        code  = 1)
                    
                    # Make sure the target is supported
                    command = LENSE.CLIENT.ensure(LENSE.CLIENT.HANDLERS.get(target),
                        isnot = None,
                        error = 'Cannot load help for unsupported command: {0}'.format(target),
                        code  = 1)
                    
                    # Return the command help
                    return command().help()
                
                # Unsupported command
                LENSE.CLIENT.ARGS.help()
                LENSE.die('\nUnsupported command: {0}\n'.format(LENSE.CLIENT.ARGS.get('command')))
            
        # Client error
        except ClientError as e:
            LENSE.LOG.exception(e.message)
            LENSE.CLIENT.error(e.message)
            
        # Request error
        except RequestError as e:
            LENSE.LOG.error(e.message)
            LENSE.CLIENT.http_error(e.code, e.message)
            