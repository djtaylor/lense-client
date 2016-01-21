from json import loads as json_loads

class ClientParams(object):
    """
    Client parameters class container.
    """
    def __init__(self):
        self.manifest = self._load_manifest()
        
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