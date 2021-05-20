import sys, datetime, os
from picamera import PiCamera
import paho.mqtt.client as mqtt
from time import sleep

#setup variables and values
coop_cam1 = PiCamera()
client = mqtt.Client()

# these are the pins that interface to the L298N driver board and tell it which way to spin
openPin = 34
closePin = 35

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("Door_Actions")

def on_message(client, userdata, msg):
    payload = str(msg.payload.decode("utf-8"))
    print("message received " ,payload)
    print("message topic=",msg.topic)
    print("message qos=",msg.qos)
    print("message retain flag=",msg.retain)
    
    if (payload == 'coop_close'):
        print("CLOSE!")
        # The door will close once I add the motor controlls here
        # it also needs to then reply with a message on the status of the door

        # turn on CLOSE pin

        # sleep long enough to open door (some number of seconds)

        # turn off close pin

        # publish new door state message
        client.publish("Door_Status", "CLOSED")

    elif (payload == 'coop_open'):
        print("OPEN!")
        # The door will open once I add the motor controls here
        # it also needs to then reply with a message on the status of the door

        # turn on OPEN pin

        # sleep long enough to open door (some number of seconds)

        # turn off open pin

        # publish new door state message
        client.publish("Door_Status", "OPEN")

client.on_connect = on_connect
client.on_message = on_message
#this device is going to be "always on" and needs to
#be listening at all times to function so connect immediately
client.connect("192.168.68.115",1883,60)
client.loop_start()

while True:
    try:
        coop_cam1.capture('/var/www/html/coop_pic.jpg')
        print("took a pic!")
        sleep(20)

    except KeyboardInterrupt:
        client.disconnect()
        client.loop_stop()
        sys.exit()

