##Apeel Sciences Prompt Sept 10th 2018
import time, datetime, io, json, uuid, requests, boto3, serial, os, sqlite3
from serial.tools import list_ports
from random import randint
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except:
        print('sql-error')

    return None

class connector:
    def __init__(self, mode, DELAY, db, config):
        self.actions = {"light1":False, "update_config":False}
        self.mode = mode
        self.auth_list = []
        self.connected = set()
        self.DELAY = DELAY #Ideally should be much longer
        self.db_conn = create_connection(db)

        with open(config) as f:
            self.data = json.load(f)
        if type(self.data['auth_list']) == int and self.data['auth_list']==-1:
            self.auth_list = ['ALL']
        else:
            self.auth_list.extend(self.data['auth_list'])

    #Check if any new devices are attached
    #https://pyserial.readthedocs.io/en/latest/tools.html
    #Allowed Devices = AUTHORIZED USBs
    #TODO: Multithreading if there's significant gain in performance
    def check_serial_devices(self):
        ports = set([item for item in serial.tools.list_ports.grep("USB")])

        if self.auth_list[0] != 'ALL':
            ports = set([i for i in list(ports) if i.hwid in self.auth_list])

        new_devices = ports.difference(self.connected)
        removed = self.connected.difference(ports)

        self.connected = ports

    #Generate Sample data for now
    def read_sensors(self):
        sample = {
            "image":self.store_image(),
            "timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "humidity":randint(0,50),
            "actions":self.actions,
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

        actions = json.loads(message.payload)

        if not self.actions["light1"] and actions.get("light1") == 1:

            #Real world code would enable real output pins
            print "ALERT: Spoilage Light 1 Turned On!"

            self.actions["light1"]=True

        elif self.actions["light1"] and actions.get("light1") == 0:

            print "ALERT: Spoilage Light 1 Turned Off!"

            self.actions["light1"] = False

        #if actions.get("update_config"):
            #Do something here


def run_instance():
    conn = connector("both", 5, "apeel.db", "config.json")

    myAWSIoTMQTTClient = None
    if conn.data["useWebsocket"]:
        myAWSIoTMQTTClient = AWSIoTMQTTClient(conn.data["clientId"], useWebsocket=True)
        myAWSIoTMQTTClient.configureEndpoint(conn.data["host"], conn.data["port"])
        myAWSIoTMQTTClient.configureCredentials(conn.data["rootCAPath"])
    else:
        myAWSIoTMQTTClient = AWSIoTMQTTClient(conn.data["clientId"])
        myAWSIoTMQTTClient.configureEndpoint(conn.data["host"], conn.data["port"])
        myAWSIoTMQTTClient.configureCredentials(conn.data["rootCAPath"], conn.data["privateKeyPath"], conn.data["certificatePath"])

    # AWSIoTMQTTClient connection configuration
    myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)

    myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing

    #Used to configure the draining speed to clear up the queued requests when the connection is back.
    myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

    # Connect and subscribe to AWS IoT
    try:
        myAWSIoTMQTTClient.connect()
    except:
        print "Initial Connection Failed"

    if conn.mode == 'both' or conn.mode == 'subscribe':
        myAWSIoTMQTTClient.subscribe(str(conn.data["topic_sub"]), 1, conn.callback)

    time.sleep(2)

    # Publish to the same topic in a loop forever
    loopCount = 0
    while True:
        conn.check_serial_devices()

        ##Step 1: Check existing entries in sqlite database
        #db_rows = db_check_rows()

        ##if any, publish them first and add the current sensor reading to the database (FIFO order)
        #
        #
        if conn.mode == 'both' or conn.mode == 'publish':
            try:
                message = conn.read_sensors()
                messageJson = message

                # Add the current reading to database
                ## For each row in db_rows, publish them first
                ## Also, remember last few entries in memory to avoid duplication

                myAWSIoTMQTTClient.publish(str(conn.data["topic"]), messageJson, 1)
                #print('Published topic %s: %s\n' % (topic, messageJson))
                loopCount += 1
            except:
                #Internet disconnection
                print "Waiting for connection..."
                #myAWSIoTMQTTClient.connect()

        time.sleep(conn.DELAY)

run_instance()

