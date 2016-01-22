from os import makedirs
from json import loads as json_loads
from os.path import expanduser, dirname, isdir, isfile

class ClientCommon(object):
    """
    Common client base class.
    """
    def __init__(self):
        self.manifest = self._load_manifest()
        self.cache    = expanduser('~/.lense/support.cache.json')
        self.endpoint = None
    
        # Initialize commons
        init_project('CLIENT')

        # Bootstrap methods
        self._bootstrap()
        
    def _bootstrap(self):
        """
        Run bootstrap after commons has been initialized.
        """
        host  = LENSE.CONF.engine.host
        proto = LENSE.CONF.engine.proto
        port  = LENSE.CONF.engine.port
        
        # API server endpoint
        self.endpoint = '{0}://{1}:{2}'.format(proto, host, port)
        
    def _save_cache(self, data):
        """
        Save server capabilities cache data.
        """
        with open(self.cache, 'w') as f:
            f.write(data)
            LENSE.FEEDBACK.success('Updated server support cache: {0}'.format(self.cache))
        
    def _load_cache(self):
        """
        Cache server capabilities.
        """
        usr_dir = dirname(self.cache)
        
        # Make sure the user directory exists
        if not isdir(usr_dir):
            makedirs(usr_dir, '0755')
        
        # If the cache doesn't exist yet
        if not isfile(self.cache):
            LENSE.FEEDBACK.info('Building server support cache...')
            
            # Support URL
            support_url = '{0}/support'.format(self.endpoint)
            
            # Request headers
            headers = {
                HEADER.CONTENT_TYPE: MIME_TYPE.APPLICATION.JSON,
                HEADER.ACCEPT: MIME_TYPE.TEXT.PLAIN
            }
            
            # Support response
            response = requests.get(support_url, headers=headers)
    
            # If support request looks OK
            if response.status_code == 200:
                self._save_cache(response.json()['data'])
            
            # Failed to get server capabilities
            else:
                LENSE.FEEDBACK.warn('Failed to retrieve server capabilities: HTTP {0}: {1}'.format(response.status_code, response.json()['error']))
                return False
        
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