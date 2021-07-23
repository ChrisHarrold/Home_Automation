import sys, datetime, os
from picamera import PiCamera
import paho.mqtt.client as mqtt
from time import sleep
import RPi.GPIO as GPIO
from ds18b20 import DS18B20

#setup variables and values
coop_cam1 = PiCamera()
client = mqtt.Client()

# these are the pins that interface to the L298N driver board 
# and tell it which way to spin - motor 1 controls the coop door
# itself and motor 2 will eventually control the vent for heat control

openPin1 = 5
closePin1 = 6
openPin2 = 200
closePin2 = 201
active_running_led = 13


GPIO.setmode(GPIO.BCM)
GPIO.setup(active_running_led, GPIO.OUT, initial=1)
GPIO.setup(openPin1, GPIO.OUT)
GPIO.setup(closePin1, GPIO.OUT)
#GPIO.setup(openPin2, GPIO.OUT)
#GPIO.setup(closePin2, GPIO.OUT)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("Door_Actions")

def on_message(client, userdata, msg):
    payload = str(msg.payload.decode("utf-8"))
    #print("message received " ,payload)
    #print("message topic=",msg.topic)
    #print("message qos=",msg.qos)
    #print("message retain flag=",msg.retain)
    
    if (payload == 'coop_close'):
        print("CLOSE!")
        # The door will close once I add the motor controlls here
        # it also needs to then reply with a message on the status of the door

        # turn on CLOSE pin
        GPIO.output(closePin1, 1)
        # sleep long enough to open door (some number of seconds)
        sleep(10)
        # turn off close pin
        GPIO.output(closePin1, 0)
        # publish new door state message
        client.publish("Door_Status", "CLOSED")

    elif (payload == 'coop_open'):
        print("OPEN!")
        # The door will open once I add the motor controls here
        # it also needs to then reply with a message on the status of the door

        # turn on OPEN pin
        GPIO.output(openPin1, 1)
        # sleep long enough to open door (some number of seconds)
        sleep(10)
        # turn off open pin
        GPIO.output(openPin1, 0)
        # publish new door state message
        client.publish("Door_Status", "OPEN")

def publish_message(the_message):
    client.publish("Coop_Picture", the_message)


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
        publish_message("'{\"Unit\":\"Coop\", \"Picture\":\"Updated\"}'")
        sleep(60)

    except KeyboardInterrupt:
        client.disconnect()
        client.loop_stop()
        GPIO.output(active_running_led, 0)
        GPIO.cleanup()
        sys.exit()

