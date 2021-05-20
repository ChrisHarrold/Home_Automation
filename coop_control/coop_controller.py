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
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)
    
    if (msg.payload == 'coop_close'):
        print("CLOSE!")
      
    elif (msg.payload == 'coop_open'):
        print("OPEN!")

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
        client.publish("Door_Status", "OPEN")
        sleep(20)
        
    except KeyboardInterrupt:
        client.disconnect()
        sys.exit()

