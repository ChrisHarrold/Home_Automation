#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <time.h>
#include <string>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Set RTC Memory Values and info for deep-sleep counter
// Deep sleep taps out at 71 minutes, so for 4 hours you need to sleep
// 1 hour, looped 4 times
#define RTCMEMORYSTART 65
#define MAXHOUR 4 // number of hours to deep sleep for
typedef struct {
  int count;
} rtcStore;

rtcStore rtcMem;

// Here are all the PIN defs
#define ONE_WIRE_BUS D1
#define DHTPIN D2
int override_pin = D5;
const int batt_pin = A0;
int trigPin = D6;
int echoPin = D7;

// Setup a oneWire instance to communicate with any OneWire device
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

//Setup DHT 22
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// other variables
int sensor_count = 0;
float tempC;
float tempF;
char data1[50];
char data0[50];
int placeholder_value;
bool debug_mode = false;
int battery_raw = 0;
int battery_clean = 0;
float duration, distance;

// declare our Wifi and MQTT connections and other constant settings for the network
char* ssid     = "International_House_of_Corgi_24";            // The SSID (name) of the Wi-Fi network you want to connect to
char* password = "ElwoodIsBigAndFat";                          // The password of the Wi-Fi network
char* mqtt_server = "192.168.2.41";                             // The target mqtt server
String clientId = "P_Filters";
int lcount = 0;

// declare our Wifi and MQTT connections
WiFiClient espClient;
PubSubClient client(espClient);

void setup(void)
{
  Serial.begin(9600);
  Serial.println("Starting up");
  // First thing to do is check the RTC memory and increment if we have not hit
  // our full sleep interval - this will prevent all the WIFI stuff from running
  // and adding battery drain when it isn't time to sample. I will remove the 
  // serial outputs, post testing to save a couple more mA as well

  // CHeck the overide pin to see if we are in programming/debug or runtime mode (DIP 2 connected to D3)
  
  pinMode(override_pin, INPUT_PULLUP);
  if (digitalRead(override_pin) == HIGH) {
    debug_mode = true;
    Serial.println("Changed Mode");
  }
  
  if (debug_mode == false) {
    Serial.println("Reading RTC Value");
    readFromRTCMemory();
    Serial.println("Updating RTC Value");
    writeToRTCMemory();

    Serial.println("Checking sleep status");
    if (rtcMem.count != 1) {
      Serial.println("Going back to sleep for an hour - will try again");
      ESP.deepSleep(3.6e+9);
    }
  }
  // If the RTC mem check passes, the program will sample the temps
  pinMode(trigPin, OUTPUT);
  sensors.begin();	// Start up the onewire sensors
  dht.begin();      // start up the DHT22

  // Define the MQTT Server connection settings and then launch the MQTT Connection
  client.setServer(mqtt_server, 1883);

  //Connect to the wireless network
  setup_wifi();
  
  // locate devices on the bus
  Serial.print("Locating devices...");
  Serial.print("Found ");
  sensor_count = sensors.getDeviceCount();
  Serial.print(sensor_count, DEC);
  Serial.println(" devices.");
  Serial.println("");
}

void loop(void)
{ 
  //reconnect mqtt at loop start  
    if (!client.connected()) {
      reconnectMQ();
  }

  one_wire_read();
  dht_read();
  check_filter_leve();
  getBatteryLevel();


  //Serial.println("And Now We Wait");
  //Serial.println("");
  client.publish("control", "{\"Unit\":\"Filters\", \"Power\":\"Preparing to deep sleep\"}"); //the "control" topic is just for notifications - change to fit your needs
  delay(10000);
  
  // now we restart the sleep cycle after taking all samples
  // nothing runs after this
  if (debug_mode == false) {
    Serial.println("Going into deep sleep");
    ESP.deepSleep(3.6e+9);
    //ESP.deepSleep(30000);
  } else {
    Serial.println("Just resting for 30 seconds");
    delay(30000);
    ESP.restart();
  }
  
}

void readFromRTCMemory() {
  system_rtc_mem_read(RTCMEMORYSTART, &rtcMem, sizeof(rtcMem));

  Serial.print("count = ");
  Serial.println(rtcMem.count);
  yield();
}

void dht_read() {
  //DHT22 read and collect variables - float is a numeric type with better precision than int
  float humidity = dht.readHumidity();
  // Read temperature as Celsius (the default - can be change to Farenheit if desired)
  float temperature = dht.readTemperature();
  // Check if any reads failed and if so alert to the console, 
  // and set values to 0 so the process can continue - DHT11 sensors are notoriously flaky
  if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Failed to read from DHT sensor! Values set to 0!");
      temperature = 0;
      humidity = 0;
  //actually got a clean reading so go down the happy path and format the reading for the MQTT message    
  } else {
      Serial.println(" DHT11 Readings: ");
      Serial.print("Humidity: "); Serial.print(humidity); Serial.print(" %\t"); 
      Serial.print("Temperature: "); Serial.print(temperature); 
      Serial.println(" *C ");
  }
  //Serial.println("Constructing the DHT11 payload:");
  placeholder_value=sprintf(data0, "{\"Unit\":\"Filters\",\"Sensor\":\"DHT-11\", \"Values\": {\"C_Temp\":\"%.2f\", \"Humidity\":\"%.2f\"}}", temperature, humidity);
  //Serial.println("Publishing the DHT11 message");
  while (!client.publish("Pond", data0)) {
    Serial.print(".");
  }
}

void one_wire_read() {

  // Send command to all the sensors for temperature conversion
  sensors.requestTemperatures(); 
  
  // Display temperature from each sensor
  for (int devs = 0;  devs < sensor_count;  devs++)
  {
    Serial.print("Sensor ");
    Serial.print(devs+1);
    Serial.print(" : ");
    tempC = sensors.getTempCByIndex(devs);
    Serial.print(tempC);
    Serial.print((char)176);//shows degrees character
    Serial.print("C  |  ");
    tempF=(DallasTemperature::toFahrenheit(tempC));
    Serial.print(tempF);
    Serial.print((char)176);//shows degrees character
    Serial.println("F");
    
    if (devs < sensor_count) {
      //Serial.println("Constructing the payload:");
      placeholder_value=sprintf(data0, "{\"Unit\":\"Filters\",\"Sensor\":\"%d\", \"Values\": {\"C_Temp\":\"%.2f\", \"F_temp\":\"%.2f\"}}", devs, tempC, tempF);
      //Serial.println("Publishing message");
      while (!client.publish("Pond", data0)) {
        Serial.print(".");
      }
      // this is going to look really weird to you. Trust me, it works. Why? Probably because the MQTT library is FULL of weird
      // conflicting varible things and has a nasty tendency to break stuff like this. Just leave this here, it works.
      sensor_count = sensors.getDeviceCount();
    }

  }

}

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


void writeToRTCMemory() {
  if (rtcMem.count == MAXHOUR) {
    rtcMem.count = 1;
  } else {
    if (rtcMem.count < 1) {
      rtcMem.count = 1;
    }
    if (rtcMem.count > 4) {
      rtcMem.count = 1;
    }
    rtcMem.count++;
  }

  system_rtc_mem_write(RTCMEMORYSTART, &rtcMem, 4);

  Serial.print("Current loop count = ");
  Serial.println(rtcMem.count);
  yield();
}

void getBatteryLevel() {
  battery_raw = analogRead(batt_pin);
  Serial.print("battery raw reading:  ");
  Serial.println (battery_raw);
  battery_clean = map(battery_raw, 0, 1024, 0, 100);
  Serial.println(battery_clean);
  placeholder_value=sprintf(data0, "{\"Battery\":\"%i\"}", battery_clean);
  while (!client.publish("Pond", data0)) {
    Serial.print(".");
  }

}
void check_filter_leve() {
    digitalWrite(echoPin, LOW);   // set the echo pin LOW
    digitalWrite(trigPin, LOW);   // set the trigger pin LOW
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);  // set the trigger pin HIGH for 10μs
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    duration = pulseIn(echoPin, HIGH);  // measure the echo time (μs)
    distance = (duration/2.0)*0.0343;   // convert echo time to distance (cm)
    if(distance>400 || distance<2) Serial.println("Out of range");
    else
    {
        Serial.print("Distance: ");
        Serial.print(distance, 1); Serial.println(" cm");
    }
}
