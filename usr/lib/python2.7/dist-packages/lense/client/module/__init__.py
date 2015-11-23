import re
import sys
import inspect
from os import path, walk

# Lense Libraries
from lense.common import LenseCommon

# Lense Common
LENSE = LenseCommon('CLIENT')

class ClientModuleCommon(object):
    """
    Common class shared by client modules.
    """
    def actions(self):
        """
        Return a list of request handler actions for the client module.
        """
        m = inspect.stack()[0][3]
        l = []
        for a in dir(self):
            if not a.startswith('_') and not a == me:
                l.append(a)
        return l

class ClientModules(object):
    """
    Public class for constructing available client modules.
    """
    def __init__(self):
        
        # Object for storing client request modules
        self._modules = {}
        
        # Load built in followed by user drop in
        self._get_modules()
        self._get_modules_d()
        
    def help_prompt(self):
        """
        Return the help prompt for all modules for argparse.
        """
        help_str = ''
        for p,m in self._modules.iteritems():
            help_str  += '{0:<10} {1}\n'.format(p, m.desc)
        help_str += '\n'
        return help_str
        
    def _import_modules(self, mod_dir, mod_path):
        """
        Import module files in a given directory.
        """
        for root, dirs, files in walk(mod_dir, topdown=False):
            for file in files:
                
                # Ignore special files
                if re.match(r'^__.*$', file) or re.match(r'^.*\.pyc$', file):
                    continue
        
                # Import the module
                mod_obj = LENSE.MODULE.IMPORT('{0}.{1}'.format(mod_path, LENSE.MODULE.NAME(file)))
                mod_cls = getattr(mod_obj, 'ClientModule')
                
                # Store the request module
                self._modules[mod_cls.path] = mod_cls
        
    def _get_modules_d(self):
        """
        Load user drop-in request modules.
        """
        self._import_modules(LENSE.MODULE.DROPIN.CLIENT[0], LENSE.MODULE.DROPIN.CLIENT[1])
        
    def _get_modules(self):
        """
        Load built-in client request modules.
        """
        self._import_modules(LENSE.MODULE.BUILTIN.CLIENT[0], LENSE.MODULE.BUILTIN.CLIENT[1])
        
    def get(self, path):
        """
        Return a module class by path.
        """
        return self._modules.get(path, None)
        
    def list(self):
        """
        Return a list of client modules.
        """
        return self._modules.keys()