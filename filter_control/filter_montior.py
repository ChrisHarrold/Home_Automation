import RPi.GPIO as GPIO
import sys, datetime, os
from time import sleep
from RPLCD import i2c
from ds18b20 import DS18B20 #Temp sensor library import
import paho.mqtt.client as mqtt #import the mqtt client from the paho library

# tag up for the first run (gets changed once into the loop)
# also add values for eventual debug mode and terminate control (will be toggle switches)
first_run = True # set this flag to teell the system to actually collect data the first time the script
# runs on startup - otherwise it doesn't and waits 60 seconds

# Debug mode - if the debug toggle is activated, this will be set tru later in the code
debug = False
debug_pin = 13

# kill switch - activating the kill switch will cause the script to terminate - it must be restarted
# via a cron job or console commands
termination_pin = 26
terminate = False

global interval
interval = 60 #Change this value to match how often you wish to take readings (in seconds)
reporting_loop_count = 60 # change this to how many intervals to report in to the hub (60, 60s loops = 1 hour)
current_loop_count = 0

# just various conunters and value holders for doing work with later
global count1
global count2
count1 = 0
lastcount1 = 0
current_count1 = 0
count2 = 0
lastcount2 = 0
current_count2 = 0
flow1 = 0
flow2 = 0
filter_full = False

# values to initialise the LCD
# -------------------------------------------------------------------
lcdmode = 'i2c'
cols = 20
rows = 4
charmap = 'A00'
i2c_expander = 'PCF8574'
# Check the address for the Screen using: sudo i2cdetect -y 1 
# at the command prompt of the Pi to verify this is the correcet address.
address = 0x27 
port = 1
# Initialise the LCD
lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap, cols=cols, rows=rows)
lcd.clear()
lcd.home()

# values to intialize the flow meters and the various counters for tracking and measuring flow
# rate on a per-interval basis
#-------------------------------------------------------------------
FLOW_SENSOR1 = 18 #Pin for sensor 1
FLOW_SENSOR2 = 23 #Pin for sensor 2

# Initialize the filter cleaning monitor switch
# ------------------------------------------------------------------
FILTER_SENSOR = 24

# Initialize callbacks for flow metering - these run all the time regardless of what else is happening
def Flow_meter1(channel):
   global count1
   count1 = count1+1

def Flow_meter2(channel):
   global count2
   count2 = count2+1

# Initialize killswitch callback
def killswitch(channel):
    print('KILLSWITCH ENGAGED. Program sleeps for 20 seconds to notify via LCD.')
    lcd.clear()
    lcd.home()
    lcd.write_string('KILLSWITCH ACTIVE')
    lcd.cursor_pos = (2,0)
    lcd.write_string('TERMINATING')
    global interval
    interval = 20
    sleep(20)
    lcd.clear()
    lcd.close()
    GPIO.cleanup()
    sys.exit()

# Turn on the GPIO pins and configure for the various inputs, and interrupts
# --------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR1, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(FLOW_SENSOR2, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(debug_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(termination_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(FILTER_SENSOR, GPIO.IN, pull_up_down = GPIO.PUD_UP)

GPIO.add_event_detect(FLOW_SENSOR1, GPIO.FALLING, callback=Flow_meter1)
GPIO.add_event_detect(FLOW_SENSOR2, GPIO.FALLING, callback=Flow_meter2)
GPIO.add_event_detect(termination_pin, GPIO.FALLING, callback=killswitch)


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
            # when the script is first run - either from the command line or via cron, it will
            # update the hub. This is part of the "keepalive" heartbeat process as well as allowing
            # the device to get to debug mode faster if desired
            interval = 0
            current_loop_count = reporting_loop_count
            first_run = False

        while interval > 0:
            lcd.home()
            lcd.cursor_pos = (3,17)
            lcd.write_string('{} '.format(interval))
            interval = interval - 1
            sleep(1)
        else :
            # Interval reseet is here so that it can be overridden by the debug if the switch is triggered
            interval = 60
            
            if GPIO.input(debug_pin) :
                debug = True
            else :
                debug = False
            
            if debug :
                current_loop_count = reporting_loop_count
                print("Debug triggered by switch - report will be sent to hub on every interval until the switch is flipped again")
                lcd.clear()
                lcd.cursor_pos = (0,0)
                lcd.write_string('--- Debug Mode ---')
                lcd.cursor_pos = (2,0)
                lcd.write_string('--- Switch ON ---')
                lcd.cursor_pos = (3,0)
                lcd.write_string('--- I = 10 ---')
                interval = 10
                sleep(5)

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
            # the "library" that is included DOES perform these two steps BUT
            # only the FIRST TIME the sensor is initialized. In order to update the sensor
            # you need to run these two command again. I feel the way RPi does 1-Wire
            # is a major deficiency really. Having to shell to the OS is not ideal.
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            Temp_sensor_count = temp_sensor.device_count()
            # initialize a quick counter for the flow sensors - this will read as many as there are
            # but will only report out the first two readings to the LCD
            i = 0
            while i < Temp_sensor_count:
                temp_temp_temp = (temp_sensor.tempC(i))
                the_tempC.append(temp_temp_temp)
                the_tempF.append((temp_temp_temp * 1.8) + 32)
                i += 1
                print('Sensor reading: {0} '.format (temp_temp_temp))
            lcd.cursor_pos = (2,0)
            lcd.write_string('Temp C: {0:.2f}/{1:.2f} '.format (the_tempC[0], the_tempC[1]))

            # Filter level check - the the hall switch has been triggered, the filter is close to needing cleaned
            # this will show up as a "true" in the Node Red flow on the other end
            if GPIO.input(FILTER_SENSOR) :
                filter_full = False
            else :
                filter_full = True
                
            # This is the data hub report part of the script - if the debug switch is flipped "on"
            # the unit will send data to the hub on every cycle as defined in the loop interval value (default 60 seconds)
            # this is useful for debugging, but overkill for the dashboard and reporting. Recommend this is once per hour max.
            if current_loop_count == reporting_loop_count :

                # Send data to home hub for storage and display in central hub
                client.connect(broker_address) #connect to broker
                client.publish("control", '{\"Unit\":\"Filter\", \"MQTT\":\"Connected\"}')
                data0 = ('{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Flow\",\"Values\":{{\"Flow1\":\"{0:.2f}\",\"Flow2\":\"{1:.2f}\"}}}}'.format (flow1, flow2))
                data1 = ('{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Temp\",\"Values\":{{\"T1_C\":\"{0:.2f}\",\"T2_C\":\"{1:.2f}\",\"T1_F\":\"{2:.2f}\",\"T2_F\":\"{3:.2f}\"}}}}'.format (the_tempC[0], the_tempC[1],the_tempF[0], the_tempF[1]))
                data2 = ('{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Level\",\"Values\":{{\"Trigger\":\"{0}\"}}}}'.format (filter_full))
                client.publish("Pond", data0)
                client.publish("Pond", data1)
                client.publish("Pond", data2)
                sleep(1)
                client.publish("control", '{\"Unit\":\"Filter\", \"MQTT\":\"Disconnecting\"}')
                client.disconnect()
                current_loop_count = 0

            # Reset counters for next loop
            current_loop_count = current_loop_count + 1
            lcd.cursor_pos = (3,0)
            lcd.write_string('Next Update:')
            lastcount1 = count1
            lastcount2 = count2
            data0 = ""
            data1 = ""

    except KeyboardInterrupt:
        print('Keyboard Interrupt Detected - Breaking program. program sleeps for 20 seconds to notify via LCD.')
        lcd.clear()
        lcd.home()
        lcd.write_string('Keyboard interrupt')
        lcd.cursor_pos = (2,0)
        lcd.write_string('Program terminating')
        sleep(20)
        lcd.clear()
        lcd.close()
        GPIO.cleanup()
        sys.exit()
        

    
