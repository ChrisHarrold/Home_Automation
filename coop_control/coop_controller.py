import sys, datetime, os
from picamera import PiCamera
import paho.mqtt.client as mqtt
from time import sleep

#setup variables and values
coop_cam1 = PiCamera()
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("Door_Actions")

def on_message(client, userdata, msg):
    print("message received " ,str(msg.payload.decode("utf-8")))
    print("message topic=",msg.topic)
    print("message qos=",msg.qos)
    print("message retain flag=",msg.retain)
    
    if (msg.payload == 'coop_close'):
        print("CLOSE!")
        # The door will close once I add the motor controlls here
        # it also needs to then reply with a message on the status of the door
      
    elif (msg.payload == 'coop_open'):
        print("OPEN!")
        # The door will open once I add the motor controls here
        # it also needs to then reply with a message on the status of the door

client.on_connect = on_connect
client.on_message = on_message
#Normally I wouldn't connect to the MQ server right away, but this device is going to be "always on" and needs to
#be listening at all times to function
client.connect("192.168.68.115",1883,60)
client.loop_start()

while True:
    try:
        coop_cam1.capture('/var/www/html/coop_pic.jpg')
        print("took a pic!")
        sleep(20)
        client.publish("Door_Status", "OPEN")
        sleep(20)
        client.publish("Door_Status", "CLOSED")
        sleep(20)

    except KeyboardInterrupt:
        client.disconnect()
        sys.exit()

