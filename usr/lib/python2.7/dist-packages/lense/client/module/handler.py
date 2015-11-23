from lense.client.module import ClientModuleCommon

class ClientModule(ClientModuleCommon):
    """
    Class wrapper for request handlers.
    """
    
    # Module request path and description
    path = 'handler'
    desc = 'Request handlers'
    
    def __init__(self, parent):
        self.parent = parent
    
    def get(self, data=None):
        """
        Retrieve a listing of API request handlers.
        """
        return self.parent._get('handler', data=data)
    
    def open(self, data=None):
        """
        Open a handler for editing.
        """
        return self.parent._put('handler/open', data=data)
    
    def close(self, data=None):
        """
        Check in a handler and release the editing lock.
        """
        return self.parent._put('handler/close', data=data)
    
    def validate(self, data=None):
        """
        Validate changes to a handler prior to saving.
        """
        return self.parent._put('handler/validate', data=data)