import RPi.GPIO as GPIO
import time

blink_me = 25

GPIO.setmode(GPIO.BCM)
GPIO.setup(blink_me, GPIO.OUT)
i=0

while i < 100 :
    GPIO.output(blink_me, GPIO.HIGH)
    print("LED on")
    time.sleep(5)
    print("LED off")
    GPIO.output(blink_me,GPIO.LOW)
    i=i+1


