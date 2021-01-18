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
i=60
current_flow_1 = 200
current_flow_2 = 185

# Generally 27 is the address;Find yours using: i2cdetect -y 1 
address = 0x27 
port = 1 # 0 on an older Raspberry Pi

# Initialise the LCD
lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap,
                  cols=cols, rows=rows)

lcd.clear()
lcd.home()
lcd.write_string('Flow on 1 here:')
lcd.crlf()
lcd.write_string('Flow on two here:')
lcd.crlf()
lcd.write_string('Next line test')

while i > 0:
    # Clear the LCD screen
    #lcd.clear()
    lcd.home()
    lcd.cursor_pos = (3,0)
    lcd.write_string('Next Update: {}'.format(i))
    i = i - 1
    sleep(1)
else:
    lcd.home()
    lcd.cursor_pos = (3,0)
    lcd.write_string('Test concludes')
    sleep(20)
    lcd.clear()
    lcd.close()

