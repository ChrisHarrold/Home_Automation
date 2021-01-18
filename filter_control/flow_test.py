#!/usr/bin/env python

import RPi.GPIO as GPIO
import time, sys


FLOW_SENSOR = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR, GPIO.IN, pull_up_down = GPIO.PUD_UP)

global count
count = 0

def countPulse(channel):
   global count
   count = count+1
   print 'The current pulse count is {0} '.format (count)
   print '\n'

GPIO.add_event_detect(FLOW_SENSOR, GPIO.BOTH, callback=countPulse)


while True:
    try:
        #print(GPIO.input(23))
	    #print (count)

        time.sleep(10)
	
    except KeyboardInterrupt:
        print '\ncaught keyboard interrupt!, bye'
        GPIO.cleanup()
        sys.exit()
