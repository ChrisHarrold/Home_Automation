from time import sleep
import RPi.GPIO as GPIO
active_running_led = 13

GPIO.setmode(GPIO.BCM)
GPIO.setup(active_running_led, GPIO.OUT, initial=1)

while True :
    try :
        sleep(10)
    except KeyboardInterrupt :
        GPIO.cleanup
  
