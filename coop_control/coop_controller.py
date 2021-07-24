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
temp_sensor = DS18B20()
lightPin = 24



GPIO.setmode(GPIO.BCM)
GPIO.setup(active_running_led, GPIO.OUT, initial=1)
GPIO.setup(lightPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
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

def publish_message(the_topic, the_message):
    client.publish(the_topic, the_message)

def Light_Check() :
    state = GPIO.input(lightPin)
    if (state == True) :
        publish_message("Coop_Sensors", "'{\"Unit\":\"Coop\", \"Sensor\":\"Coop_Light\", \"Value\":\"DO NOT CLOSE\"}'")
    else :
        publish_message("Coop_Sensors", "'{\"Unit\":\"Coop\", \"Sensor\":\"Coop_Light\", \"Value\":\"READY TO CLOSE\"}'")

def Collect_Temp_Data() :
        # Get current water temperatures:
        # the "library" that is included DOES perform these two steps BUT
        # only the FIRST TIME the sensor is initialized. In order to update the sensor
        # you need to run these two command again. I feel the way RPi does 1-Wire
        # is a major deficiency really. Having to shell to the OS is not ideal.
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        Temp_sensor_count = temp_sensor.device_count()

        the_tempC = []
        the_tempF = []
        temp_temp_temp = 0
        # initialize a quick counter for the temp sensors - this will read as many as there are
        # but will only report out the first reading as is - can be extended to handle more
        i = 0
        #print(Temp_sensor_count)
        while i < Temp_sensor_count:
            try :
                temp_temp_temp = (temp_sensor.tempC(i))
            except IndexError :
                temp_temp_temp = 100

            the_tempC.append(temp_temp_temp)
            the_tempF.append((temp_temp_temp * 1.8) + 32)
            i += 1
            #print('Sensor reading: {0} '.format (temp_temp_temp))
        #lcd.cursor_pos = (2,0)
        #lcd.write_string('{0:.1f}'.format (the_tempC[0]))
        data1 = ('{{\"Unit\":\"Coop\",\"Sensor\":\"Coop_Temp\",\"Values\":{{\"T1_C\":\"{0:.2f}\",\"T1_F\":\"{3:.2f}\"}}'.format (the_tempC[0], the_tempF[0]))
        publish_message("Coop_Sensors", data1)
        return

def take_picture():
    coop_cam1.capture('/var/www/html/coop_pic.jpg')
    print("took a pic!")
    publish_message("Coop_Picture", "'{\"Unit\":\"Coop\", \"Picture\":\"Updated\"}'")
    return

client.on_connect = on_connect
client.on_message = on_message
#this device is going to be "always on" and needs to
#be listening at all times to function so connect immediately
client.connect("192.168.68.115",1883,60)
client.loop_start()

while True:
    try:
        take_picture()
        Collect_Temp_Data()
        Light_Check()
        sleep(60)

    except KeyboardInterrupt:
        client.disconnect()
        client.loop_stop()
        GPIO.output(active_running_led, 0)
        GPIO.cleanup()
        sys.exit()

