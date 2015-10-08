class ModUser:
    """
    Class wrapper for requests to the user utilities.
    """
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