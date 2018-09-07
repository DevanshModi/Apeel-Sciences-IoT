##Apeel Sciences Prompt Sept 10th 2018
import time, datetime, io, json, uuid, requests, boto3, serial, os
from serial.tools import list_ports
from random import randint
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient



class connector:
    def __init__(self):
        self.mode = "both"
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
            "image":self.store_image(),
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
    def store_image(self):
        name = str(uuid.uuid4())

        uri_duration = 2592000  # 30 days = 30 * 86400 seconds
        access_key =  os.environ.get('AWS_KEY')
        access_sig = os.environ.get('AWS_SIG')

        s3_client = boto3.client('s3',aws_access_key_id=access_key, aws_secret_access_key=access_sig)

        url = s3_client.generate_presigned_url('put_object', Params={'Bucket': 'apeel', 'Key': name+'.jpg'},ExpiresIn=uri_duration)

        return url

    def callback(self, client, userdata, message):

        print("Received a new message: ")
        print(message.payload)
        print("from topic: ")
        print(message.topic)
        print("--------------\n\n")



####################################
host = 'a90y3e0ptmg5b.iot.us-east-2.amazonaws.com'
rootCAPath = 'cert/root-CA.crt'
certificatePath = 'cert/Vendor_Measurement-1.cert.pem'
privateKeyPath = 'cert/Vendor_Measurement-1.private.key'
port = 8883
useWebsocket = False
clientId = 'Apeel-Device-1'
topic = '/sdk/test/Python'

def test_code():
    conn = connector()

    # conn.read_sensors()
    # Init AWSIoTMQTTClient
    myAWSIoTMQTTClient = None
    if useWebsocket:
        myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
        myAWSIoTMQTTClient.configureEndpoint(host, port)
        myAWSIoTMQTTClient.configureCredentials(rootCAPath)
    else:
        myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
        myAWSIoTMQTTClient.configureEndpoint(host, port)
        myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    # AWSIoTMQTTClient connection configuration
    myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)

    myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing

    #Used to configure the draining speed to clear up the queued requests when the connection is back.
    myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    myAWSIoTMQTTClient.configureConnectDisconnectTimeout(5)  # 10 sec
    myAWSIoTMQTTClient.configureMQTTOperationTimeout(10)  # 5 sec

    myAWSIoTMQTTClient.
    # Connect and subscribe to AWS IoT
    myAWSIoTMQTTClient.connect()

    if conn.mode == 'both' or conn.mode == 'subscribe':
        myAWSIoTMQTTClient.subscribe(topic, 1, conn.callback)

    time.sleep(2)

    # Publish to the same topic in a loop forever
    loopCount = 0
    while True:
        if conn.mode == 'both' or conn.mode == 'publish':
            message = conn.read_sensors()
            messageJson = message
            #print message
            myAWSIoTMQTTClient.publish(topic, messageJson, 1)
            #print('Published topic %s: %s\n' % (topic, messageJson))
            loopCount += 1
        time.sleep(2)

test_code()

####################################

