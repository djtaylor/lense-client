import re
import json
import time
import copy
import datetime
import MySQLdb

# Django Libraries
from django.db import connection
from django.core.serializers.json import DjangoJSONEncoder

# CloudScape Variables
from cloudscape.common.vars import A_RUNNING

# CloudScape Libraries
from cloudscape.common.utils import valid, invalid
from cloudscape.engine.api.app.agent.models import DBHostStats
from cloudscape.engine.api.app.host.models import DBHostDetails, DBHostGroupMembers, DBHostSystemInfo
from cloudscape.engine.api.app.cluster.models import DBClusterIndex

class ClusterSearch:
    """
    Search the cluster index.
    """
    def __init__(self, parent):
        self.api   = parent

    def _get_rows(self, cursor):
        desc = cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]

    def launch(self):
        """
        Worker method for searching the cluster index.
        
        WARNING
        
        This is a really weak class right now. I'm not sanitizing the SQL search string yet.
        """
        
        # Define the search string and query
        search_string  = MySQLdb.escape_string(self.api.data['string'])
        search_query   = 'SELECT * FROM cluster_index WHERE string LIKE \'%%%s%%\'' % search_string

        # Log the search query
        self.api.log.info('Constructed cluster search query: <%s>' % search_query)

        # Run the search
        try:
            
            # Open a manual connection and run the query
            cursor = connection.cursor()
            cursor.execute(search_query)
            
            # Fetch the results
            search_results = self._get_rows(cursor)
        except Exception as e:
            return invalid(self.api.log.exception('Failed to run cluster search: %s' % str(e)))
        
        # Return the results
        return valid(json.dumps(search_results))

class ClusterIndex:
    """
    Rebuild the cluster search index.
    """
    def __init__(self, parent):
        self.api      = parent
        
        # Search object mapper
        self.map      = {
            'host': {
                'extract':  self._extract_hosts,
                'utility': 'host/get'
            },
            'formula': {
                'extract':  self._extract_formulas,
                'utility': 'formula/get'
            },
            'datacenter': {
                'extract':  self._extract_datacenters,
                'utility': 'locations/datacenters/get'
            },
            'hgroup': {
                'extract':  self._extract_hgroups,
                'utility': 'host/group/get'
            },
            'user': {
                'extract':  self._extract_users,
                'utility': 'user/get'
            },
            'group': {
                'extract':  self._extract_groups,
                'utility': 'group/get'
            },
            'utility': {
                'extract':  self._extract_utils,
                'utility': 'auth/utility/get'
            }
        }
        
        # Portal base URL
        self.base_url = '%s://%s/portal' % (self.api.conf.portal.proto, self.api.conf.portal.host)
        
        # Index rows
        self.rows     = []
        
    def _extract_utils(self, utils):
        """
        Extract only the details required for a utility object row.
        """
        ret = []
        for util in utils:
            ret.append({
                'type':   'utility',
                'string': '%s %s %s %s %s' % (util['name'], util['desc'], util['method'], util['cls'], util['mod']),
                'label':  '%s:%s' % (util['name'], util['method']),
                'url':    '%s/admin?panel=utilities&utility=%s' % (self.base_url, util['uuid']) 
            })
        return ret
        
    def _extract_groups(self, groups):
        """
        Extract only the details required for a group object row.
        """
        ret = []
        for group in groups:
            ret.append({
                'type':   'group',
                'string': '%s %s' % (group['name'], group['desc']),
                'label':  '%s' % group['name'],
                'url':    '%s/admin?panel=groups&group=%s' % (self.base_url, group['uuid'])     
            })
        return ret
        
    def _extract_users(self, users):
        """
        Extract only the details required for a user object row.
        """
        ret = []
        for user in users:
            ret.append({
                'type':   'user',
                'string': '%s' % user['username'],
                'label':  '%s' % user['username'],
                'url':    '%s/admin?panel=users&user=%s' % (self.base_url, user['username'])        
            })
        return ret
        
    def _extract_hgroups(self, hgroups):
        """
        Extract only the details required for a host group object row.
        """
        ret = []
        for hgroup in hgroups:
            ret.append({
                'type':   'hgroup',
                'string': '%s' % hgroup['name'],
                'label':  '%s' % hgroup['name'],
                'url':    '%s/hosts?panel=groups&group=%s' % (self.base_url, hgroup['uuid'])     
            })
        return ret
        
    def _extract_datacenters(self, datacenters):
        """
        Extract only the details required for a datacenter object row.
        """
        ret = []
        for datacenter in datacenters:
            ret.append({
                'type':   'datacenter',
                'string': '%s %s' % (datacenter['name'], datacenter['label']),
                'label':  '%s: %s' % (datacenter['name'], datacenter['label']),
                'url':    '%s/admin?panel=datacenters&datacenter=%s' % (self.base_url, datacenter['uuid'])   
            })
        return ret
        
    def _extract_formulas(self, formulas):
        """
        Extract only the details required for a formula object row.
        """
        ret = []
        for formula in formulas:
            ret.append({
                'type':   'formula',
                'string': '%s %s %s' % (formula['name'], formula['label'], formula['desc']),
                'label':  '%s: %s' % (formula['name'], formula['label']),
                'url':    '%s/formula?panel=details&formula=%s' % (self.base_url, formula['uuid'])   
            })
        return ret
        
    def _extract_hosts(self, hosts):
        """
        Extract only the details required for a host object index row.
        """
        
        # Get all datacenters
        datacenters = self.api.acl.authorized_objects('datacenter', 'locations/datacenters/get')
        
        # Construct the return list
        ret = []
        for host in hosts:
            datacenter = [x['name'] for x in datacenters.details if x['uuid'] == host['datacenter']] 
            ret.append({
                'type':   'host',
                'string': '%s %s %s %s %s %s %s' % (host['name'], host['ip'], datacenter, host['os_type'], host['sys']['os']['distro'], host['sys']['os']['version'], host['sys']['os']['arch']),
                'label':  '%s: %s %s, %s' % (host['name'], host['sys']['os']['distro'], host['sys']['os']['version'], host['ip']),
                'url':    '%s/hosts?panel=details&host=%s' % (self.base_url, host['uuid'])
            })
        return ret
        
    def _index_objects(self):
        """
        Walk through the map and extract all objects.
        """
        for t,o in self.map.iteritems():
            self.rows = self.rows + o['extract'](self.api.acl.authorized_objects(t, o['utility']).details)
        
    def launch(self):
        """
        Worker method for finding and returning a list of objects.
        """
        
        # Index all cluster objects
        self._index_objects()

        # Flush the old index
        DBClusterIndex.objects.all().delete()

        # Rebuild the index
        for row in self.rows:
            DBClusterIndex(**row).save()

        # Return success
        return valid('Successfully rebuilt cluster search index')

class ClusterStats:
    """
    Retrieve host statistics, crunch into an object containing averages and current
    statistics, and return a statistics object for use by either D3JS or another
    application defined by the user.
    """
    def __init__(self, parent):
        self.api = parent
        
        # Date format
        self.date_fmt  = '%Y-%m-%d %H:%M:%S'
        
        # Constructed statistics
        self.stats     = None
        
        # Get any filters
        self.filters   = {} if not ('filter' in self.api.data) else self.api.data['filter']
        
        # CPU core and Hz counter
        self.cpu_cores = 0
        self.cpu_ghz   = 0
        
        # Host objects
        self.host_list = []
        
        # I/O groups
        self.io_groups = {
            'net_io':   {
                'db_key':    'network_io',
                'label':     'Network I/O',
                'unit':      'B/s',
                'stat_keys': ['bytes_sent', 'bytes_recv']
            },
            'disk_io':  {
                'db_key':    'disk_io',
                'label':     'Disk I/O',
                'unit':      'B/s',
                'stat_keys': ['rbytes', 'wbytes']
            }
        }
        
        # Statistic totals
        self.totals    = {
            'host': {
                'total':        0,
                'linux':        0,
                'windows':      0,
            },
            'cpu':  {
                'total':        float(0),
                'used':         float(0),
            },
            'mem':  {
                'used':         [],
                'total':        [],
                'free':         []
            },
            'disk': {
                'total':        float(0),
                'used':         float(0)
            },
            'net_io':  {},
            'disk_io': {}
        }
        
    def _percent_calc(self, total, used):
        """
        Return a percentage retrieved from a total/used value pair.
        """
        total_num = float(total)
        used_num  = float(used)
        
        # Cannot divide by 0
        if total_num == 0:
            return 0.0
        
        # Calculate the percentage used
        '%2.f' % float(100.0 * used_num / total_num)
        
    def _bytes_to(self, bytes, unit='G'):
        """
        Convert bytes value to GB/MB/KB.
        """
        
        # Division counter
        counter = {'G': 3, 'M': 2, 'K': 1}
        
        # If using an unsupported unit
        if not unit in counter:
            return bytes
        
        # Convert the value to an integer
        bytes_num = int(bytes)
        
        # Convert to the target unit
        count = 0
        while (count < counter[unit]):
            bytes_num = float(bytes_num / 1024)
            count += 1
        
        # Return the converted value
        return '%.2f' % bytes_num
        
    def _get_latest_stats(self, uuid, stat_rows):
        """
        Construct the latest disk, CPU, and memory statistics for the host.
        """
        
        # I/O Groups
        stat_count = 0
        stat_last  = {}
        for row in stat_rows:
            stat_count += 1
            date_str    = row['created'].strftime(self.date_fmt)
            
            # Process each I/O group
            row_avgs  = {}
            for key, attrs in self.io_groups.iteritems():
                
                # Set up the row averages
                if not key in row_avgs:
                    row_avgs[key] = {}
                    for stat_key in attrs['stat_keys']:
                        row_avgs[key][stat_key] = 0
            
                # Initialize the statistics group
                if not str(stat_count) in self.totals[key]:
                    self.totals[key][str(stat_count)] = {
                        'date': date_str,
                        'data': { k: 0 for k in attrs['stat_keys'] }
                    }
                    
                # Process each group device
                obj_stats = json.loads(row[attrs['db_key']])
                for obj, stats in obj_stats.iteritems():
                    for stat_key in attrs['stat_keys']:
                        row_avgs[key][stat_key] += stats[stat_key]
                        
                # Skip the first iteration, need two sets of data for averages
                if not stat_count == 1:
                    for stat_key in attrs['stat_keys']:
                        self.totals[key][str(stat_count)]['data'][stat_key] += (stat_last[key][stat_key] - row_avgs[key][stat_key]) / 10
                
                # Store the current statistics for the next iteration
                stat_last[key] = row_avgs[key]
            
        # Disk usage
        _disk = json.loads(stat_rows[0]['disk_use'])
        for disk, stats in _disk.iteritems():
            self.totals['disk']['used'] += float(stats['used'])
            
        # CPU usage
        _cpu = json.loads(stat_rows[0]['cpu_use'])
        self.totals['cpu']['total'] += float(100)
        self.totals['cpu']['used']  += float(_cpu['used'])
        
        # Memory averages
        _mem = json.loads(stat_rows[0]['memory_use'])
        self.totals['mem']['used'].append(float(_mem['used']))
        self.totals['mem']['free'].append(float(_mem['free']))
        self.totals['mem']['total'].append(float(_mem['total']))
        
    def _map_io(self, key):
        """
        Map network and disk I/O data for the host.
        """
        
        # Base I/O data
        _iodata = {
            'chart': {
                key: {
                    'data_keys': { 'x': 'date', 'y': self.io_groups[key]['stat_keys'] },
                    'label': self.io_groups[key]['label'],
                    'type': 'io',
                    'unit':  self.io_groups[key]['unit'],
                    'group': []
                }}}
        
        # Group data
        _groupdata = { 'label': 'Cluster', 'stats': [] }
        for k,d in self.totals[key].iteritems():
            _groupdata['stats'].append({ 'date': d['date'], 'data': d['data']})
        
        # Sort the stats by date and append to base I/O data
        _groupdata['stats'].sort(key=lambda x: datetime.datetime.strptime(x['date'], self.date_fmt))
        _iodata['chart'][key]['group'].append(_groupdata)
        
        # Return the constructed data object
        return _iodata
        
    def _crunch_totals(self):
        """
        Crunch statistic totals into a format that will be used by either D3JS or another
        user application for rendering data.
        """
        
        # Perform CPU calculations
        cpu_pused    = self._percent_calc(self.totals['cpu']['total'], self.totals['cpu']['used'])
        cpu_pfree    = '%.2f' % (100.0 - float(cpu_pused))
        
        # Perform disk calculations
        disk_gbtotal = self._bytes_to(self.totals['disk']['total'], unit='G')
        disk_gbused  = '%.2f' % float(self.totals['disk']['used'])
        disk_pused   = self._percent_calc(disk_gbtotal, disk_gbused)
        
        # Perform memory calculations
        mem_mbused   = '%.2f' % float(sum(self.totals['mem']['used']))
        mem_mbtotal  = '%.2f' % float(sum(self.totals['mem']['total']))
        mem_pused    = self._percent_calc(mem_mbtotal, mem_mbused)
        
        # Constructed stats object
        c_stats = {
            'host': {
                'total':         self.totals['host']['total'],
                'linux':         self.totals['host']['linux'],
                'windows':       self.totals['host']['windows']
            },
            'cpu': {
                'cores':         self.cpu_cores,
                'ghz_total':     self.cpu_ghz,
                'ghz_used':      (float(cpu_pused) * self.cpu_ghz) / 100.0,
                'ghz_free':      (float(cpu_pfree) * self.cpu_ghz) / 100.0,
                'percent_used':  float(cpu_pused),
                'percent_free':  float(cpu_pfree),
            },
            'mem': {
                'mb_free':      float('%.2f' % float(sum(self.totals['mem']['free']))),
                'mb_used':      float(mem_mbused),
                'mb_total':     float(mem_mbtotal),
                'percent_used': float(mem_pused),
                'percent_free': float(100 - float(mem_pused))
            },
            'disk': {
                'gb_total':     float(disk_gbtotal),
                'gb_used':      float(disk_gbused),
                'gb_free':      float('%.2f' % (float(disk_gbtotal) - float(disk_gbused))),
                'percent_used': float(disk_pused),
                'percent_free': float(100 - float(disk_pused))
            }
        }
        
        # Construct any I/O stats
        for key, attrs in self.io_groups.iteritems():
            _iostat = self._map_io(key)
            c_stats[key] = _iostat
        return c_stats
        
    def launch(self):
        """
        Worker method for gathering, crunching, and return cluster statistics.
        """
        
        # If filtering by host group
        hgroup = False
        if 'hgroup' in self.filters:
            hgroup = copy.copy(self.filters['hgroup'])
            del self.filters['hgroup']
        
        # Build a list of all authorized hosts
        authorized_hosts = self.api.acl.authorized_objects('host', 'host/get', self.filters)
        
        # If filtering by host group
        hgroup_members = False if not hgroup else [x['host_id'] for x in list(DBHostGroupMembers.objects.filter(group=hgroup).values())]
        
        # Construct the statistics for each host
        for host in authorized_hosts.details:
            
            # If filtering by host group
            if hgroup_members:
                if not host['uuid'] in hgroup_members:
                    continue
            
            # Get the stats row
            stat_rows = DBHostStats(host['uuid']).get(latest=30)
            
            # Start calculating statistics
            self.totals['host']['total'] += 1
            self.totals['host'][host['os_type']] += 1
            
            # Get the statistics for the host if it meets the criteria
            if (host['agent_status'] == A_RUNNING) and (len(stat_rows) >= 30):
                self._get_latest_stats(host['uuid'], stat_rows)
                
                # Get the size of all disks
                for disk in host['sys']['disk']:
                    self.totals['disk']['total'] += float(disk['size'])
                
                # Count the number of cores and Hz
                for cpu in host['sys']['cpu']:
                    
                    # Get the number of cores per CPU
                    num_cores       = int(cpu['cores'])
                    self.cpu_cores += num_cores
                    
                    # Calculate the total speed of the physical CPU
                    ghz_str         = re.compile(r'^.*[ ]([0-9\.]*)GHz.*$').sub(r'\g<1>', cpu['model'])
                    self.cpu_ghz   += float(ghz_str) * int(cpu['cores'])
            
        # Get the averages
        self.stats = self._crunch_totals()
        
        # Return the global statistics object
        return valid(json.dumps(self.stats, cls=DjangoJSONEncoder))