import json
from time import time
from sys import getsizeof, exit
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
        },
        {
            "short": "c",
            "long": "continue",
            "help": "Continue test run even if errors occur.",
            "action": "store_true"
        }
    ] + OPTIONS
    
    # Supported commands
    commands = {}
    
    def __init__(self):
        super(ClientHandler_Test, self).__init__(self.id)
        
        # Test manifest / continuous mode
        self.manifest = None
        self.cont     = LENSE.CLIENT.ARGS.get('continue', False)
        
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
        
        # Test ID
        test_id = self.manifest['id']
        
        # Sections block required
        if not 'sections' in self.manifest:
            LENSE.die('Test manifest must contain a "sections" block')
        
        # Process the manifest
        for section_key, section_block in self.manifest['sections'].iteritems():
        
            # Make sure a test block exists
            if not isinstance(section_block.get('tests', None), list):
                LENSE.die('Section block must contain a "tests" section and it must be a list of test definitions')
        
            # Get authentication / server options
            auth   = self._get_authentication(section_block.get('auth', {}))
            server = self._get_server(section_block.get('server', {}))
        
            # Begin test feedback
            LENSE.FEEDBACK.block([
                'Test ID:    {0}'.format(section_key),
                'Test Desc:  {0}'.format(section_block.get('desc', 'No description provided')),
                'Auth User:  {0}'.format(auth['user']),
                'Auth Group: {0}'.format(auth['group']),
                'Endpoint:   {0}://{1}:{2}'.format(server['proto'], server['host'], server['port'])
            ], 'INIT')
        
            # Construct REST client
            LENSE.CLIENT.REST.construct(user=auth['user'], group=auth['group'], key=auth['key'], endpoint=server)
        
            # Errors flag
            has_errors = False
        
            # Scan each test block
            test_start = time()
            for test_block in section_block['tests']:
                LENSE.FEEDBACK.block([
                    'ID:          {0}'.format(test_block['id']),
                    'Description: {0}'.format(test_block['desc']),
                    'Path:        {0}'.format(test_block['path']),
                    'Method:      {0}'.format(test_block['method'])
                ], 'RUNNING')
        
                # Request parameters
                params = {
                    'path': test_block['path'],
                    'method': test_block['method'],
                    'data': json.dumps(test_block.get('data', {})),
                    'ensure': False
                }
                
                # Make the request
                req_start = time()
                response  = LENSE.CLIENT.REST.request(**params)
                req_time  = '{0} seconds'.format(str(time() - req_start))
                
                # Expects block
                expects  = { 'code': 200 } if not 'expects' in test_block else test_block['expects']
                
                # Code / returned data OK
                expects_ok = True if (expects['code'] == response.code) else False
                data_ok    = self._validate_response_data(expects.get('data', None), response.content)
                
                # Response code match
                if expects_ok:
                    
                    # Response data mismatch
                    if not data_ok[0]:
                        LENSE.FEEDBACK.error('expects.code={0}, response.code={1}, data.expects[{2}]={3} data.returned[{2}]={4}, request_time={5}'.format(
                            expects['code'],
                            response.code,
                            data_ok[1]['key'],
                            data_ok[1]['value'][0],
                            data_ok[1]['value'][1],
                            req_time
                        ))
                        has_errors = True
                        
                        # Do not continue after error
                        if not self.cont:
                            LENSE.FEEDBACK.error('Test block failed!')
                            exit(response.code)
                        
                    # Response data match
                    else:
                        LENSE.FEEDBACK.success('expects.code={0}, response.code={1}, data.returned=OK, rsp_size_bytes={2}, request_time={3}'.format(
                            expects['code'],
                            response.code,
                            getsizeof(response.content),
                            req_time
                        ))
                    
                # Response code mismatch
                else:
                    LENSE.FEEDBACK.error('expects.code={0}, response.code={1}, rsp_size_bytes={2}, request_time={3}'.format(
                        expects['code'],
                        response.code,
                        getsizeof(response.content),
                        req_time
                    ))
                    has_errors = True
                    
                    # Do not continue after error
                    if not self.cont:
                        LENSE.FEEDBACK.error('Test block failed!')
                        exit(response.code)
            
            # Section complete
            if has_errors:
                LENSE.FEEDBACK.warn('Not all tests completed successfully. Please check the server logs to troubleshoot')
            else:
                LENSE.FEEDBACK.success('All tests completed successfully in: {0} seconds'.format(str(time() - test_start)))