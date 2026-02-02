/*
  Blink Built-in LED - Your First Arduino Program!
  
  This program blinks the LED that's already built into your Arduino UNO Q board.
  No external components needed - just upload and watch!
  
  The built-in LED is usually connected to pin 13.
*/

void setup() {
  // Initialize the built-in LED pin as an output
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Start serial communication so we can see what's happening
  Serial.begin(115200);
  Serial.println("=== BUILT-IN LED BLINK TEST ===");
  Serial.println("Watch the LED on your Arduino board!");
  Serial.println("It should blink ON and OFF every second.");
  Serial.println();
}

void loop() {
  // Turn the LED ON
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("LED ON");
  delay(1000);  // Wait for 1 second (1000 milliseconds)
  
  // Turn the LED OFF
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("LED OFF");
  delay(1000);  // Wait for 1 second
}