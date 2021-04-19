#!/usr/bin/python3
import RPi.GPIO as GPIO
import sys, datetime, os
from time import sleep
from RPLCD import i2c
from ds18b20 import DS18B20 #Temp sensor library import
import paho.mqtt.client as mqtt #import the mqtt client from the paho library

# RUNTIME INDICATOR
active_running_led = 5

# tag up for the first run (gets changed once into the loop)
# also add values for eventual debug mode and terminate control (will be toggle switches)
first_run = True
# Debug mode - if the debug toggle is activated, this will be set true later in the code
global debug
debug = False
debug_pin = 25
dreport = False

# Maintenance Mode - while the witch is ON nothing happens - no reporting and no collecting
# This is meant to be switched to the "ON" state while servicing the filters, and then turning it off
# Restarts the script as though it was a first run and starts the loop again
maintenance_pin = 26
global maintenance_mode
maintenance_mode = False
mreport = False

global interval
interval = 60 #Change this value to match how often you wish to take readings (in seconds)
reporting_loop_count = 60 # change this to how many intervals to report in to the hub (60, 60s loops = 1 hour)
current_loop_count = 0

# just various counters and value holders for doing work with later
global count1
global count2
global lastcount1
global lastcount2
global current_count1
global current_count2
global flow1
global flow2
global maintenance_mode_active
global maintenance_interval
count1 = 0
lastcount1 = 0
current_count1 = 0
count2 = 0
lastcount2 = 0
current_count2 = 0
flow1 = 0
flow2 = 0
maintenance_mode_active = False
maintenance_interval = 0
data3 =""

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
global lcd
lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap, cols=cols, rows=rows)
lcd.clear()
lcd.home()

# values to intialize the flow meters
#-------------------------------------------------------------------
FLOW_SENSOR1 = 18 #Pin for sensor 1
FLOW_SENSOR2 = 23 #Pin for sensor 2

# Initialize the filter alert monitor
# ------------------------------------------------------------------
FILTER_SENSOR = 24
filter_full = False
filter_alert_LED = 6

# Initialize callbacks for flow metering - these run all the time regardless of what else is happening
def Flow_meter1(channel):
   global count1
   count1 = count1 + 1

def Flow_meter2(channel):
   global count2
   count2 = count2 + 1


# Turn on the GPIO pins and configure for the various inputs, and interrupts
# as well as activating the runtime LED
# --------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR1, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(FLOW_SENSOR2, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(debug_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(maintenance_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(FILTER_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(filter_alert_LED, GPIO.OUT)
GPIO.setup(active_running_led, GPIO.OUT, initial=1)



# these two add the listener threads to th GPIO for the flow meter - they will count the pulses in the background
# while the program runs, and then will update the counter(s) for readout on the interval
GPIO.add_event_detect(FLOW_SENSOR1, GPIO.FALLING, callback=Flow_meter1)
GPIO.add_event_detect(FLOW_SENSOR2, GPIO.FALLING, callback=Flow_meter2)

# Initialize temp sensor
# this uses 1-wire and is connected to GPIO4 (although i do not think this matters?)
temp_sensor = DS18B20()

# initialize MQTT for sending to the home hub and spcify the variables for holding messages
broker_address = "192.168.68.115" 
client = mqtt.Client("Filter_Monitor") #create new instance

def Collect_Flow_Data() :
    # Get current LPM from flow meters:
        current_count1 = count1 - lastcount1
        current_count2 = count2 - lastcount2
        flow1 = (current_count1/.55)
        flow2 = (current_count2/.55)
        lcd.cursor_pos = (0,0)
        lcd.write_string('Flow 1 {0:.2f} LPM'.format (flow1))
        lcd.cursor_pos = (1,0)
        lcd.write_string('Flow 2 {0:.2f} LPM'.format (flow2))
        data0 = '{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Flow\",\"Values\":{{\"Flow1\":\"{0:.2f}\",\"Flow2\":\"{1:.2f}\"}}}}'.format (flow1, flow2)
        return data0
              
def Collect_Temp_Data() :
        # Get current water temperatures:
        # the "library" that is included DOES perform these two steps BUT
        # only the FIRST TIME the sensor is initialized. In order to update the sensor
        # you need to run these two command again. I feel the way RPi does 1-Wire
        # is a major deficiency really. Having to shell to the OS is not ideal.
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        Temp_sensor_count = temp_sensor.device_count()

        the_tempC = []
        the_tempF = []
        temp_temp_temp = 0
        # initialize a quick counter for the temp sensors - this will read as many as there are
        # but will only report out the first 3 readings to the LCD as it runs out of room for more
        i = 0
        while i < Temp_sensor_count:
            temp_temp_temp = (temp_sensor.tempC(i))
            the_tempC.append(temp_temp_temp)
            the_tempF.append((temp_temp_temp * 1.8) + 32)
            i += 1
            #print('Sensor reading: {0} '.format (temp_temp_temp))
        lcd.cursor_pos = (2,0)
        lcd.write_string('{0:.1f}/{1:.1f}/{2:.1f} '.format (the_tempC[0], the_tempC[1], the_tempC[2]))
        data1 = ('{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Temp\",\"Values\":{{\"T1_C\":\"{0:.2f}\",\"T2_C\":\"{1:.2f}\",\"T3_C\":\"{2:.2f}\",\"T1_F\":\"{3:.2f}\",\"T2_F\":\"{4:.2f}\",\"T3_F\":\"{5:.2f}\"}}}}'.format (the_tempC[0], the_tempC[1], the_tempC[2],the_tempF[0], the_tempF[1], the_tempF[2]))
        return data1

def Publish_Data(fdata, tdata, mmdata):

    # Filter level check - the the hall switch has been triggered, the filter is close to needing cleaned
    # this will show up as a "true" in the Node Red flow on the other end
    if (GPIO.input(FILTER_SENSOR) == False) :
        filter_full = True
        GPIO.output(filter_alert_LED, 1)
    else :
        GPIO.output(filter_alert_LED, 0)
        filter_full = False
    data2 = ('{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Level\",\"Values\":{{\"Trigger\":\"{0}\"}}}}'.format (filter_full))
        
    client.connect(broker_address) #connect to broker
    client.publish("control", '{\"Unit\":\"Filter\", \"MQTT\":\"Connected\"}')  
    client.publish("Pond", fdata)
    client.publish("Pond", tdata)
    client.publish("Pond", data2)
    if maintenance_mode_active :
        client.publish("Pond", mmdata)
    client.publish("control", '{\"Unit\":\"Filter\", \"MQTT\":\"Disconnecting\"}')
    sleep(1)
    client.disconnect()
    print('Data Published')



# Here is the actual program:
while True:
    try:
        if first_run:
            # when the script is first run - either from the command line or via cron, it will
            # update the hub.
            interval = 0
            current_loop_count = reporting_loop_count
            first_run = False
            print('First Run Confirm')

        while interval > 0:
            
            # triggering the debug mode will override all other operations and force the device into debug
            # this will update the hub every 10 seconds
            if GPIO.input(debug_pin) :
                debug = True
                print("Debug enabled - data will be updated every 10 seconds")
                lcd.clear()
                lcd.cursor_pos = (0,0)
                lcd.write_string('--- Debug Mode ---')
                lcd.cursor_pos = (2,0)
                lcd.write_string('--- Switch ON ---')
                lcd.cursor_pos = (3,0)
                lcd.write_string('--- I = 10 ---')
                
                while GPIO.input(debug_pin) :
                    sleep(10)
                    if (GPIO.input(FILTER_SENSOR) == False) :
                        filter_full = True
                        GPIO.output(filter_alert_LED, 1)
                    else :
                        GPIO.output(filter_alert_LED, 0)
                        filter_full = False
                    flowdata = Collect_Flow_Data()
                    tempdata = Collect_Temp_Data()
                    Publish_Data(flowdata, tempdata, data3)
                    lastcount1 = count1
                    lastcount2 = count2
            
            else :
                if debug == True :
                    debug = False
                    dreport = True
                    print("Debug cancelled - resuming normal operation")
                    interval = 10
                    current_loop_count = reporting_loop_count
                    lcd.clear()
                    lcd.cursor_pos = (0,0)
                    lcd.write_string(' Debug Mode ')
                    lcd.cursor_pos = (2,0)
                    lcd.write_string('-- Switch OFF --')
                    lcd.cursor_pos = (3,0)
                    lcd.write_string('Next Update:')
            
            if GPIO.input(maintenance_pin) :
                # If maintenance mode has been activated, the unit will operate in this mode until the switch is flipped off again
                # No data is collected during the maintenance interval (Maintenance assumes the filter is being cleaned out)
                print("Switching to maintenance mode - no data collection will occur")
                while GPIO.input(maintenance_pin) :
                    maintenance_mode_active = True
                    lcd.clear()
                    lcd.cursor_pos = (0,0)
                    lcd.write_string(' Maintenance Mode ')
                    lcd.cursor_pos = (2,0)
                    lcd.write_string('-- Switch ON --')
                    lcd.cursor_pos = (3,0)
                    lcd.write_string('{} minutes elapsed'.format(maintenance_interval))
                    maintenance_interval = maintenance_interval + 1
                    interval = 60
                    sleep(5)
            else :
                # if maintenance mode WAS active (by switching on the switch), but is now "OFF" the program will update the LCD
                # and set the interval short and the reporting to "TRUE" This will give you
                # the ability to have a "last cleaned" timestamp on the dashboard as well.

                if maintenance_mode_active :
                    maintenance_mode_active = False
                    mreport = True
                    lcd.clear()
                    lcd.cursor_pos = (0,0)
                    lcd.write_string(' Maintenance Mode ')
                    lcd.cursor_pos = (2,0)
                    lcd.write_string('-- Switch OFF --')
                    lcd.cursor_pos = (3,0)
                    lcd.write_string('Next Update:')
                    interval = 5
                    current_loop_count = reporting_loop_count
            
            # If maintenance mode or debug mode are not activated, the loop simply continues the countdown and updates the LCD
            # it will check the filter sensor on every loop to confirm if it needs to light the light on the panel 
            if (GPIO.input(FILTER_SENSOR) == False) :
                filter_full = True
                GPIO.output(filter_alert_LED, 1)
            else :
                GPIO.output(filter_alert_LED, 0)
                filter_full = False
            lcd.clear()
            flowdata = Collect_Flow_Data()
            tempdata = Collect_Temp_Data()
            lcd.home()
            lcd.cursor_pos = (3,17)
            lcd.write_string('{} '.format(interval))
            interval = interval - 1
            sleep(1)
        
        else :
            # Interval reset
            interval = 60
            # This is the data hub report part of the script
            if current_loop_count == reporting_loop_count :
                print('Reporting Loop - Data will be sent')
                if mreport :
                    data3 = ('{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Maintenance\",\"Values\":{{\"Maintenance\":\"{0:.2f}\"}}}}'.format (maintenance_interval))
                    maintenance_interval = 0
                    lcd.clear()
                    flowdata = Collect_Flow_Data()
                    tempdata = Collect_Temp_Data()
                    Publish_Data(flowdata, tempdata, data3)
                    current_loop_count = 0
                    mreport = False
                elif dreport :
                    dreport = False
                    lcd.clear()
                    flowdata = Collect_Flow_Data()
                    tempdata = Collect_Temp_Data()
                    Publish_Data(flowdata, tempdata, data3)
                    current_loop_count = 0
                else :
                    lcd.clear()
                    flowdata = Collect_Flow_Data()
                    tempdata = Collect_Temp_Data()
                    Publish_Data(flowdata, tempdata, data3)
                    current_loop_count = 0

                
                
            # Reset, clear all the data strings, and restart the regular loop
            current_loop_count = current_loop_count + 1
            print(current_loop_count)
            lcd.cursor_pos = (3,0)
            lcd.write_string('Next Update:')
            lcd.cursor_pos = (3,17)
            lcd.write_string('{} '.format(interval))
            lastcount1 = count1
            lastcount2 = count2
            count1 = 0
            count2 = 0

    except KeyboardInterrupt:
        print('Keyboard Interrupt Detected - Breaking program. program sleeps for 20 seconds to notify via LCD.')
        lcd.clear()
        lcd.home()
        lcd.write_string('Keyboard interrupt')
        lcd.cursor_pos = (2,0)
        lcd.write_string('Program halting')
        sleep(20)
        lcd.clear()
        lcd.close()
        GPIO.output(active_running_led, 0)
        GPIO.cleanup()
        sys.exit()