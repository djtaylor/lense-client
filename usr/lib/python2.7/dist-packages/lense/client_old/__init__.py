from __future__ import print_function
from sys import exit

# Lense imports
from lense.client.args import LenseClientArgs
from lense.client.manager import LenseClientAPI
from lense.client.module import LenseClientModules

__version__ = '0.1.1'    
    
class LenseClient(object):
    """
    Factory class for constructing the Lense API client.
    """
    def __init__(self, cli):
        self.is_cli = cli
        
        # Arguments / API connector
        self.ARGS   = LenseClientArgs.construct(cli)
        self.API    = LenseClientAPI()

    def authenticate(self, user, group, key=None, token=None):
        """
        Authenticate the user/group before making a request.
        
        :param  user: The API username to make the request as
        :type   user: str
        :param group: The API group UUID to make the request as
        :type  group: str
        :param   key: The API key to submit for a token request
        :type    key: str
        :param token: The API token to submit for authorized requests
        :type  token: str
        """

        # Must supply a key and/or token
        if not key and not token:
            raise Exception('Must supply an API \'key\' and/or \'token\'')

        # Make a token request
        if not token:
            

    @staticmethod
    def error(response, code=500, cli=False):
        """
        Helper method used to handle a returned error response.
        
        :param response: The response JSON object
        :type  response: dict
        :param     code: The HTTP return code
        :type      code: int
        :param      cli: Boolean indicating if being called from a command line client
        :type       cli: bool
        """
        
        # If being run from the command line
        if cli:
            
            # Show the error message
            print('ERROR: {0}'.format(response.get('message', 'Failed to process the request')))
                
            # Print the response
            print('\n---RESPONSE---')
            print('HTTP {0}: {1}\n'.format(code, response.get('error', 'An unknown error has occurred')))
            
            # If any debug information is present
            if 'debug' in response:
                print('---DEBUG---')
                print('Traceback (most recent call last):')
                for l in response['debug']['traceback']:
                    print('  File "{0}", line {1}, in {2}'.format(l[0], l[1], l[2]))
                    print('    {0}'.format(l[3]))
                print('Exception: {0}\n'.format(response['debug']['exception']))
            
            # Exit the client
            exit(1)
            
        # Library is being loaded from another module
        else:
            return response
    
    
    
        
    @classmethod
    def bootstrap(cls, cli):
        """
        Bootstrap the Lense client.
        
        :param cli: Is this being called from the command line
        :type  cli: bool
        """
        LENSE.CLIENT = cls(cli)
        
def cli():
    """
    Public method for constructing the command-line interface for Lense client.
    """
    
    # Initialize the project
    init_project('CLIENT')
    
    # Setup the client interface
    LENSE.SETUP.client(cli=True)