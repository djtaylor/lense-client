from lense.client.module import ClientModuleCommon

class ClientModule(ClientModuleCommon):
    """
    Class wrapper for requests to the user utilities.
    """
    
    # Module request path and description
    path = 'acl'
    desc = 'Manage Lense users.'
    
    def __init__(self, parent):
        self.parent = parent
        
    def get(self, data={}):
        """
        Get details for either a single or all users.
        """
        return self.parent._get('user', data=data)
    
    def create(self, data={}):
        """
        Create a new user account.
        """
        return self.parent._post('user', data=data)