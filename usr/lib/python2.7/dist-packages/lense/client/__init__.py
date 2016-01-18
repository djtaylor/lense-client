from lense.client.handler import ClientHandler_CLI

def cli():
    """
    Load the client CLI handler.
    """
    client = ClientHandler_CLI()
    client.run()