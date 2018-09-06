##Apeel Sciences Prompt Sept 10th 2018
import time
import serial
from serial.tools import list_ports
import io
import json
from random import randint


class connector:
    def __init__(self):
        self.auth_list = []
        self.connected = set()

        with open('config.json') as f:
            data = json.load(f)
        if type(data['auth_list']) == int and data['auth_list']==-1:
            self.auth_list = ['ALL']
        else:
            self.auth_list.extend(data['auth_list'])

    #Check if any new devices are attached
    #https://pyserial.readthedocs.io/en/latest/tools.html
    #Allowed Devices = AUTHORIZED USBs
    #TODO: Multithreading if significant change in performance
    def check_serial_devices(self):
        ports = set([item for item in serial.tools.list_ports.grep("USB")])

        if self.auth_list[0] != 'ALL':
            ports = set([i for i in list(ports) if i.hwid in self.auth_list])

        new_devices = ports.difference(self.connected)
        removed = self.connected.difference(ports)

        self.connected = ports

    def read_sensors(self):
        sample = {
            "image":"",
            "humidity":randint(0,50),
            "actions":{},
            "temp":randint(0,50)
        }

        sample["connected_devices"] = [device.hwid for device in list(self.connected)]

        sample = json.dumps(sample)
        pass

    def store_data(self):
        pass
    
    
####################################

def test_code():
    conn = connector()
    print conn.auth_list

    while True:
        conn.check_serial_devices()
        print conn.connected
        time.sleep(0.5)

test_code()

####################################
    
    
