from cloudscape.common.bootstrap.manager import Bootstrap

class ModBootstrap:
    """
    Client module for bootstrap the Cloudscape installation.
    """
    def __init__(self, parent):
        self.parent = parent
        
    def _default(self):
        """
        Default bootstrap handler.
        """
        
        # Create a new bootstrap handler
        bootstrap = Bootstrap()
        
        # Run and return the bootstrap module
        return bootstrap.run()