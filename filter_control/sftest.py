# simple function test
this_publish = 'This is the data string before'

def create_data_to_publish () :
    flow1 = 10
    flow2 = 20
    data0 = '{{\"Unit\":\"Filter\",\"Sensor\":\"Filter_Flow\",\"Values\":{{\"Flow1\":\"{0:.2f}\",\"Flow2\":\"{1:.2f}\"}}}}'.format (flow1, flow2)
    return data0

def publish_data (d1) :
    print(d1)
    return d1

this_publish = create_data_to_publish()
data1 = publish_data(this_publish)

print(data1)