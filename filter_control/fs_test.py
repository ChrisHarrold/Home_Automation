# Temp.py

from ds18b20 import DS18B20	
	
# test temperature sensors
x = DS18B20()
count=x.device_count()
i = 0
while i < count:
	print(x.tempC(i))
	i += 1