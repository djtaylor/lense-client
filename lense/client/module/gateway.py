class ModGateway:
    """
    Class wrapper for authorization utilities.
    """
    def __init__(self, parent):
        self.parent = parent
    
    def get_token(self, data=None):
        """
        Get an API token.
        """
        return self.parent._get('gateway/token', data=data)
    
    def get_acl(self, data=None):
        """
        Get an object containing ACL definitions.
        """
        return self.parent._get('gateway/acl', data=data)
    
    def update_acl(self, data=None):
        """
        Update an existing ACL definition.
        """
        return self.parent._put('gateway/acl', data=data)
    
    def get_utilities(self, data=None):
        """
        Retrieve a listing of API utilities.
        """
        return self.parent._put('gateway/utilities', data=data)
    
    def open_utility(self, data=None):
        """
        Open a utility for editing.
        """
        return self.parent._put('gateway/utilities/open', data=data)
    
    def close_utility(self, data=None):
        """
        Check in a utility and release the editing lock.
        """
        return self.parent._put('gateway/utilities/close', data=data)
    
    def validate_utility(self, data=None):
        """
        Validate changes to a utility prior to saving.
        """
        return self.parent._put('gateway/utilities/validate', data=data)
    
    def create_acl_object(self, data=None):
        """
        Create a new ACL object.
        """
        return self.parent._post('gateway/acl/objects', data=data)
    
    def get_acl_objects(self, data=None):
        """
        Retrieve a listing of ACL object types.
        """
        return self.parent._get('gateway/acl/objects', data=data)
    
    def delete_acl_objects(self, data=None):
        """
        Delete an ACL object definition.
        """
        return self.parent._delete('gateway/acl/objects', data=data)