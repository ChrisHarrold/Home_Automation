#include <time.h>

int IN1 = 5;
int IN2 = 4;

void setup() {
// set all the motor control pins to outputs
Serial.begin(9600);
pinMode(IN1, OUTPUT);
pinMode(IN2, OUTPUT);
digitalWrite(IN1, LOW);
digitalWrite(IN2, LOW);
}


void doorUp() {
  Serial.println("Door Up");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  delay(5000); // let motor run for 5 seconds
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  Serial.println("Done Door Up");
}

void doorDown() {
  Serial.println("Door Down");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  delay(5000); // let motor run for 5 seconds
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  Serial.println("Done Door Down");
}

void loop() {
  Serial.println("Starting Up");
  delay(5000);
  doorUp();   
  delay(5000);
  doorDown();   
}
