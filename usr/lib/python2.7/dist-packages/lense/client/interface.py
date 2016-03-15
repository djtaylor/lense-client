import json
from sys import exit
from threading import Thread
from os.path import expanduser, isfile

# Lense Libraries
from lense import import_class
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
        self.HANDLERS = import_class('ClientHandlers', 'lense.client.handlers')
        self.ARGS     = import_class('ClientArgs', 'lense.client.args', init=False)
        self.REST     = import_class('ClientREST', 'lense.client.rest', kwargs={ 'user': None, 'group': None, 'key': None })
        
        # Client attributes
        self.home     = expanduser('~/.lense')
        self.support  = None
        
    def cache_support(self):
        """
        Build the API request support cache.
        """
        cache_file = '{0}/support.cache.json'.format(self.home)
        
        # Cache file already exists
        if isfile(cache_file):
            self.support = json.loads(open(cache_file, 'r').read())
            return True
        
        # Get server API support
        response = LENSE.CLIENT.REST.request('support', 'GET')
        
        # Failed to retrieve server API support
        LENSE.CLIENT.ensure_request(response.code,
            value = 200,
            error = 'Failed to retrieve server API support',
            code  = response.code)
        
        # Write the support cache
        with open(cache_file, 'w') as f:
            f.write(json.dumps(response.content))
        
        # Load the support cache
        self.support = response.content
        return True
        
    def _load_data(self, data):
        return json.loads(data) if data else None

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
    
    def authorize(self):
        """
        Public method for authorizing a user account.
        """
        for k in ['user', 'group', 'key']:
            if not self.kwargs.get(k, False):
                raise ClientError('Missing required authorization key: {0}'.format(k))
        
        # User attributes
        self.user  = self.kwargs.get('user')
        self.group = self.kwargs.get('group')
        self.key   = self.kwargs.get('key')

        # Store the command
        self.command = self.kwargs.get('command')

        # Bootstrap the client
        self._bootstrap()

    def request(self, **kwargs):
        """
        Make a request to the API server.
        """
        
        # Load request attributes
        path   = kwargs.get('path', self.kwargs.get('path', None))
        method = kwargs.get('method', self.kwargs.get('method', None))
        data   = self._load_data(kwargs.get('data', self.kwargs.get('data', None)))
        
        # Path / method required
        if not path or not method:
            raise ClientError('Request attributes "path" and "method" required')
        
        # Make the API request
        return self.rest.request(path, method, data)
        
    def http_response(self, content, code=200):
        """
        Print a successfull HTTP response.
        """
        try:
            content = '\n\n{0}\n'.format(json.dumps(content, indent=2))
        except:
            pass
        LENSE.FEEDBACK.success('HTTP {0}: {1}'.format(code, content))
        exit(0)

    def http_error(self, message, code):
        """
        Print an HTTP request error.
        """
        LENSE.FEEDBACK.error('HTTP {0}: {1}'.format(code, message))
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