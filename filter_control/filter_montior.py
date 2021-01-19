import RPi.GPIO as GPIO
import time, sys, datetime
from RPLCD import i2c

# values to initialise the LCD
lcdmode = 'i2c'
cols = 20
rows = 4
charmap = 'A00'
i2c_expander = 'PCF8574'
i=60

# values to intialize the flow meters
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