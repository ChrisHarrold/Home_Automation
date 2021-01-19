import subprocess
result = subprocess.run(['ls', '/sys/devices/w1_bus_master1', '-d', '28*'], stdout=subprocess.PIPE).stdout.decode('utf-8')
print (result)  