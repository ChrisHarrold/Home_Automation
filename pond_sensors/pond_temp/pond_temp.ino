#include <OneWire.h>
#include <DallasTemperature.h>
#include <time.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Data wire is plugged into digital pin 2 on the Arduino
#define ONE_WIRE_BUS D1

// Setup a oneWire instance to communicate with any OneWire device
OneWire oneWire(ONE_WIRE_BUS);	

// Pass oneWire reference to DallasTemperature library
DallasTemperature sensors(&oneWire);

int deviceCount = 0;
float tempC;
float tempF;
char data1[50];
char data0[50];
int placeholder_value;


// declare our Wifi and MQTT connections and other constant settings for the network
char* ssid     = "International_House_of_Corgi_24";            // The SSID (name) of the Wi-Fi network you want to connect to
char* password = "ElwoodIsBigAndFat";                          // The password of the Wi-Fi network
char* mqtt_server = "192.168.2.41";                             // The target mqtt server
String clientId = "PT_1";
int lcount = 0;

// declare our Wifi and MQTT connections
WiFiClient espClient;
PubSubClient client(espClient);

// Reconnects to the MQTT message-bus if the connection died, or we're
// not otherwise connected.
//

void reconnectMQ() {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wifi not connected - configuring");
    setup_wifi();
  } else {
    Serial.println("Wifi Connected - connecting MQTT");
  }

  // Attempt to connect
  Serial.println("Attempting to connect to MQTT Server...");
  while (!client.connected()) {
    if (client.connect(clientId.c_str())) {
      Serial.println("connected to MQTT server");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }

  // Once connected, publish an announcement...
//  String payload = "{\"Unit\":\"PT_1\", \"MQTT\":\"Connected\"}";
//  payload.toCharArray(data1, (payload.length() + 1));
//  Serial.println("attempting to publish message");
  client.publish("control", "{\"Unit\":\"PT_1\", \"MQTT\":\"Connected\"}"); //the "control" topic is just for notifications - change to fit your needs
//  Serial.println("I actually got past that part");
}

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to ");
  Serial.print(ssid); Serial.println(" ...");

  WiFi.begin(ssid, password);             // Connect to the wifi network

  while (WiFi.status() != WL_CONNECTED) // Wait for the Wi-Fi to connect
    delay(1000);
    Serial.print('.');

  Serial.println('\n');
  Serial.println("Connected!");  
  Serial.print("IP address:\t");
  Serial.println(WiFi.localIP());         // Send the IP address of the ESP32 to the serial port
  
}

void setup(void)
{
  sensors.begin();	// Start up the library
  Serial.begin(9600);
  Serial.println("Starting up");
  
  // Define the MQTT Server connection settings and then launch the MQTT Connection
  client.setServer(mqtt_server, 1883);

  //Connect to the wireless network
  setup_wifi();
  
  // locate devices on the bus
  Serial.print("Locating devices...");
  Serial.print("Found ");
  deviceCount = sensors.getDeviceCount();
  Serial.print(deviceCount, DEC);
  Serial.println(" devices.");
  Serial.println("");
}

void loop(void)
{ 
  //reconnect mqtt at loop start  
    if (!client.connected()) {
      reconnectMQ();
  }

  // Send command to all the sensors for temperature conversion
  sensors.requestTemperatures(); 
  
  // Display temperature from each sensor
  for (int i = 0;  i < deviceCount;  i++)
  {
    Serial.print("Sensor ");
    Serial.print(i+1);
    Serial.print(" : ");
    tempC = sensors.getTempCByIndex(i);
    Serial.print(tempC);
    Serial.print((char)176);//shows degrees character
    Serial.print("C  |  ");
    tempF=(DallasTemperature::toFahrenheit(tempC));
    Serial.print(tempF);
    Serial.print((char)176);//shows degrees character
    Serial.println("F");

    Serial.println("Constructing the payload:");
    placeholder_value=sprintf(data0, "{\"Message\":\"\", \"Sensors\": {\"C_Temp\":\"%.2f\", \"F_temp\":\"%.2f\"}}", tempC, tempF);
    Serial.println("Publishing message");
    while (!client.publish("Pond", data0)) {
    Serial.print(".");
  }
  Serial.println("And Now We Wait");
  Serial.println("");
  delay(10000);
}
