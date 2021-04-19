#!/usr/bin/env python

import RPi.GPIO as GPIO
import time, sys


FLOW_SENSOR1 = 18
FLOW_SENSOR2 = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR1, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(FLOW_SENSOR2, GPIO.IN, pull_up_down = GPIO.PUD_UP)
global count1
global count2
count1 = 0
lastcount1 = 0
current_count1 = 0
count2 = 0
lastcount2 = 0
current_count2 = 0
interval = 60
flow1 = 0
flow2 = 0

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
        while interval > 0:
            print('Counting down to current reading: {} \n'.format(interval))
            time.sleep(1)
            interval = interval-1
        else:
            current_count1 = count1 - lastcount1
            current_count2 = count2 - lastcount2
            
            flow1 = (current_count1/.55)
            flow2 = (current_count2/.55)

            print('Flow Rate on tank 1 is: {0} Liters/Minute\n'.format (flow1))
            print('Flow Rate on tank 2 is: {0} Liters/Minute\n'.format (flow2))

            lastcount1 = count1
            lastcount2 = count2
            count1 = 0
            count2 = 0
            interval = 60

            
	
    except KeyboardInterrupt:
        print('\ncaught keyboard interrupt!, bye')
        GPIO.cleanup()
        sys.exit()
