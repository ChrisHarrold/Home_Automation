from time import sleep
import RPi.GPIO as GPIO
import sys

lightPin = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(lightPin, GPIO.IN)

while True:
    try :
        if (lightPin == GPIO.HIGH) :
            print("It is not dark")
        else :
            print("DARK")
        sleep(10)
    except KeyboardInterrupt :
        GPIO.cleanup()
        sys.exit()
    