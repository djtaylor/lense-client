import re
import json
from os import listdir
from urllib import urlopen

# Lense Libraries
from lense.common.utils import ensure_root
from lense.client.handlers.base import ClientHandler_Base

class ClientHandler_Module(ClientHandler_Base):
    """
    Class object for managing Lense modules.
    """
    id      = 'module'
    
    # Command description
    desc    = {
        "title": "Lense Modules",
        "summary": "Manage Lense platform modules",
        "usage": "lense module [command] [module] [options]"
    }
    
    # Supported options
    options = []
    
    # Supported commands
    commands = {
        "install": {
            "help": "Install a new module"
        },
        "remove": {
            "help": "Remove a module"
        },
        "upgrade": {
            "help": "Upgrade a module"
        },
        "list": {
            "help": "Show installed modules"
        }
    }
    
    # Target objects
    objects = {
        "module": {
            "help": "The target module name [upgrade/remove] or URI [install]"
        }
    }
    
    def __init__(self):
        super(ClientHandler_Module, self).__init__(self.id)
        
        # Target module name / URI / module root
        self.module = LENSE.CLIENT.ARGS.get('module', None)
        self.root   = '/etc/lense/modules'
        
        # Install modules
        self.installed = self._get_installed()
        
    def _check_module_arg(self):
        """
        Make sure the module argument is present.
        """
        if not self.module:
            LENSE.die('Must specify a module name/URI!')
        
    def _get_installed(self):
        """
        Discover currently installed modules.
        """
        modules = []
        for module in listdir(self.root):
            try:
                modules.append(json.loads(open('{0}/{1}/manifest.json'.format(self.root, module), 'r').read()))
                
            # Failed to load module manifest
            except Exception as e:
                LENSE.LOG.exception('Failed to load module "{0}" manifest: {1}'.format(module, str(e)))
                LENSE.die('Could not load manifest for module: {0}'.format(module))
        return modules
        
    def _parse_github_url(self):
        """
        Validate and extract attributes from a GitHub URL when installing a module.
        """
        if not re.match(r'https://github.com/[^\/]*/[^\/]*$', self.module):
            LENSE.die('Invalid GitHub URL: {0}'.format(self.module))
        
        # Parse the GitHub URL
        return {
            'account': re.compile(r'https://github.com/([^\/]*)/[^\/]*$').sub(r'\g<1>', self.module),
            'repository': re.compile(r'https://github.com/[^\/]*/([^\/]*$)').sub(r'\g<1>', self.module)
        }
        
    def _validate_manifest(self, manifest, remote=False):
        """
        Validate a manifest's contents.
        """
        for k in ['name', 'description', 'author', 'source', 'version']:
            if not k in manifest:
                LENSE.die('Invalid manifest, missing required key: {0}'.format(k))
        
            # Validate source block
            if not isinstance(manifest['source'], dict):
                LENSE.die('Manifest "source" block must be a dictionary')
                
            # Only GitHub supported
            if not manifest['source'].get('type', None) == 'github':
                LENSE.die('Invalid/missing source type, must be "github"')
                
            # URI must match the module path
            if remote:
                if not manifest['source'].get('uri', None) == self.module:
                    LENSE.die('Invalid/missing source URI, must match: {0}'.format(self.module))
        
        # Return the manifest
        return manifest
        
    def _get_local_manifest(self):
        """
        Retrieve a local manifest for a module.
        """
        try:
            manifest_path = '{0}/{1}/manifest.json'.format(self.root, self.module)
            return self._validate_manifest(json.loads(open(manifest_path).read()))
        except Exception as e:
            LENSE.die('Failed to load module "{0}" manifest: {1}'.format(self.module, str(e)))
        
    def _get_github_manifest(self):
        """
        Retrieve a remote GitHub manifest before installing.
        """
        github_url = self._parse_github_url()
        
        # Raw manifest contents
        raw_manifest = 'https://raw.githubusercontent.com/{0}/{1}/master/manifest.json'.format(
            github_url['account'],
            github_url['repository']
        )
        
        # Get the manifest contents
        try:
            response = urlopen(raw_manifest)
            
            # Validate the manifest
            return self._validate_manifest(json.loads(response.read()))
        
        # Failed to retrieve/parse module manifest
        except Exception as e:
            LENSE.die('Failed to load module manifest: {0}'.format(str(e)))
        
    def list(self):
        """
        List installed modules.
        """
        print ''
        for module in self.installed:
            print 'Module: {0}'.format(module['name'])
            print 'Description: {0}'.format(module['description'])
            print 'Version: {0}'.format(module['version'])
            print 'Author: {0}'.format(module['author'])
            print 'Source:'
            print '> Type: {0}'.format(module['source']['type'])
            print '> URI: {0}'.format(module['source']['uri'])
            print '> Branch: {0}\n'.format(module['source'].get('branch', 'master'))
        
    def install(self):
        """
        Install a Lense module.
        """
        ensure_root()
        
        # Check module argument
        self._check_module_arg()
        
        # Get the remote manifest
        manifest = self._get_github_manifest()
    
        # Download the module
        LENSE.CLIENT.GITHUB.clone(
            local  = '{0}/{1}'.format(self.root, manifest['name']),
            remote = self.module,
            branch = manifest['source'].get('branch', 'master')
        )
        
        # Module installation success
        LENSE.FEEDBACK.success('Installed module: {0}@{1}'.format(manifest['name'], manifest['source']['uri']))
    
    def remove(self):
        """
        Remove a Lense module.
        """
        ensure_root()
        
        # Check module argument
        self._check_module_arg()
        
        # Get the local manifest
        manifest = self._get_local_manifest()
        
        # Remove the module directory
        LENSE.rmdir('{0}/{1}'.format(self.root, manifest['name']))
        LENSE.FEEDBACK.success('Uninstalled module: {0}'.format(manifest['name']))
    
    def upgrade(self):
        """
        Upgrade a Lense module.
        """
        ensure_root()
        
        # Check module argument
        self._check_module_arg()
        
        # Get the local manifest
        manifest = self._get_local_manifest()
        
        # Update the module
        LENSE.CLIENT.GITHUB.pull(
            local  = '{0}/{1}'.format(self.root, manifest['name']),
            remote = manifest['source']['uri'],
            branch = manifest['source'].get('branch', 'master')
        )