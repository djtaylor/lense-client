import re
import sys
import inspect
from os import path, walk

# Lense Libraries
from lense import import_class

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
            if not a.startswith('_') and not a == m:
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
                module = import_class('ClientModule', '{0}.{1}'.format(mod_path, LENSE.MODULE.name(file)), init=False)
                
                # Store the request module
                self._modules[module.path] = module
        
    def _get_modules_d(self):
        """
        Load user drop-in request modules.
        """
        
        # Get the client dropin module attributes
        client_dropins = LENSE.MODULE.dropin('client')
        
        # Import the modules
        self._import_modules(client_dropins[0], client_dropins[1])
        
    def _get_modules(self):
        """
        Load built-in client request modules.
        """
        
        # Get the client builtin module attributes
        client_builtins = LENSE.MODULE.builtin('client')
        
        # Import the modules
        self._import_modules(client_builtins[0], client_builtins[1])
        
    def help_prompt(self):
        """
        Return the help prompt for all modules for argparse.
        """
        help_str = ''
        for p,m in self._modules.iteritems():
            help_str  += '{0:<10} {1}\n'.format(p, m.desc)
        help_str += '\n'
        return help_str
        
    def getmod(self, path):
        """
        Return a module class by path.
        
        :param path: The request path
        :type  path: str
        :rtype: ClientModule
        """
        return self._modules.get(path, None)
        
    def listmod(self):
        """
        Return a list of client modules.
        """
        return self._modules.keys()