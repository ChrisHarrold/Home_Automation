int trigPin = D1;            // HC-SR04 trigger pin
int echoPin = D2;            // HC-SR04 echo pin
float duration, distance;

void setup()
{
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT); // define trigger pin as output
  pinMode(echoPin, INPUT);
  digitalWrite(echoPin, LOW);   // set the echo pin LOW
}
void loop()
{
  
  digitalWrite(trigPin, LOW);   // set the trigger pin LOW
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);  // set the trigger pin HIGH for 10μs
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);  // measure the echo time (μs)
  distance = (duration/2.0)*0.0343;   // convert echo time to distance (cm)
  Serial.println(distance);
  if(distance>400 || distance<2) Serial.println("Out of range");
  else
  {
    Serial.print("Distance: ");
    Serial.print(distance, 1); Serial.println(" cm");
  }
  delay(10000);
}
