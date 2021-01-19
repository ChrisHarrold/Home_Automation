import subprocess
result = subprocess.run(['sudo', 'ls', '/sys/bus/w1/devices/28*', '-d',], stdout=subprocess.PIPE).stdout.decode('utf-8')
print (result)  