# Import LCD library
from RPLCD import i2c

# Import sleep library
from time import sleep

# constants to initialise the LCD
lcdmode = 'i2c'
cols = 20
rows = 4
charmap = 'A00'
i2c_expander = 'PCF8574'
i=1

# Generally 27 is the address;Find yours using: i2cdetect -y 1 
address = 0x27 
port = 1 # 0 on an older Raspberry Pi

# Initialise the LCD
lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap,
                  cols=cols, rows=rows)

def write_to_lcd_display():
    # Write a string on first line and move to next line
    lcd.write_string('Testing LCD')
    lcd.crlf()
    lcd.write_string('This is Line 2')
    lcd.crlf()
    lcd.write_string('This is line 3')
    lcd.crlf()
    lcd.write_string('This is line 4')

while i < 100:
    sleep(20)
    # Clear the LCD screen
    lcd.clear()
    sleep(20)
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
