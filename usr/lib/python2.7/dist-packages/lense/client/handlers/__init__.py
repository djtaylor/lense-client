from lense import import_class

class ClientHandlers(object):
    """
    Class object for loading command client handlers.
    """
    def _get_handler_args(self, handler):
        """
        Private method for returning handler argument attributes.
        """
        try:
            return {
                "help": self._handlers.get(handler).help,
                "options": self._handlers.get(handler).options,
                "commands": self._handlers.get(handler).commands
            }
        except Exception as e:
            LENSE.die('Failed to retrieve handler attributes: {0}'.format(str(e)))
        
    def all(self):
        """
        Return all available handlers.
        """
        return {
            "request": import_class('ClientHandler_Request', 'lense.client.handlers.request', init=False),
            "test": import_class('ClientHandler_Test', 'lense.client.handlers.test', init=False)
        }
        
    def get_args(self, handler=None):
        """
        Construct and return argument attributes for a single or all handlers.
        """
        if handler:
            return self._get_handler_args(handler)
        
        # Arguments for all handlers
        args = {}
        for h in self._handlers.keys():
            args[h] = self._get_handler_args(h)
        return args
        
    def get(self, handler):
        """
        Retrieve and initialize a command handler.
        """
        return LENSE.CLIENT.ensure(self.all().get(handler, None),
            isnot = None,
            error = 'Attempted to load unsupported handler: {0}'.format(handler),
            code  = 1)