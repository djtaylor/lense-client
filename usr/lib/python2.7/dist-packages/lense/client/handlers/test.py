import json
from sys import getsizeof
from os.path import isfile

# Lense Libraries
from lense.client.args.options import OPTIONS
from lense.common.exceptions import RequestError
from lense.client.handlers.base import ClientHandler_Base

class ClientHandler_Test(ClientHandler_Base):
    """
    Class object for managing API test runner.
    """
    id      = 'test'
    
    # Command description
    desc    = {
        "title": "Lense API Testrunner",
        "summary": "Run the Lense API test suite",
        "usage": "lense test [options]"
    }
    
    # Supported options
    options = [
        {
            "short": "m",
            "long": "manifest",
            "help": "Specify a path to a test manifest in JSON format.",
            "action": "store"
        }
    ] + OPTIONS
    
    # Supported commands
    commands = {}
    
    def __init__(self):
        super(ClientHandler_Test, self).__init__(self.id)
        
        # Test manifest
        self.manifest = None
        
    def get_manifest(self):
        """
        Load and return the test manifest.
        """
        manifest = LENSE.CLIENT.ARGS.get('manifest', '/usr/share/lense/client/test.default.json')
        
        # Test manifest argument required
        if not manifest:
            LENSE.die('Must specify a test manifest: lense test --manifest example.json')
        
        # Test manifest file not found
        if not isfile(manifest):
            LENSE.die('Could not locate test manifest: {0}'.format(manifest))
        
        try:
            self.manifest = json.loads(open(LENSE.CLIENT.ARGS.get('manifest'), 'r').read())
        except Exception as e:
            LENSE.die('Failed to parse test manifest: {0}'.format(str(e)))
        
    def _validate_response_data(self, expects, data):
        """
        Validate data in a response.
        """
        
        # No response data validation
        if not expects:
            return [True, None]
        
        # Validate the response data
        for k,v in expects.iteritems():
            if not k in data:
                return [False, {'key': k, 'value': [v,None]}]
            if not data[k] == v:
                return [False, {'key': k, 'value': [v,data[k]]}]
        
        # Response data OK
        return [True, None]
        
    def _get_authentication(self, block):
        """
        Extract authentication attributes from a section block.
        """
        return {
            'user': block.get('user', LENSE.CLIENT.ARGS.get('user')),
            'group': block.get('group', LENSE.CLIENT.ARGS.get('group')),
            'key': block.get('key', LENSE.CLIENT.ARGS.get('key'))
        }
        
    def _get_server(self, block):
        """
        Extract server attributes from a section block.
        """
        return {
            'host': block.get('host', LENSE.CONF.engine.host),
            'port': block.get('port', LENSE.CONF.engine.port),
            'proto': block.get('proto', LENSE.CONF.engine.proto)
        }
        
    def default(self):
        """
        Default command handler.
        """
        
        # Load the test manifest
        self.get_manifest()
        
        # Process the manifest
        for section_key, section_block in self.manifest.iteritems():
            LENSE.FEEDBACK.info('Initializing test run: section="{0}", desc="{1}"'.format(section_key, section_block.get('desc', 'No description provided')))
        
            # Make sure a test block exists
            if not isinstance(section_block.get('tests', None), list):
                LENSE.die('Section block must contain a "tests" section and it must be a list of test definitions')
        
            # Get authentication / server options
            auth   = self._get_authentication(section_block.get('auth', {}))
            server = self._get_server(section_block.get('server', {}))
            LENSE.FEEDBACK.info('Authentication: user="{0}", group="{1}", key="{2}"'.format(auth['user'], auth['group'], auth['key']))
            LENSE.FEEDBACK.info('Endpoint: {0}://{1}:{2}'.format(server['proto'], server['host'], server['port']))
        
            # Construct REST client
            LENSE.CLIENT.REST.construct(user=auth['user'], group=auth['group'], key=auth['key'], endpoint=server)
        
            # Scan each test block
            for test_block in section_block['tests']:
        
                # Request parameters
                params = {
                    'path': test_block['path'],
                    'method': test_block['method'],
                    'data': json.dumps(test_block.get('data', {})),
                    'ensure': False
                }
                
                # Make the request
                response = LENSE.CLIENT.REST.request(**params)
                
                # Expects block
                expects  = { 'code': 200 } if not 'expects' in test_block else test_block['expects']
                
                # Code / returned data OK
                expects_ok = True if (expects['code'] == response.code) else False
                data_ok    = self._validate_response_data(expects.get('data', None), response.content)
                
                # Response code match
                if expects_ok:
                    
                    # Response data mismatch
                    if not data_ok[0]:
                        LENSE.FEEDBACK.error('id={0}, expects.code={1}, response.code={2}, data.expects[{3}]={4} data.returned[{3}]={5}'.format(*[
                            test_block['id'],
                            expects['code'],
                            response.code,
                            data_ok[1]['key'],
                            data_ok[1]['value'][0],
                            data_ok[1]['value'][1]
                        ]))
                        
                    # Response data match
                    else:
                        LENSE.FEEDBACK.success('id={0}, expects.code={1}, response.code={2}, data.returned=OK, rsp_size_bytes={3}'.format(*[
                            test_block['id'],
                            expects['code'],
                            response.code,
                            getsizeof(response.content)
                        ]))
                    
                # Response code mismatch
                else:
                    LENSE.FEEDBACK.error('id={0}, expects.code={1}, response.code={2}, rsp_size_bytes={3}'.format(*[
                        test_block['id'],
                        expects['code'],
                        response.code,
                        getsizeof(response.content)
                    ]))
            