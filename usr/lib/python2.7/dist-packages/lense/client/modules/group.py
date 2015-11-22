from lense.client.module import ClientModuleCommon

class ClientModule(ClientModuleCommon):
    """
    Class wrapper for requests to the API group utilities.
    """
    
    # Module request path and description
    path = 'group'
    desc = 'Manage Lense user groups.'
    
    def __init__(self, parent):
        self.parent = parent
        
    def get(self, data={}):
        """
        Get details for either a single or all groups.
        """
        return self.parent._get('group', data=data)
    
    def create(self, data={}):
        """
        Create a new group.
        """
        return self.parent._post('group', data=data)
    
    def delete(self, data={}):
        """
        Delete a group.
        """
        return self.parent._delete('group', data=data)
    
    def update(self, data={}):
        """
        Update a group.
        """
        return self.parent._put('group', data=data)
    
    def add_member(self, data={}):
        """
        Add a member to a group.
        """
        return self.parent._post('group/member', data=data)
    
    def remove_member(self, data={}):
        """
        Remove a member from the group.
        """
        return self.parent._delete('group/member', data=data)