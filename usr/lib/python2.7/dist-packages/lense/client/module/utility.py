class ModUtility:
    """
    Class wrapper for authorization utilities.
    """
    def __init__(self, parent):
        self.parent = parent
    
    def get(self, data=None):
        """
        Retrieve a listing of API utilities.
        """
        return self.parent._get('utility', data=data)
    
    def open(self, data=None):
        """
        Open a utility for editing.
        """
        return self.parent._put('utility/open', data=data)
    
    def close(self, data=None):
        """
        Check in a utility and release the editing lock.
        """
        return self.parent._put('utility/close', data=data)
    
    def validate(self, data=None):
        """
        Validate changes to a utility prior to saving.
        """
        return self.parent._put('utility/validate', data=data)