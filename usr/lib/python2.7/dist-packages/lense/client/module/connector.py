class ModConnector:
    """
    Class wrapper for requests to the connector utilities.
    """
    def __init__(self, parent):
        self.parent = parent
        
    def get(self, data={}):
        """
        Get details for either a single or all connectors.
        """
        return self.parent._get('connector', data=data)
    
    def create(self, data={}):
        """
        Create a new connector.
        """
        return self.parent._post('connector', data=data)
    
    def update(self, data={}):
        """
        Update an existing connector.
        """
        return self.parent._put('connector', data=data)
    
    def delete(self, data={}):
        """
        Delete an existing connector.
        """
        return self.parent._delete('connector', data=data)