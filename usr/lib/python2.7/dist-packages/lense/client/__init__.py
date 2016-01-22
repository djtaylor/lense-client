from lense.client.handler import ClientHandler_CLI
from lense.common.exceptions import ClientError

def cli():
    """
    Load the client CLI handler.
    """
    try:
        client = ClientHandler_CLI()
        response = client.run()
        
        # Print the results
        client.print_response(response.content, response.code)
        
    # Client error
    except ClientError as e:
        LENSE.LOG.exception(e.message)
        client.print_error_and_die(e.message, e.code)