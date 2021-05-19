from picamera import PiCamera
import time

coop_cam1 = PiCamera()
coop_cam1.capture('/var/www/html/coop_pic.jpg')
print("took a pic!")