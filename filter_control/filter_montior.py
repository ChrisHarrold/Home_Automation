import RPi.GPIO as GPIO
import sys, datetime, os
from time import sleep
from RPLCD import i2c
from ds18b20 import DS18B20 #Temmp sensor library import
import paho.mqtt.client as mqtt #import the mqtt client from the paho library

# tag up for the first run (gets changed once into the loop)
# also add values for eventual debug mode and terminate control (will be toggle sitches)
first_run = True
debug = False
terminate = False

# values to initialise the LCD
# -------------------------------------------------------------------
lcdmode = 'i2c'
cols = 20
rows = 4
charmap = 'A00'
i2c_expander = 'PCF8574'
i=60
# Generally 27 is the address;Find yours using: i2cdetect -y 1 
address = 0x27 
port = 1 # 0 on an older Raspberry Pi
# Initialise the LCD
lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap,
                  cols=cols, rows=rows)
lcd.clear()
lcd.home()

# values to intialize the flow meters
#-------------------------------------------------------------------
FLOW_SENSOR1 = 18 #Pin for sensor 1
FLOW_SENSOR2 = 23 #Pin for sensor 2
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
interval = 60 #Change this value to match how often you wish to take readings (in seconds)
flow1 = 0
flow2 = 0

# Initialize callbacks for flow metering - these run all the time regardless of what else is happening
# ----------------------------------------------------------------
def Flow_meter1(channel):
   global count1
   count1 = count1+1

def Flow_meter2(channel):
   global count2
   count2 = count2+1

GPIO.add_event_detect(FLOW_SENSOR1, GPIO.FALLING, callback=Flow_meter1)
GPIO.add_event_detect(FLOW_SENSOR2, GPIO.FALLING, callback=Flow_meter2)


# Initialize temp sensor
# this uses 1-wir and is connected to GPIO4 (although i do not think this matters?)
temp_sensor = DS18B20()
the_tempC = []
the_tempF = []
temp_temp_temp = 0

# initialize MQTT for sending to the home hub
broker_address = "192.168.68.115" 
client = mqtt.Client("Filter_Monitor") #create new instance
data0 = ""
data1 = ""


# Here is the actual program:
while True:
    try:
        if first_run:
            interval = 0
            first_run = False

        while interval > 0:
            lcd.home()
            lcd.cursor_pos = (3,17)
            lcd.write_string('{} '.format(interval))
            interval = interval - 1
            sleep(1)
        else:
            lcd.clear()
            lcd.home()
            # Get current LPM from flow meters:
            current_count1 = count1 - lastcount1
            current_count2 = count2 - lastcount2
            flow1 = (current_count1/.55)
            flow2 = (current_count2/.55)
            lcd.cursor_pos = (0,0)
            lcd.write_string('Flow 1 {0:.2f} LPM'.format (flow1))
            lcd.cursor_pos = (1,0)
            lcd.write_string('Flow 2 {0:.2f} LPM'.format (flow2))
            
            # Get current out-flow water temperatures:
            # the "library" that is included DOES perform theese two steps BUT
            # only the FIRST TIME the sensor is initialized. In order to update the sensor
            # you need to run these two command again. I feel the way RPi does 1-Wire
            # is a major deficiency really. Having to shell to the OS is not ideal.
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            Temp_sensor_count = temp_sensor.device_count()
            i = 0
            while i < Temp_sensor_count:
                temp_temp_temp = (temp_sensor.tempC(i))
                the_tempC.append(temp_temp_temp)
                the_tempF.append((temp_temp_temp * 1.8) + 32)
                i += 1
            lcd.cursor_pos = (2,0)
            lcd.write_string('Temp C: {0:.2f}/{1:.2f} '.format (the_tempC[0], the_tempC[1]))

            # Send data to home hub for storage and display in central hub
            client.connect(broker_address) #connect to broker
            data0 = ('\"{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Flow\",\"Values\":{{\"Flow1\":\"{0:.2f}\",\"Flow2\":\"{1:.2f}\"}}}}\"'.format (flow1, flow2))
            data1 = ('\"{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Temp\",\"Values\":{{\"T1_C\":\"{0:.2f}\",\"T2_C\":\"{1:.2f}\",\"T1_F\":\"{2:.2f}\",\"T2_F\":\"{3:.2f}\"}}}}\"'.format (the_tempC[0], the_tempC[1],the_tempF[0], the_tempF[1]))
            client.publish("Pond", data0)
            client.publish("Pond", data1)
            sleep(1)
            client.disconnect()

            # Reset counters for next loop
            lcd.cursor_pos = (3,0)
            lcd.write_string('Next Update:')
            lastcount1 = count1
            lastcount2 = count2
            interval = 60
            data0 = ""
            data1 = ""

    except KeyboardInterrupt:
        print('Keyboard Interrupt Detected - Breaking program. program sleeps for 20 seconds to notify via LCD.')
        lcd.clear()
        lcd.home()
        lcd.write_string('Keyboard interrupt')
        lcd.cursor_pos = (2,0)
        lcd.write_string('Program terminated')
        sleep(20)
        lcd.clear()
        lcd.close()
        GPIO.cleanup()
        sys.exit()