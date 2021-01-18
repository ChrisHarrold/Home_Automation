#!/usr/bin/env python

import RPi.GPIO as GPIO
import time, sys


FLOW_SENSOR1 = 18
FLOW_SENSOR2 = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR, GPIO.IN, pull_up_down = GPIO.PUD_UP)
global count1
global count2
count1 = 0
count2 = 0

def Flow_meter1(channel):
   global count1
   count1 = count1+1

def Flow_meter2(channel):
   global count2
   count2 = count2+1

GPIO.add_event_detect(FLOW_SENSOR1, GPIO.FALLING, callback=Flow_meter1)
GPIO.add_event_detect(FLOW_SENSOR2, GPIO.FALLING, callback=Flow_meter2)


while True:
    try:
        #print(GPIO.input(23))
	    #print (count)
        print('Flow Rate on tank 1 is: {0} \n'.format (count1))
        print('Flow Rate on tank 2 is: {0} \n'.format (count2))
        time.sleep(10)
	
    except KeyboardInterrupt:
        print('\ncaught keyboard interrupt!, bye')
        GPIO.cleanup()
        sys.exit()
