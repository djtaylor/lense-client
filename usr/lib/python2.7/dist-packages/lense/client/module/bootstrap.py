from lense.common.bootstrap.manager import Bootstrap

class ModBootstrap:
    """
    Client module for bootstrap the Lense installation.
    """
    def __init__(self, parent):
        self.parent = parent
        
    def _default(self, data=None):
        """
        Default bootstrap handler.
        """
        
        # Create a new bootstrap handler
        bootstrap = Bootstrap()
        
        # Run and return the bootstrap module
        return bootstrap.run()