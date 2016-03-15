from lense.client.args.options import OPTIONS
from lense.client.handlers.base import ClientHandler_Base

class ClientHandler_Request(ClientHandler_Base):
    """
    Class object for managing API requests.
    """
    id      = 'request'
    
    # Command description
    desc    = {
        "title": "Lense API Request",
        "summary": "Make a request to the Lense API",
        "usage": "lense request [path] [method]"
    }
    
    # Supported options
    options = OPTIONS
    
    # Supported commands
    commands = {
        "test": {
            "help": "A dummy command"
        }
    }
    
    def __init__(self):
        super(ClientHandler_Request, self).__init__(self.id)