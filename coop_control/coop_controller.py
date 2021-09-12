import sys, datetime, os
from picamera import PiCamera
import paho.mqtt.client as mqtt
import time
import RPi.GPIO as GPIO
from ds18b20 import DS18B20

#setup variables and values
coop_cam1 = PiCamera()
client = mqtt.Client()

# I have taken to numbering pins in order so I can see what GPIO
# I am using at a glance. This keeps me from adding functions and duplicating
# a pin!
openPin1 = 5
closePin1 = 6
maintenance_pin = 12
door_toggle = 16
openPin2 = 22
vent_toggle =  25
lightPin = 24
active_running_led = 26
closePin2 = 27

i = 1
temp_sensor = DS18B20()
first_run = True
door_state = ""
vent_state = ""
# I realized the motor timming was in a bunch of places suddenly so I thought to put
# a single variable here to control the door motor runtime. That way once I get the
# right timing, it is a single change instead of 6 or 8
door_time = 3
vent_time = 3

#set all pins to startup modes:
GPIO.setmode(GPIO.BCM)
GPIO.setup(active_running_led, GPIO.OUT)
GPIO.setup(lightPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(maintenance_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(openPin1, GPIO.OUT)
GPIO.setup(closePin1, GPIO.OUT)
#GPIO.setup(openPin2, GPIO.OUT)
#GPIO.setup(closePin2, GPIO.OUT)
GPIO.setup(door_toggle, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(vent_toggle, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# get last known local door and vent values:
try :
    with open('/tmp/doorstate.txt', "r") as f:
        str_door_temp = f.read()
        if ('CLOSED' in str_door_temp) :
            door_state = 'CLOSED'
        elif ('OPEN' in str_door_temp) :
            door_state = 'OPEN'
        f.close
    time.sleep(1)
    with open('/tmp/doorstate.txt', "w+") as f:
        f.write(door_state)
        f.close
    
except FileNotFoundError:
    # the file was not found so this is 100% the very first run
    # ever and we need to create the file. The door must be OPEN
    # at installation for this to work and NodeRed needs to be in sync
    # this is unlikely to ever be needed, but I am the king of handling
    # corner cases so why stop now!?
    door_state = 'OPEN'
    with open('/tmp/doorstate.txt', "w+") as f:
        f.write(door_state)
        f.close

#set up the log file
try :
    with open('/var/www/html/coop_logger.txt', "w") as f:
        timeStr = time.ctime()
        f.write("new log file started " + timeStr + "\n")
        f.close
        
except FileNotFoundError:
    # the file was not found so this is 100% the very first run
    # ever and we need to create the file.
    with open('/var/www/html/coop_logger.txt', "w+") as f:
        timeStr = time.ctime()
        f.write("new log file started " + timeStr + "\n")
        f.close

def door_button_press_callback():
    # manual override button on the controller activates a close or open toggle
    # deppending on the current door state
    global door_state
    if (door_state == 'OPEN') :
        # turn on CLOSE pin
        GPIO.output(closePin1, 1)
        # time.sleep long enough to close door (some number of seconds - needs testing)
        time.sleep(door_time)
        # turn off close pin
        GPIO.output(closePin1, 0)
        #update to new door state
        door_state = 'CLOSED'
        with open('/tmp/doorstate.txt', "w") as f:
            f.write(door_state)
            f.close
        # publish new door state message to NodeRed
        client.publish("Door_Status", "CLOSED")
    
    else :
        # turn on OPEN pin
            GPIO.output(openPin1, 1)
            # time.sleep long enough to open door (some number of seconds)
            time.sleep(door_time)
            # turn off open pin
            GPIO.output(openPin1, 0)
            #update to new door state
            door_state = 'OPEN'
            with open('/tmp/doorstate.txt', "w") as f:
                f.write(door_state)
                f.close
            # publish new door state message to NodeRed
            client.publish("Door_Status", "OPEN")


def vent_button_press_callback():
    print("vent change!")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("Door_Actions")

def on_message(client, userdata, msg):
    payload = str(msg.payload.decode("utf-8"))
    global door_state
    if (payload == 'coop_close'):
        if (door_state == 'OPEN') :
            # turn on CLOSE pin
            GPIO.output(closePin1, 1)
            # time.sleep long enough to open door (some number of seconds - needs testing)
            time.sleep(door_time)
            # turn off close pin
            GPIO.output(closePin1, 0)
            #update the new state of the door:
            door_state = 'CLOSED'
            with open('/tmp/doorstate.txt', "w") as f:
                f.write(door_state)
                f.close
            # publish new door state message
            client.publish("Door_Status", "CLOSED")
        else :
            #state mismatch detected - raise alarm for manual check
            client.publish("Door_Status", "ALARM")

    if (payload == 'coop_open'):
        if (door_state == 'CLOSED') :
            # turn on OPEN pin
            GPIO.output(openPin1, 1)
            # time.sleep long enough to open door (some number of seconds)
            time.sleep(door_time)
            # turn off open pin
            GPIO.output(openPin1, 0)
            #update the new state of the door:
            door_state = 'OPEN'
            with open('/tmp/doorstate.txt', "w") as f:
                f.write(door_state)
                f.close
            # publish new door state message
            client.publish("Door_Status", "OPEN")
        else :
            #state mismatch detected - raise alarm for manual check
            #it should be REALLY hard to get to this state
            client.publish("Door_Status", "ALARM")

    if (payload == 'check_door') :
        # this allows a quick sanity check via node red to ensure the state on the controller matches the state
        # on the dashboard
        with open('/tmp/doorstate.txt', "r") as f:
            str_door_temp = f.read()
            if ('CLOSED' in str_door_temp) :
                door_data = ('{\"Unit\":\"Coop\",\"Sensor\":\"Door_State\",\"Values\":\"CLOSED"}')
                publish_message("Coop_Sensors", door_data)
            elif ('OPEN' in str_door_temp) :
                door_data = ('{\"Unit\":\"Coop\",\"Sensor\":\"Door_State\",\"Values\":\"OPEN"}')
                publish_message("Coop_Sensors", door_data)
            f.close

def publish_message(the_topic, the_message):
    client.publish(the_topic, the_message)

def log_stash(raising_entity, the_error):
    with open('/var/www/html/coop_logger.txt', "a") as f:
        timeStr = time.ctime()
        f.write(raising_entity + ":" + the_error +":" + timeStr + "\n")
        f.close

def Light_Check() :
    # checek the daylight sensor to see if we should close the coop
    # chickens mostly go in only when it is dark enough
    state = GPIO.input(lightPin)
    ldata = ""
    if (state == True) :
        ldata = ('{\"Unit\":\"Coop\",\"Sensor\":\"Coop_Light\",\"Values\":\"DO NOT CLOSE"}')
        publish_message("Coop_Sensors", ldata)
    else :
        ldata = ('{\"Unit\":\"Coop\",\"Sensor\":\"Coop_Light\",\"Values\":\"READY TO CLOSE"}')
        publish_message("Coop_Sensors", ldata)

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
        # but will only report out the first reading as is - can be extended to handle more
        i = 0
        #print(Temp_sensor_count)
        while i < Temp_sensor_count:
            try :
                temp_temp_temp = (temp_sensor.tempC(i))
            except IndexError :
                log_stash("Temp sensor error", "The temperature probe did not read correctly")
                temp_temp_temp = 100

            the_tempC.append(temp_temp_temp)
            the_tempF.append((temp_temp_temp * 1.8) + 32)
            i += 1
            #print('Sensor reading: {0} '.format (temp_temp_temp))
        #lcd.cursor_pos = (2,0)
        #lcd.write_string('{0:.1f}'.format (the_tempC[0]))
        if i > 0 :
            data1 = ('{{\"Unit\":\"Coop\",\"Sensor\":\"Coop_Temp\",\"Values\":{{\"T1_C\":\"{0:.2f}\",\"T1_F\":\"{1:.2f}\"}}}}'.format (the_tempC[0], the_tempF[0]))
        else :
            data1 = ('{\"Unit\":\"Coop\",\"Sensor\":\"Coop_Temp\",\"Values\":\"NO DATA\"}')
        
        publish_message("Coop_Sensors", data1)
        data1 = ""
        return

def Take_Picture():
    coop_cam1.capture('/var/www/html/coop_pic.jpg')
    log_stash("Camera", "Picture successsfully captured")
    publish_message("Coop_Picture", "'{\"Unit\":\"Coop\", \"Picture\":\"Updated\"}'")
    return

def Check_Maintenance() :
    state = GPIO.input(maintenance_pin)
    print("I checked!")
    mdata = ""
    if (state == True) :
        print("Maintenance!")
        log_stash("Maintenance Mode", "Maintenance mode activated")
        mdata = ('{\"Unit\":\"Coop\",\"Sensor\":\"Coop_Clean\",\"Values\":\"Coop Cleaning In Progress!"}')
        publish_message("Coop_Sensors", mdata)
        while state :
            time.sleep(10)
            print("Still In maintenance mode")
        mdata = ('{\"Unit\":\"Coop\",\"Sensor\":\"Coop_Clean\",\"Values\":\"Coop Cleaning Complete"}')
        log_stash("Maintenance Pin", "Maintenance mode deactivated")
        publish_message("Coop_Sensors", mdata)
    return


# Here is where the actual meat of the program starts and enters the "always on" loop
# this device is going to be "always on" and needs to
# be listening at all times to function so connect immediately
# this defines the interrupts and sets up the eternal listening loop
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.68.115",1883,60)
client.loop_start()
GPIO.add_event_detect(door_toggle, GPIO.RISING, callback=door_button_press_callback, bouncetime=300)
GPIO.add_event_detect(vent_toggle, GPIO.RISING, callback=vent_button_press_callback, bouncetime=300)

# turn on status LED after priming the system
GPIO.output(active_running_led, 1)

# run forever:
while True:
    try:
        if first_run :
            print("First Run")
            # on the first run the program does the key checks immediately
            # helps with debugging on the Node Red side
            Take_Picture()
            Collect_Temp_Data()
            Light_Check()
            first_run = False

        i = i+1 #simple incrementer for the 60 second time.sleep cycle

        if (i < 60):
            # this will check the maintenance switch
            # then carry on to time.sleep for one second.    
            # if the maintenance mode is activated it
            # will stay in maintenance mode until the switch
            # is changed back to normal op mode 
            Check_Maintenance()
        
        else :
            # if 60 time.sleeps have passed, carry out all checks
            # (photo - Temp - Light level - and Maintenance switch)
            Check_Maintenance()
            Take_Picture()
            Collect_Temp_Data()
            Light_Check()
            i = 1 #reset the incrementer to restart the loop
            print("Still Running!")
        
        time.sleep(1)

    except KeyboardInterrupt:
        client.disconnect()
        client.loop_stop()
        GPIO.output(active_running_led, 0)
        GPIO.cleanup()
        sys.exit()

