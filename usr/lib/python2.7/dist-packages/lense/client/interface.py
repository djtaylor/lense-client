import json
from sys import exit
from threading import Thread
from os import makedirs, environ, geteuid
from os.path import expanduser, isfile, isdir

# Lense Libraries
from lense import import_class
from lense.client import CLIENT_HOME, SUPPORT_CACHE
from lense.common.exceptions import ClientError, RequestError

class ClientResponse(object):
    """
    Class object for a successfull HTTP response
    """
    def __init__(self, content, code=200):
        self.content = content
        self.code    = code

class ClientInterface(object):
    """
    Interface class for the Lense client.
    """
    def __init__(self):
        self.HANDLERS = None
        self.ARGS     = None
        self.REST     = import_class('ClientREST', 'lense.client.rest', init=False)
        self.GITHUB   = import_class('ClientGitHub', 'lense.client.github', init=False)
        
        # Store the calling user account if using sudo
        self.sysuser  = environ.get('SUDO_USER', environ.get('LOGNAME', None))
        self.as_sudo  = True if geteuid() == 0 else False
        
        # Support cache
        self.support  = None
        
    def bootstrap(self):
        """
        Bootstrap the client.
        """
        
        # Make the home directory
        if not isdir(CLIENT_HOME):
            makedirs(CLIENT_HOME)
        
        # Cache file already exists
        if isfile(SUPPORT_CACHE):
            LENSE.LOG.info('Loading supported API operations cache <- {0}'.format(SUPPORT_CACHE))
            self.support = json.loads(open(SUPPORT_CACHE, 'r').read())
        
        # Generate cache
        else:
        
            # Get server API support
            response = LENSE.CLIENT.REST.request_anonymous('support', 'GET')
            
            # Failed to retrieve server API support
            LENSE.CLIENT.ensure_request(response.code,
                value = 200,
                error = 'Failed to retrieve server API support',
                code  = response.code)
            
            # Write the support cache
            with open(SUPPORT_CACHE, 'w') as f:
                f.write(json.dumps(response.content))
            LENSE.LOG.info('Cached supported API operations -> {0}'.format(SUPPORT_CACHE))
            
            # Load the support cache
            LENSE.LOG.info('Loading supported API operations cache <- {0}'.format(SUPPORT_CACHE))
            self.support  = response.content
        
        # Load objects
        self.HANDLERS = import_class('ClientHandlers', 'lense.client.handlers')
        self.ARGS     = import_class('ClientArgs', 'lense.client.args', init=False)

    def get_authentication(self):
        """
        Return a dictionary of authentication attributes.
        """
        
        # User / group / key
        auth = {
            'user': LENSE.CLIENT.ARGS.get('user'),
            'group': LENSE.CLIENT.ARGS.get('group'),
            'key': LENSE.CLIENT.ARGS.get('key')
        }
        
        # Make sure required authentication parameters are set
        for k,v in auth.iteritems():
            if not v: LENSE.die('Missing required parameter "{0}", not found in arguments or environment'.format(k))

        # Return authentication parameters
        return auth
    
    def params(self, keys):
        """
        Retrieve a dictionary of object attributes.
        
        :param keys: A list of keys to retrieve
        :type  keys: list
        :rtype: list
        """
        params = {}
        for key in keys:
            if hasattr(self, key):
                params[key] = getattr(self, key)
        return params
        
    def _thread_worker(self, key, path, method, data=None):
        """
        Worker method for handled threaded API calls.
        
        :param    key: The key to access the response object with
        :type     key: str
        :param   path: The request path
        :type    path: str
        :param method: The request method
        :type  method: str
        :param   data: Additional request data
        :type    data: dict
        """
        
        self._response[key] = self.request(path=path, method=method, data=data)
        
    def request_threaded(self, requests):
        """
        Multi-threaded request handler.
        """
        
        # Threads / responses
        threads = []
        
        # Process each request
        for key, attr in requests.iteritems():
        
            # Get any request data
            data   = None if (len(attr) == 2) else attr[2]
        
            # Create the thread, append, and start
            thread = Thread(target=self._thread_worker, args=[key, attr[0], attr[1], data])
            threads.append(thread)
            thread.start()
            
        # Wait for the API calls to complete
        for thread in threads:
            thread.join()
            
        # Return the response object
        return self._response
        
    def http_response(self, response, raw=False):
        """
        Print a successfull HTTP response.
        """
        content = response.content
        
        # Raw output
        if raw:
            print json.dumps(response.content)
            
        # Formatted output
        else:
            try:
                content = '\n\n{0}\n'.format(json.dumps(response.content, indent=2))
            except:
                pass
            LENSE.FEEDBACK.success('HTTP {0}: {1}'.format(response.code, content))
        
        # Request finished
        exit(0)

    def http_error(self, code, msg):
        """
        Print an HTTP request error.
        """
        LENSE.FEEDBACK.error('HTTP {0}: {1}'.format(code, msg))
        exit(code)

    def error(self, message):
        """
        Print a ClientError message.
        """
        LENSE.FEEDBACK.error(message)
        exit(1)
        
    def response(self, content, code=200):
        """
        Return a ClientResponse object.
        """
        return ClientResponse(content, code)
        
    def ensure(self, *args, **kwargs):
        """
        Raise a ClientError if ensure fails.
        """
        kwargs['exc'] = ClientError
        return LENSE.ensure(*args, **kwargs)
    
    def ensure_request(self, *args, **kwargs):
        """
        Raise a RequestError if a client request fails.
        """
        kwargs['exc'] = RequestError
        return LENSE.ensure(*args, **kwargs)