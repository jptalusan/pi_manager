
#Notes:
#https://www.influxdata.com/blog/getting-started-python-influxdb/

from influxdb import InfluxDBClient
import psutil
import os
import socket
import fcntl
import struct
from datetime import datetime
import time
import conf
import json
from flatten_json import flatten

def getCPUuse():
    return(str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip(\
)))

# client = InfluxDBClient(db_ip, 8086, 'root', 'root', 'bl01_db')

#result = client.query('SELECT mean("noise") AS "mean_noise" FROM "bl01_db"."autogen"."meas_1" \
#           WHERE time > now() - 1h AND "bt_address"='FA114A6A871C' AND "gateway"='raspberrypi3-08' AND "sensor_type"='IM' GROUP BY time(10s), "bt_address";')

#result = client.query('select noise from bl01_db.autogen.meas_1;')

# result = client.query('select mean("noise") as "mean_noise" from bl01_db.autogen.meas_1 where time > now() - 5m group by time(10s)')

# print("Result: {0}".format(result))

pi_mgmt =InfluxDBClient(conf.INFLUXDB_IP, \
                        conf.INFLUXDB_PORT, \
                        conf.INFLUXDB_USERNAME, \
                        conf.INFLUXDB_PASSWORD, \
                        conf.INFLUXDB_DBNAME)

'''
#https://psutil.readthedocs.io/en/latest/

cpu_count = psutil.cpu_count()

#might have to run twice?
cpu_percent = psutil.cpu_percent(interval=1)
cpu_percent_list = psutil.cpu_percent(interval=1, percpu=True)
cpu_freq_tuple = psutil.cpu_freq() #cpu_freq_tuple.current/min/max
psutil.virtual_memory() #total, available
psutil.disk_usage('/') #total, free
psutil.net_if_addrs() #wlan0, address
speed test python, https://pypi.org/project/iperf3/ for iperf, server?
speed test for internet:  https://pypi.org/project/pyspeedtest/, probably above is betters
'''

hostname = socket.gethostname()

ts = time.time()
st = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z')

def generate_json(hostname, time):
    #JSONArray
    array = []

    #JSONObjects
    util_obj = {}
    util_obj["measurement"] = "pi_management_info"

    user_obj = {}
    user_obj["user"] = "Test"

    util_obj["tags"] = user_obj

    util_obj["time"] = st

    field_obj = {}
    field_obj["pi_name"] = hostname

    cpu_usage_list = psutil.cpu_percent(interval=1, percpu=True)
    field_obj["cpu_usage"] = cpu_usage_list

    #virtual memory in bytes
    vir_mem_data = psutil.virtual_memory()
    vir_mem_keys = ['total', 'used', 'available']
    vir_mem_vals = [vir_mem_data.total, vir_mem_data.used, vir_mem_data.available]
    vir_mem_objs = dict(zip(vir_mem_keys, vir_mem_vals))

    field_obj["virtual_memory"] = vir_mem_objs

    disk_keys = ['total', 'used', 'free']
    disk_vals = psutil.disk_usage('/')
    disk_objs = dict(zip(disk_keys, disk_vals))

    field_obj["disk_usage"] = disk_objs

    #network interfaces
    netif_data = psutil.net_if_addrs()
    netif_stat = psutil.net_if_stats()

    netif_keys = ['eth0', 'wlan0']
    netif_list = []
    netif_labels = ['ip_address', 'nic_speed']

    for ind, val in enumerate(netif_keys):
        temp = []
        ip_address = netif_data[val][0].address
        nic_speed = netif_stat[val].speed
        temp.append(ip_address)
        temp.append(nic_speed)
        netif_dict = dict(zip(netif_labels, temp))
        netif_list.append(netif_dict)

    netif_objs = dict(zip(netif_keys, netif_list))
    field_obj["network"] = netif_objs
    #TODO: Maybe add iperf3 results here? to server (NUC)?


    #tasks
    field_obj["tasks_queue"] = ['task1', 'task2', 'task3']

    #Collating
    util_obj["fields"] = field_obj

    array.append(util_obj)

    # test = util_obj["fields"]["network"]
    # for key, value in test.iteritems():
    #     print(key, value)

    return array

vir_mem_vals = psutil.disk_usage('/')
# print(type(vir_mem_vals))

json_body = generate_json(hostname, st)
# print(type(json_body))
# print(json.dumps(json_body))


# print(json_body[0]["fields"]["cpu_usage"])


# print(type(json_body))
# print(type(json_body[0]))
#i can use this so not useless
#remove fields or get only inside of fields, and then put it back into a new json haha for fields obj
flat_fields = flatten(json_body[0]["fields"])
# print(flat_fields)

#Waste of time, need to parse this into separte fields:
#https://stackoverflow.com/questions/41183756/inserting-list-as-value-in-influxdb

influxdb_input = [
            {
                "measurement": hostname,
                "tags": {
                    "user": "Test",
                },
                "time": st,
                "fields": flat_fields
            }
            ]
#TODO: List of measurements (aka hostnames)
# query_str = 'SHOW MEASUREMENTS ON pi_management'
# query_str = 'SELECT last(*) FROM \"pi_management\".\"autogen\".\"' + 'raspberrypi3-08' + '\";'
# query_str = 'SELECT last(pi_name), time FROM \"pi_management\".\"autogen\".\"' + 'raspberrypi3-08' + '\";'
# pi_mgmt_result = pi_mgmt.query(query_str)
# print(pi_mgmt_result)

# print(influxdb_input)

#TODO: need to convert string to int or long so can graph
#TODO: What about nulls? if added like more columns
#TODO: Cannot delete, so just add for history
#INSERT
pi_mgmt.write_points(influxdb_input)

#TODO GET LATEST without messing up time
# query_str = 'SELECT last(*) FROM \"pi_management\".\"autogen\".\"' + hostname + '\";'
# print(query_str)
# pi_mgmt_result = pi_mgmt.query(query_str)
# pi_mgmt_result = pi_mgmt.query('SELECT "ip", "pi_name" FROM "pi_management"."autogen"."pi_management_info";')
# print(pi_mgmt_result)

# print pi_mgmt.get_list_database()

# ResultSet({'(u'raspberrypi3-08', None)': [{u'last_disk_usage_used': 2323107840L, u'last_network_eth0_ip_address': u'163.221.68.211', u'last_network_wlan0_nic_speed': 0, u'last_disk_usage_total': 62972461056L, u'last_virtual_memory_used': 287379456, u'last_virtual_memory_available': 631955456, u'last_network_wlan0_ip_address': u'169.254.208.17', u'last_network_eth0_nic_speed': 100, u'last_tasks_queue_0': u'task1', u'last_tasks_queue_1': u'task2', u'last_tasks_queue_2': u'task3', u'last_virtual_memory_total': 1018093568, u'time': u'1970-01-01T00:00:00Z', u'last_pi_name': u'raspberrypi3-08', u'last_disk_usage_free': 58059616256L, u'last_cpu_usage_2': 3, u'last_cpu_usage_3': 0, u'last_cpu_usage_0': 0, u'last_cpu_usage_1': 1}]})