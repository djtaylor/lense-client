from lense.client.args import ClientArgs_CLI

class ClientHandler_CLI(object):
    """
    Class for handling command line requests to the Lense client libraries.
    """
    def __init__(self):
        self.args = ClientArgs_CLI()

    def run(self):
        print self.args

class ClientHandler_Mod(object):
    pass