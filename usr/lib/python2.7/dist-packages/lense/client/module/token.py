class ModToken:
    """
    Class wrapper for handling token requests.
    """
    def __init__(self, parent):
        self.parent = parent
    
    def get(self, data=None):
        """
        Get an API token.
        """
        return True