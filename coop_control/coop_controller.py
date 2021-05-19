from picamera import PiCamera
import time

coop_cam1 = PiCamera()
coop_cam1.capture('/pictures/coop_pic.jpg')
print("took a pic!")