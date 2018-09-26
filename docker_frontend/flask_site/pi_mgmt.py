from __future__ import print_function
from flask import Flask, g, jsonify
from flask import render_template
from influxdb import InfluxDBClient
import sys
import json
import requests
from datetime import datetime, timedelta
import time
from dateutil import parser

app = Flask(__name__)

db_ip = '163.221.68.206'

global client

@app.before_first_request
def do_something_only_once():
    global client
    client = InfluxDBClient(db_ip, 8086, 'root', 'root', 'bl01_db')

def get_measurements_list():
    query_str = 'SHOW MEASUREMENTS ON pi_management'
    result = client.query(query_str)
    print(result)
    points = result.get_points()

    meas_list = []

    for item in points:
        meas_list.append(item['name'])

    return meas_list

def get_data(hostname):
    #TODO: Change so it will iterate through all available measurements
    query_str = 'SELECT last(*) FROM \"pi_management\".\"autogen\".\"' + hostname + '\";'
    result = client.query(query_str)
    #result = client.query('SELECT "ip", "pi_name" FROM "pi_management"."autogen"."pi_management_info";')
    return result

def get_last_timestamp(hostname):
    query_str = 'SELECT last(pi_name), time FROM \"pi_management\".\"autogen\".\"' + hostname + '\";'
    result = client.query(query_str)
    return result

@app.route('/get_latest_records')
def get_latest_records():
    host_list = get_measurements_list()
    names = []

    # node_array = []
    node_obj = {}
    # for host in host_list:




    counter = 0
    for host in host_list:
        # counter += 1
        result = get_data(host)
        points = result.get_points()
        data = {}
        for item in points:

            counter += 1
            ts = get_last_timestamp(item['last_pi_name'])
            ts_p = ts.get_points()
            time_in = ''

            for ti in ts_p:
                time_in = ti['time']


            dt_o = parser.parse(time_in)
            tzz = dt_o + timedelta(hours=9)

            data['timestamp'] = str(tzz)[:-6]
            data['cpu_usage'] = [item['last_cpu_usage_0'], \
                                 item['last_cpu_usage_1'], \
                                 item['last_cpu_usage_2'], \
                                 item['last_cpu_usage_3']]

            data['disk_usage'] = [item['last_disk_usage_free'], \
                                  item['last_disk_usage_total'], \
                                  item['last_disk_usage_used']]

            network = {}
            network['eth0'] = {'ip_address' : item['last_network_eth0_ip_address'], \
                               'nic_speed' : item['last_network_eth0_nic_speed']}

            network['wlan0'] = {'ip_address' : item['last_network_wlan0_ip_address'], \
                                'nic_speed' : item['last_network_wlan0_nic_speed']}

            data['network'] = network

            data['tasks'] = [item['last_tasks_queue_0'], \
                             item['last_tasks_queue_1'], \
                             item['last_tasks_queue_2']]

            data['virtual_memory'] = [item['last_virtual_memory_available'], \
                                  item['last_virtual_memory_total'], \
                                  item['last_virtual_memory_used']]  
            break

        node_obj[host] = data
    # node_array.append(node_obj)
    s = ''
    for h in node_obj:
        s = h
    j = json.dumps(node_obj)
    # d = json.loads(j)
    # return str(d['raspberrypi3-01']['virtual_memory'][0])
    return j
    # return jsonify(node_obj)
    # return str(len(node_obj))
    # return str(counter)

@app.route('/get_latest_records/<hostname>')
def show_records(hostname):
    uri = "http://163.221.68.211:5000/get_latest_records"
    try:
        uResponse = requests.get(uri)
    except requests.ConnectionError:
       return "Connection Error"  
    Jresponse = uResponse.text
    data = json.loads(Jresponse)
    return str(data[hostname])

@app.route('/')
def hello():
    pi_list = []

    host_list = get_measurements_list()
    pi_list.append(host_list)
    pi_list.append(" ")
    for host in host_list:
        result = get_data(host)
        points = result.get_points()
        output = 'Raspberry Pi available'

        for item in points:
            pi_name = item['last_pi_name']
            ip_addr = item['last_network_eth0_ip_address']
            ts = get_last_timestamp(pi_name)
            ts_p = ts.get_points()
            time_in = ''

            for ti in ts_p:
                time_in = ti['time']
            row = pi_name + ' : ' + ip_addr + ', last seen: ' + time_in 
            pi_list.append(row)

    return render_template('list.html', pi_list=pi_list)

def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

@app.route('/manager')
def manager():
    host_list = get_measurements_list()
    uri = "http://163.221.68.211:5000/get_latest_records"
    try:
        uResponse = requests.get(uri)
    except requests.ConnectionError:
       return "Connection Error"  
    Jresponse = uResponse.text
    data = json.loads(Jresponse)

    timestamp = str(data['raspberrypi3-01']['timestamp'])
    dt_o = parser.parse(timestamp)
    tzz = dt_o + timedelta(hours=9)

    return render_template('index.html', latest_records=data, host_list=host_list, timestamp=tzz)

#TODO: Use websockets here!    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)