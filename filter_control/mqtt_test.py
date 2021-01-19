import paho.mqtt.client as mqtt #import the client1
broker_address="192.168.68.115" 
client = mqtt.Client("Filter_Monitor") #create new instance
client.connect(broker_address) #connect to broker
client.publish("TEST","TEST")#publish