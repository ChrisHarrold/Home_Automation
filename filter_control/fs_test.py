import subprocess
result = subprocess.run(['ls', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')
print (result)