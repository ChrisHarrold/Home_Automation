#!/usr/bin/python3
import traceback
import RPi.GPIO as GPIO
import sys, datetime, os
import time
from RPLCD import i2c
from ds18b20 import DS18B20 #Temp sensor library import
import paho.mqtt.client as mqtt #import the mqtt client from the paho library

# RUNTIME INDICATOR
active_running_led = 5

# tag up for the first run (gets changed once into the loop)
# also add values for eventual debug mode and terminate control (will be toggle switches)
first_run = True

# Debug mode - if the debug toggle is activated, this will be set true later in the code
debug_pin = 25
dreport = False

# Maintenance Mode - while the witch is ON nothing happens - no reporting and no collecting
# This is meant to be switched to the "ON" state while servicing the filters, and then turning it off
# Restarts the script as though it was a first run and starts the loop again
maintenance_pin = 26
mreport = False

global interval
interval = 60 #Change this value to match how often you wish to take readings (in seconds)
reporting_loop_count = 10 # change this to how many intervals to report in to the hub (60 loops = ~1 hour and 10 mins give or take)
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
data3 = ""

#set up the log file
try :
    with open('/var/www/html/pond_logger.txt', "w") as f:
        timeStr = time.ctime()
        f.write("new log file started " + timeStr + "\n")
        f.close
        
except FileNotFoundError:
    # the file was not found so this is 100% the very first run
    # ever and we need to create the file.
    with open('/var/www/html/pond_logger.txt', "w+") as f:
        timeStr = time.ctime()
        f.write("new log file started " + timeStr + "\n")
        f.close

def log_stash(raising_entity, the_error):
    with open('/var/www/html/pond_logger.txt', "a") as f:
        timeStr = time.ctime()
        f.write(raising_entity + "  :  " + the_error +"  :  " + timeStr + "\n")
        f.close

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

# Initialize callbacks for flow metering - these run all the time regardless of what else is happening
def Flow_meter1(channel):
   global count1
   count1 = count1 + 1

def Flow_meter2(channel):
   global count2
   count2 = count2 + 1

# these two add the listener threads to th GPIO for the flow meter - they will count the pulses in the background
# while the program runs, and then will update the counter(s) for readout on the interval
GPIO.add_event_detect(FLOW_SENSOR1, GPIO.FALLING, callback=Flow_meter1)
GPIO.add_event_detect(FLOW_SENSOR2, GPIO.FALLING, callback=Flow_meter2)

# Initialize callbacks for debug and maintenance mode
def debug_mode_on(channel):
    
    # triggering the debug mode will override all other operations and force the device into debug
    # this will update the hub every 10 seconds
    log_stash("Debug Pin ", "Debug mode activated ")
    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string('--- Debug Mode ---')
    lcd.cursor_pos = (2,0)
    lcd.write_string('--- Switch ON ---')
    lcd.cursor_pos = (3,0)
    lcd.write_string('--- I = 10 ---')
    
    while GPIO.input(debug_pin) :
        time.sleep(10)
        filter_level_check()
        Collect_Flow_Data()
        Collect_Temp_Data()

def debug_mode_off(channel):
    log_stash("Debug Pin ", "Debug mode deactivated ")
    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string(' Debug Mode ')
    lcd.cursor_pos = (2,0)
    lcd.write_string('-- Switch OFF --')
    lcd.cursor_pos = (3,0)
    lcd.write_string('Next Update:')

def Check_Maintenance() :
    state = GPIO.input(maintenance_pin)
    mdata = ""
    maintenance_interval = 0
    if (state == True) :
        print("Maintenance!")
        lcd.clear()
        lcd.cursor_pos = (0,0)
        lcd.write_string(' Maintenance Mode ')
        lcd.cursor_pos = (2,0)
        lcd.write_string('-- Switch ON --')
        log_stash("Maintenance Mode ", "Maintenance mode activated ")
        mdata = ('{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Maintenance\",\"Values\":\"Cleaning in Progress!"}')
        publish_message("Pond", mdata)
        while state :
            lcd.cursor_pos = (3,0)
            lcd.write_string('{} minutes elapsed'.format(maintenance_interval))
            maintenance_interval = maintenance_interval + 1
            time.sleep(60)
            state = GPIO.input(maintenance_pin)
            print("In the loop " + str(state))
            print("Still In maintenance mode")
            if state == False :
                break

        mdata = ('{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Maintenance\",\"Values\":\"Filter Cleaning Complete"}')
        state = False
        log_stash("Maintenance Pin ", "Maintenance mode deactivated ")
        publish_message("Pond", mdata)
    return

# Initialize temp sensor
# this uses 1-wire and is connected to GPIO4
temp_sensor = DS18B20()

# initialize MQTT for sending to the home hub and specify the variables for holding messages
# this will stay connected indefinitely to allow simple message publishing
broker_address = "192.168.68.115" 
client = mqtt.Client("Filter_Monitor") #create new instance
client.connect("192.168.68.115",1883,60)
log_stash("MQTT Connection Success! ", "MQTT connected ")
client.loop_start()

def filter_level_check():
    # Filter level check - the the hall switch has been triggered, the filter is close to needing cleaned
    # this will show up as a "true" in the Node Red flow on the other end
    if (GPIO.input(FILTER_SENSOR) == False) :
        filter_full = True
        GPIO.output(filter_alert_LED, 1)
        log_stash("Filter level ", "Float level confirmed high ")
    else :
        GPIO.output(filter_alert_LED, 0)
        filter_full = False
        log_stash("Filter level ", "Float level confirmed low ")
    the_message = ('{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Level\",\"Values\":{{\"Trigger\":\"{0}\"}}}}'.format (filter_full))
    log_stash("Filter Level Data Collected ", "Sending to publisher ")
    publish_message("Pond", the_message)
    
def Collect_Flow_Data() :
    # Get current LPM from flow meters:
        flow1 = (count1/7.5)
        flow2 = (count2/7.5)
        lcd.cursor_pos = (0,0)
        lcd.write_string('Flow 1 {0:.2f} LPM'.format (flow1))
        lcd.cursor_pos = (1,0)
        lcd.write_string('Flow 2 {0:.2f} LPM'.format (flow2))
        data0 = '{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Flow\",\"Values\":{{\"Flow1\":\"{0:.2f}\",\"Flow2\":\"{1:.2f}\"}}}}'.format (flow1, flow2)
        log_stash("Flow Data Collected ", "Sending to publisher ")
        publish_message("Pond", data0)
              
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
            try :
                temp_temp_temp = (temp_sensor.tempC(i))
            except IndexError :
                log_stash("Themal probe failure! ", "Temp sensor " + i + " failed to read correctly. ")
                temp_temp_temp = 100

            the_tempC.append(temp_temp_temp)
            the_tempF.append((temp_temp_temp * 1.8) + 32)
            i += 1
        lcd.cursor_pos = (2,0)
        lcd.write_string('{0:.1f}/{1:.1f}/{2:.1f} '.format (the_tempC[0], the_tempC[1], the_tempC[2]))
        data1 = ('{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Temp\",\"Values\":{{\"T1_C\":\"{0:.2f}\",\"T2_C\":\"{1:.2f}\",\"T3_C\":\"{2:.2f}\",\"T1_F\":\"{3:.2f}\",\"T2_F\":\"{4:.2f}\",\"T3_F\":\"{5:.2f}\"}}}}'.format (the_tempC[0], the_tempC[1], the_tempC[2],the_tempF[0], the_tempF[1], the_tempF[2]))
        log_stash("Temp Data Collected ", "Sending to publisher ")
        publish_message("Pond", data1)

def publish_message(the_topic, the_message):
    try:
        client.publish(the_topic, the_message)
        log_stash("I published a message ", " it was: " + the_message + " ")
    except Exception:
        traceback.print_exc()("I published a message ", " it was: " + the_message + " ")

    
# Here is the actual program:
while True:
    try:
        if first_run:
            # when the script is first run - either from the command line or via cron, it will
            # update the hub.
            interval = 0
            current_loop_count = reporting_loop_count
            first_run = False
            log_stash("First Run Confirmation", "The monitor has started its first run")

        if interval > 0:
                      
            # it will check the filter sensor on every loop to confirm if it needs to light the light on the panel 
            Check_Maintenance()
            lcd.home()
            lcd.cursor_pos = (3,17)
            lcd.write_string('{} '.format(interval))
            interval = interval - 1
            time.sleep(1)
        
        else :
            log_stash("One minute elapsed ", "Data collection loop triggered ")
            publish_message("Control","Filter Updated")  
            # Interval reset
            interval = 60
            # This is the data hub report part of the script
            if current_loop_count == reporting_loop_count :
                log_stash("Data Reporting loop triggered ", "Data WILL BE reported ")
                lcd.clear()
                Collect_Flow_Data()
                Collect_Temp_Data()
                filter_level_check()
                current_loop_count = 0   
            
            # Reset, clear all the data strings, and restart the regular loop
            current_loop_count = current_loop_count + 1
            lcd.cursor_pos = (3,0)
            lcd.write_string('Next Update:')
            lcd.cursor_pos = (3,17)
            lcd.write_string('{} '.format(interval))
            count1 = 0
            count2 = 0
            log_stash("LCD Updated ", "Data NOT reported ")

    except KeyboardInterrupt:
        log_stash("Keyboard interrupt", "Program break received. terminating program.")
        lcd.clear()
        lcd.home()
        lcd.write_string('Keyboard interrupt')
        lcd.cursor_pos = (2,0)
        lcd.write_string('Program halting')
        time.sleep(20)
        lcd.clear()
        lcd.close()
        log_stash("Program halted", "Program halted by keyboard break.")
        GPIO.output(active_running_led, 0)
        GPIO.cleanup()
        sys.exit()