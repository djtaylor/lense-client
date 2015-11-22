from lense.client.module import ClientModuleCommon

class ClientModule(ClientModuleCommon):
    """
    Class wrapper for requests to the statistics utilities.
    """
    
    # Module request path and description
    path = 'stats'
    desc = 'Manage Lense statistics.'
    
    def __init__(self, parent):
        self.parent = parent
        
    def get_request(self, data={}):
        """
        Gather request statistics.
        """
        return self.parent._get('stats/request', data=data)