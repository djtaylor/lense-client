from lense.client.handler import ClientHandler_CLI
from lense.common.exceptions import ClientError, RequestError        

def cli():
    """
    Load the client CLI handler.
    """
    client = ClientHandler_CLI()
    try:
        client.bootstrap()
        response = client.run()
        
        # Print the results
        client.http_response(response.content, response.code)
        
    # Client error
    except ClientError as e:
        LENSE.LOG.exception(e.message)
        client.error(e.message)
        
    # Request error
    except RequestError as e:
        LENSE.LOG.exception(e.message)
        client.http_error(e.message, e.code)