# hall test
import RPi.GPIO as GPIO
from time import sleep

FILTER_SENSOR = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(FILTER_SENSOR, GPIO.IN, pull_up_down = GPIO.PUD_UP)

i = 100
while i > 0 :
    if GPIO.input(FILTER_SENSOR) :
        print('Detected a field!')
    else :
        print('No field')
    i = i - 1
    sleep(2)