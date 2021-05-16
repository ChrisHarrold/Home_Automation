/* Interface L298N With NodeMCU
 * By TheCircuit
 */

//int ENA = 3; //4;
int IN1 = 3; //0;
int IN2 = 2; //2;

void setup() {
// set all the motor control pins to outputs
//pinMode(ENA, OUTPUT);
pinMode(IN1, OUTPUT);
pinMode(IN2, OUTPUT);
}

// this function will run the motors in both directions at a fixed speed

void doorUp() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  delay(5000); // let motor run for 5 seconds
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

void doorDown() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  delay(5000); // let motor run for 5 seconds
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

void loop() {
  testOne();   
  delay(1000);   
}
