##Apeel Sciences Prompt Sept 10th 2018
import time, datetime, io, json, uuid, requests, boto3, serial, os
from serial.tools import list_ports
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
            "timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "humidity":randint(0,50),
            "actions":{},
            "temp":randint(0,50),
            "connected_devices":[device.hwid for device in list(self.connected)]
        }

        sample = json.dumps(sample)

        return sample

    #TODO: 1 Switch to environment variables 2 Upload File to Pre-Signed URL
    ##
    def store_data(self):
        name = str(uuid.uuid4())

        uri_duration = 2592000  # 30 days = 30 * 86400 seconds
        access_key =  os.environ.get('AWS_KEY')
        access_sig = os.environ.get('AWS_SIG')

        s3_client = boto3.client('s3',aws_access_key_id=access_key, aws_secret_access_key=access_sig)

        url = s3_client.generate_presigned_url('put_object', Params={'Bucket': 'apeel', 'Key': name+'.jpg'},ExpiresIn=uri_duration)

        #
####################################

def test_code():
    conn = connector()
    print conn.auth_list

    while True:
        # conn.check_serial_devices()
        # print conn.connected
        conn.store_data()

        time.sleep(5)

test_code()

####################################
    
    
