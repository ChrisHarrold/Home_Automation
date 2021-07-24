from time import sleep
import RPi.GPIO as GPIO
import sys

lightPin = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(lightPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
    try :
        state = GPIO.input(lightPin)
        if (state == True) :
            print("It is not dark")
        else :
            print("DARK")
        sleep(10)
    except KeyboardInterrupt :
        GPIO.cleanup()
        sys.exit()
    