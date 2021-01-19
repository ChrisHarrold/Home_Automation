import subprocess
result = subprocess.run(['sudo', 'ls', '/sys/bus/w1/devices', '-d', '28*'], stdout=subprocess.PIPE).stdout.decode('utf-8')
print (result)  