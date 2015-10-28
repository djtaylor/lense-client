class ModIntegrator:
    """
    Class wrapper for requests to the integrator utilities.
    """
    def __init__(self, parent):
        self.parent = parent
        
    def get(self, data={}):
        """
        Get details for either a single or all integrators.
        """
        return self.parent._get('integrator', data=data)
    
    def create(self, data={}):
        """
        Create a new integrator.
        """
        return self.parent._post('integrator', data=data)
    
    def update(self, data={}):
        """
        Update an existing integrator.
        """
        return self.parent._post('integrator', data=data)
    
    def delete(self, data={}):
        """
        Delete an existing integrator.
        """
        return self.parent._delete('integrator', data=data)