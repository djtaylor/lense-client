from lense.client.module import ClientModuleCommon

class ClientModule(ClientModuleCommon):
    """
    Class wrapper for interacting with ACL definitions.
    """
    
    # Module request path and description
    path = 'acl'
    desc = 'ACL keys, objects, and access definitions'
    
    def __init__(self, parent):
        self.parent = parent
    
    def get(self, data=None):
        """
        Get an object containing ACL definitions.
        """
        return self.parent._get('acl/keys', data=data)
    
    def update(self, data=None):
        """
        Update an existing ACL definition.
        """
        return self.parent._put('acl/keys', data=data)
    
    def delete(self, data=None):
        """
        Delete an existing ACL definition.
        """
        return self.parent._delete('acl/keys', data=data)
    
    def create_object(self, data=None):
        """
        Create a new ACL object.
        """
        return self.parent._post('acl/objects', data=data)
    
    def get_objects(self, data=None):
        """
        Retrieve a listing of ACL object types.
        """
        return self.parent._get('acl/objects', data=data)
    
    def delete_object(self, data=None):
        """
        Delete an ACL object definition.
        """
        return self.parent._delete('acl/objects', data=data)