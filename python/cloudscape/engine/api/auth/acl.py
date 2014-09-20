import json
import importlib

# Django Libraries
from django.contrib.auth.models import User

# CloudScape Libraries
from cloudscape.common import config
from cloudscape.common import logger
from cloudscape.common.http import HEADER, PATH
from cloudscape.common.utils import invalid, valid
from cloudscape.common.vars import T_USER, T_HOST
from cloudscape.common.collection import Collection
from cloudscape.engine.api.objects.manager import ObjectsManager
from cloudscape.engine.api.app.user.models import DBUser
from cloudscape.engine.api.app.group.models import DBGroupDetails, DBGroupMembers
from cloudscape.engine.api.app.host.models import DBHostDetails
from cloudscape.engine.api.app.auth.models import DBAuthACLAccessHost, DBAuthACLAccessGlobal, \
                                                  DBAuthACLAccessObject, DBAuthUtilities, DBAuthACLKeys, \
                                                  DBAuthACLObjects
              
# Configuration / Logger / Objects Manager
CONF    = config.parse()
LOG     = logger.create('cloudscape.engine.api.auth.acl', CONF.server.log)
OBJECTS = ObjectsManager()
         
def get_obj_def(type):
    """
    Retrieve the object definition for a specific type.
    """
    return [x for x in list(DBAuthACLObjects.objects.all().values()) if x['type'] == type][0]
         
class ACLAuthObjects(object):
    """
    Parent class used to construct a list of objects that a user is authorized to access.
    """
    def __init__(self, user, type, path):
        
        # ACL user object / object type / object utility / cache manager
        self.user      = user
        self.type      = type
        self.utility   = ACLUtility(path).get()
        
        # Object accessor
        self.obj_def   = get_obj_def(type)
        
        # Search filters
        self.filters   = {}
        
        # Object IDs / details
        self.ids       = []
        self.details   = []
        
    def extract(self, idstr):
        """
        Extract a specific objecy from the details list.
        """
        for i in self.details:
            if i[self.obj_def['obj_key']] == idstr:
                return i
        return None
        
    def _merge_objects(self, new_objs):
        """
        Merge a new list of objects with the existing object list, ignoring duplicate entries.
        """
        if isinstance(new_objs, list):
            for i in new_objs:
                if not (i[self.obj_def['obj_key']] in self.ids):
                    self.ids.append(i[self.obj_def['obj_key']])
                    self.details.append(i)
        
    def _check_global_access(self, global_acls):
        """
        Determine if the user has global access to the utility.
        """
        for global_acl in global_acls:
            
            # If access is explicitly denied, try another ACL
            if not global_acl['allowed'] == 'yes': continue
            
            # Get all supported global utilities for this ACL
            global_utilities = [x['utility_id'] for x in list(DBAuthACLAccessGlobal.objects.filter(acl=global_acl['uuid']).values())]
            
            # If the ACL supports the target utility
            if self.utility.uuid in global_utilities:
                
                # Merge the object list
                self._merge_objects(OBJECTS.get(self.type, filters=self.filters))
        
    def _check_object_access(self, object_acls, group):
        """
        Determine if the user has access to specific objects in the utility.
        """
        
        # No utility object association
        if not self.utility.obj['object']:
            return
        
        # Create an instance of the ACL authorization class
        acl_mod   = importlib.import_module(self.obj_def['acl_mod'])
        acl_class = getattr(acl_mod, self.obj_def['acl_cls'])
        
        # Process each object ACL
        for object_acl in object_acls[self.type]['details']:
            
            # ACL access filter
            acl_filter = { 'owner': group }
            acl_filter['acl_id']  = object_acl['acl_id']
            acl_filter['allowed'] = True
        
            # Begin constructing a list of accessible objects
            for access_object in list(acl_class.objects.filter(**acl_filter).values()):
                acl_key = '%s_id' % self.obj_def['acl_key']
                
                # Get the accessible object
                self._merge_objects(OBJECTS.get(self.type, access_object[acl_key], filters=self.filters))
        
    def get(self, filters={}):
        """
        Process group membership and extract each object that is allowed for a specific group
        and ACL combination.
        """
        
        # Set any filters
        self.filters = filters
        
        # Process each group the user is a member of
        for group, acl in self.user.acls.iteritems():
        
            # Check for global access to the utility
            self._check_global_access(acl['global'])
        
            # Check for object level access to the utility
            self._check_object_access(acl['object'], group)
        
        # Return the authorized objects
        return self
         
class ACLUtility(object):
    """
    Parent class used to construct the ACL attributes for a specific utility. This includes
    retrieving the utility UUID, and any ACLs that provide access to this specific utility.
    """
    def __init__(self, path):
        
        # Utility name / UUID / object
        self.path   = path
        self.obj    = DBAuthUtilities.objects.filter(path=self.path).values()[0]
        self.uuid   = self.obj['uuid']
        
    def get(self): 
        return self
                 
class ACLUser(object):
    """
    Parent class used to construct ACL attributes for a specific API user. Construct an object
    defining the username, groups the user is a member of, all ACLs the user has access to based
    on their groups, as well as the account type (i.e., user/host).
    """
    def __init__(self, user):
       
        # Username / groups / ACLs
        self.name   = user
        self.type   = self._get_acc_type()
        self.groups = [] if (self.type == T_HOST) else self._get_groups()
        self.acls   = self._get_acls()
   
    def _get_acc_type(self):
        """
        Determine if the API account is a user or a host.
        """
        return T_HOST if DBHostDetails.objects.filter(uuid=self.name).count() else T_USER
   
    def _get_acls(self):
        """
        Construct and return an object containing enabled ACLs for all groups the user
        is currently a member of, or host permissions if the account type is T_HOST.
        """
        acls = {}
        
        # Host account
        if self.type == T_HOST:
            acls = list(DBAuthACLAccessHost.objects.all().values())
        
        # User account
        else:
            for group in self.groups:
                group_details = list(DBGroupDetails.objects.filter(uuid=group).values())[0]
                acls[group] = {
                    'object': group_details['permissions']['object'],
                    'global': group_details['permissions']['global'],
                }
                
        # Return the ACLs object
        return acls
        
    def _get_groups(self):
        """
        Construct and return a list of group UUIDs that the current API user is a 
        member of.
        """
        
        # Get the user object
        user_obj = DBUser.objects.get(username=self.name)
        
        # Construct a list of group UUIDs the user is a member of
        groups = [x['group_id'] for x in list(DBGroupMembers.objects.filter(member=user_obj.uuid).values())]
    
        # Log the user's group membership
        LOG.info('Constructed group membership for user [%s]: %s' % (user_obj.uuid, json.dumps(groups)))
        
        # Return the group membership list
        return groups
   
    def get(self): 
        return self
              
class ACLGateway(object):
    """
    ACL gateway class used to handle permissions for API requests prior to loading
    any API utilities. Used after key/token authorization.
    """
    def __init__(self, request):
        
        # Request object
        self.request       = request
        self.utility       = ACLUtility(self.request.path).get()
        self.user          = ACLUser(self.request.user).get()
        
        # Accessible objects / object key
        self.obj_list      = []
        self.obj_key       = None
        
        # Authorization flag / error container
        self.authorized    = False
        self.auth_error    = None
        
        # Authorize the request
        self._authorize()
        
    def _set_authorization(self, auth, err=None):
        """
        Set the authorized flag and an optional error message if the user is not authorized. Return the
        constructed ACL gateway instance.
        """
        self.authorized = auth
        self.auth_error = None if not err else err
        
        # Return the ACL gateway
        return self
  
    def _check_host_access(self):
        """
        Check if the managed host has access to the utility.
        """
        for acl in self.user.acls:
            
            # Get all supported host utilities for the ACL
            acl_access = [x['utility_id'] for x in list(DBAuthACLAccessHost.objects.filter(acl=acl['acl_id']).values())]
            
            # If the ACL supports the target utility
            if self.utility.uuid in acl_access:
                return valid()
        
        # Access denied
        return invalid('Access denied to utility [%s]' % self.utility.path)
        
    def _check_global_access(self, global_acls):
        """
        Determine if the user has global access to the utility.
        """
        for global_acl in global_acls:
            
            # If access is explicitly denied, try another ACL
            if not global_acl['allowed'] == 'yes': continue
            
            # Get all globally accessible utilities for this ACL
            global_access = [x['utility_id'] for x in list(DBAuthACLAccessGlobal.objects.filter(acl=global_acl['uuid']).values())]
            
            # If the ACL supports the target utility
            if self.utility.uuid in global_access:
                return valid(LOG.info('Global access granted for user [%s] to utility [%s]' % (self.user.name, self.utility.path)))
        
        # Global access denied
        return invalid('Global access denied for user [%s] to utility [%s]' % (self.user.name, self.utility.path))
    
    def _check_object_access(self, object_acls, group):
        """
        Determine if the user has object level access to the utility.
        """
        
        # Make sure the utility has an object type association
        if not self.utility.obj['object']:
            return invalid('')
        object_type = self.utility.obj['object']
        
        # Get the object authorization class
        obj_def   = get_obj_def(object_type)
        acl_mod   = importlib.import_module(obj_def['acl_mod'])
        acl_class = getattr(acl_mod, obj_def['acl_cls'])
            
        # Utility object key and target object value
        self.obj_key = self.utility.obj['object_key']
        
        # Specific object key found
        if (self.request.data) and (self.obj_key in self.request.data):
            
            # Process each ACL for the object type
            tgt_obj = None
            for object_acl in object_acls[object_type]['details']:
                tgt_obj = self.request.data[self.obj_key]
            
                # Object filter
                filter = {}
                filter['owner']            = group
                filter['allowed']          = True
                filter[obj_def['acl_key']] = tgt_obj
            
                # Check if the user has access to this object
                if acl_class.objects.filter(**filter).count():
                    return valid(LOG.info('Object level access granted for user [%s] to utility [%s] for object [%s:%s]' % (self.user.name, self.utility.path, self.utility.obj['object'], tgt_obj)))
        
            # Access denied
            return invalid(' for object <%s:%s>' % (self.utility.obj['object'], tgt_obj))
        
        # User not accessing a specific object
        else:
            return valid()
        
    def _check_access(self):
        """
        Make sure the user has access to the selected resource. Not sure how I want to handle a user 
        having multiple ACLs that provided access to the same utility. This raises the question on 
        what to do if one ACL is allowed, and another is disabled. I can either explicitly deny access 
        if any ACL is found with a disabled flag, or just skip the ACL and look for an enabled one. 
        For now I am going to do the latter.
        """    
        
        # Check host access
        if self.user.type == T_HOST:
            access_status = self._check_host_access()
            if not access_status['valid']:
                return access_status
            return valid()
            
        # Check user access
        else:
        
            # Access status object
            group_access = {}
        
            # Look through each ACL grouping
            for group, acl_obj in self.user.acls.iteritems():
                
                # Group level access
                group_access[group] = {}
                
                # Check object and global access
                group_access[group] = {
                    'global': self._check_global_access(acl_obj['global']),
                    'object': self._check_object_access(acl_obj['object'], group)
                } 
                
            # Check the group access object
            obj_error  = ''
            can_access = False
            for group, access in group_access.iteritems():
                for type, status in access.iteritems():
                    if status['valid']:
                        can_access = status
                    
                    # Capture any object errors
                    if (type == 'object') and not (status['valid']):
                        obj_error = status['content']
            
            # Access allowed
            if can_access:
                return can_access
            
            # Access denied
            else:
                err_msg = 'Access denied to utility [%s]%s' % (self.utility.path, obj_error)
                
                # Log the error message
                LOG.error(err_msg)
                
                # Return the authentication error
                return invalid(err_msg)
        
    def _authorize(self):
        """
        Worker method used to make sure the API user has the appropriate permissions
        required to access the utility.
        """
        
        # Permit access to <auth/get> for all API users with a valid API key
        if self.utility.path == PATH.GET_TOKEN:
            return self._set_authorization(True)
            
        # Log the initial ACL authorization request
        LOG.info('Running ACL gateway validation: utility=%s, %s=%s' % (self.utility.path, self.user.type, self.user.name))
        
        # If the user is not a member of any groups (and not a host account type)
        if not self.user.groups and self.user.type == T_USER:
            return self._set_authorization(False, LOG.error('User [%s] is not a member of any groups, membership required for utility authorization' % (self.user.name)))
        
        # Check if the account has access
        try:
            access_status = self._check_access()
            if not access_status['valid']:
                return self._set_authorization(False, access_status['content'])
            LOG.info('ACL gateway authorization success: %s=%s, utility=%s' % (self.user.type, self.user.name, self.utility.path))
            
            # Account has access
            return self._set_authorization(True)
            
        # ACL gateway critical error
        except Exception as e:
            return self._set_authorization(False, LOG.exception('Failed to run ACL gateway: %s' % str(e)))
    
    def target_object(self):
        """
        Public method used to extract the target object ID from the API data.
        """
        if self.request.data:
            return None if not (self.obj_key in self.request.data) else self.request.data[self.obj_key]
        return None
        
    def authorized_objects(self, type, path=None, filter=None):
        """
        Public method used to construct a list of authorized objects of a given type for the 
        API user.
        
        TODO: Need to filter out ACLs when doing the ACL object class to only include ACLs that apply for the
        current utility.
        """
        
        # Create the authorized objects list
        return ACLAuthObjects(self.user, type, (path if path else self.utility.path)).get(filter)