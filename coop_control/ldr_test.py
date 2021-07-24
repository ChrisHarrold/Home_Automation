from time import sleep
import RPi.GPIO as GPIO

lightPin = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(lightPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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
    