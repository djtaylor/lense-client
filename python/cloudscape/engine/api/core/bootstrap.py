import os
import sys
import MySQLdb
from subprocess import Popen
from getpass import getpass

# cs
from cloudscape.common.feedback import Feedback
from cloudscape.common.vars import L_BASE

class Bootstrap(object):
    """
    Main class object for bootstrapping the Cloudscape installation. This
    includes setting up the database and setting the admin user account.
    """
    def __init__(self):
        self.feedback = Feedback()
    
        # Bootstrap parameters
        self.params   = {}
    
        # Database connection
        self._connection = None
    
    def _get_password(self, prompt, min_length=8):
        _pass = getpass(prompt)
        
        # Make sure the password is long enough
        if not len(_pass) >= min_length:
            self.fb.show('Password cannot be empty and must be at least %s characters long' % str(min_length)).error()
            return self._get_password(prompt, min_length)
            
        # Confirm the password
        _pass_confirm = getpass('Please confirm the password: ')
            
        # Make sure the passwords match
        if not _pass == _pass_confirm:
            self.feedback.show('Passwords do not match, try again').error()
            return self._get_password(prompt, min_length)
            
        # Password looks good
        return _pass
    
    def _get_input(self, prompt, default=None):
        _input = raw_input(prompt) or default
        
        # If no input found
        if not _input:
            self.feedback.show('Must provide a value').error()
            return self._get_input(prompt, default)
    
        # Return the input
        return _input
    
    def _try_mysql_root(self):
        """
        Attempt to connect to the MySQL server as root user.
        """
        try:
            self._connection = MySQLdb.connect(
                host=self.params['db_host']['value'], 
                port=int(self.params['db_port']['value']),
                user='root',
                passwd=self.params['db_root_password']['value']
            )
            self.feedback.show('Connected to MySQL using root user').success()
        except Exception as e:
            self.feedback.show('Unable to connect to MySQL with root user: %s' % str(e)).error()
            sys.exit(1)
    
    def _bootstrap_info(self):
        """
        Show a brief introduction and summary on the bootstrapping process.
        """
        print '\nCloudscape Bootstrap Utility\n'
        print 'The bootstrap utility is used to get a new Cloudscape installation up and'
        print 'running as quickly as possible. This will set up the database, make sure'
        print 'any required users exists, and populate the tables with seed data.\n'
    
    def _database(self):
        
        # Parameters required to connect to, create, and populate the database
        self.params = {
            'db_host': {
                'type': 'str',
                'default': 'localhost',
                'prompt': 'Please enter the hostname or IP address of the MySQL database server (localhost): ',
                'value': None
            },
            'db_port': {
                'type': 'str',
                'default': '3306',
                'prompt': 'Please enter the port to connect to the MySQL database server (3306): ',
                'value': None
            },
            'db_name': {
                'type': 'str',
                'default': 'cloudscape',
                'prompt': 'Please enter the name of the database to use/create for Cloudscape (cloudscape): ',
                'value': None
            },
            'db_user': {
                'type': 'str',
                'default': 'cloudscape',
                'prompt': 'Please enter the name of the primary non-root database user (cloudscape): ',
                'value': None
            },
            'db_password': {
                'type': 'pass',
                'default': None,
                'prompt': 'Please enter the password for the primary non-root database user: ',
                'value': None
            },
            'db_root_password': {
                'type': 'pass',
                'default': None,
                'prompt': 'Please enter the root password for the database server: ',
                'value': None
            }
        }
        
        # Run through each parameter
        for p,a in self.params.iteritems():
            
            # Regular string input
            if a['type'] == 'str':
                a['value'] = self._get_input(a['prompt'], a['default'])
                
            # Password input
            if a['type'] == 'pass':
                a['value'] = self._get_password(a['prompt'])
        print ''
            
        # Test the database connection
        self._try_mysql_root()
            
        # Create the database and user account
        try:
            _cursor = self._connection.cursor()
            
            # Create the database
            _cursor.execute('CREATE DATABASE IF NOT EXISTS %s' % self.params['db_name']['value'])
            self.feedback.show('Created database "%s"' % self.params['db_name']['value']).success()
            
            # Create the database user
            _cursor.execute("CREATE USER '%s'@'%s' IDENTIFIED BY '%s'" % (self.params['db_user']['value'], self.params['db_host']['value'], self.params['db_password']['value']))
            _cursor.execute("GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s'" % (self.params['db_name']['value'], self.params['db_user']['value'], self.params['db_host']['value']))
            _cursor.execute("FLUSH PRIVILEGES")
            self.feedback.show('Created database user "%s" with grants' % self.params['db_user']['value']).success()
            
        except Exception as e:
            self.feedback.show('Failed to bootstrap Cloudscape database: %s' % str(e)).error()
            sys.exit(1)
            
        # Close the connection
        _cursor.close()
        
        # Run Django syncdb
        try:
            app  = '%s/python/cloudscape/engine/api/manage.py' % L_BASE
            proc = Popen(['python', app, 'syncdb'])
            proc.communicate()
            
            # Make sure the command ran successfully
            if not proc.returncode == 0:
                self.feedback.show('Failed to sync Django application database').error()
                sys.exit(1)
                
            # Sync success
            self.feedback.show('Synced Django application database').success()
        except Exception as e:
            self.feedback.show('Failed to sync Django application database: %s' % str(e)).error()
            sys.exit(1) 
            
    def run(self):
        """
        Kickstart the bootstrap process for Cloudscape.
        """
        
        # Show bootstrap information
        self._bootstrap_info()
        
        # Bootstrap the database
        self._database()