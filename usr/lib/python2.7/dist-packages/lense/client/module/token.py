from lense.client.module import ClientModuleCommon

class ClientModule(ClientModuleCommon):
    """
    Class wrapper for handling token requests.
    """
    
    # Module request path and description
    path = 'token'
    desc = 'Request authorization tokens'
    
    def __init__(self, parent):
        self.parent = parent
    
    def get(self, data=None):
        """
        Get an API token.
        """
        return True