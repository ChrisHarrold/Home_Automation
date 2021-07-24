from time import sleep
import RPi.GPIO as GPIO
import sys

lightPin = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(lightPin, GPIO.IN)

while True:
    try :
        state = GPIO.input(lightPin)
        if (state is False) :
            print("It is not dark")
        else :
            print("DARK")
        sleep(10)
    except KeyboardInterrupt :
        GPIO.cleanup()
        sys.exit()
    