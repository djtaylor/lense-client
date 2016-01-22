import json
import requests
from os import makedirs
from os.path import expanduser, dirname, isdir, isfile

# Lense Libraries
from lense.common import init_project
from lense.common.http import HEADER, MIME_TYPE
from lense.common.exceptions import ClientError
from lense.client.rest import RESTInterface

class ClientResponse(object):
    """
    Class object for a successfull HTTP response
    """
    def __init__(self, content, code=200):
        self.content = content
        self.code    = code

class ClientCommon(object):
    """
    Common client base class.
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
            return json.loads(open(manifest_file, 'r').read())
        except Exception as e:
            LENSE.die('Failed to load arguments manifest: {0}'.format(e.message))
    
    def ensure(self, *args, **kwargs):
        """
        Raise a ClientError if ensure fails.
        """
        kwargs['exc'] = ClientError
        return LENSE.ensure(*args, **kwargs)