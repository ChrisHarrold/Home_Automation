# Import LCD library
from RPLCD import i2c

# Import sleep library
from time import sleep
import datetime

# constants to initialise the LCD
lcdmode = 'i2c'
cols = 20
rows = 4
charmap = 'A00'
i2c_expander = 'PCF8574'
i=1
current_flow_1 = 200
current_flow_2 = 185

# Generally 27 is the address;Find yours using: i2cdetect -y 1 
address = 0x27 
port = 1 # 0 on an older Raspberry Pi

# Initialise the LCD
lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap,
                  cols=cols, rows=rows)

def write_to_lcd_display():
    # Write a string on first line and move to next line
    lcd.write_string('Tank 1 flow is '+ str(current_flow_1) + ' LPM')
    lcd.crlf()
    lcd.crlf()
    lcd.write_string('Tank 12flow is '+ str(current_flow_2) + ' LPM')
    lcd.crlf()
    now = datetime.datetime.now()
    lcd.write_string('Last updated: ' + now.strftime("%H:%M:%S"))
    sleep(10)

while i < 100:
    # Clear the LCD screen
    lcd.clear()
    sleep(5)
    write_to_lcd_display()

lcd.clear()
lcd.write_string('Testing Complete')
lcd.crlf()
lcd.write_string('This Will remain on screen')
lcd.crlf()
lcd.write_string('I hope?')
lcd.crlf()
lcd.write_string('I wonder what happens...')

sleep(30)
