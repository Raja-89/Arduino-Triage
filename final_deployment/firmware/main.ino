/* FINAL FIRMWARE: SERIAL BRIDGE EDITION */
#include <ArduinoJson.h>
#include <Servo.h>
#include <Wire.h>
#include <Modulino.h>           
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C 

const int PIN_MIC_ANALOG = A1;  
const int PIN_LED_STATUS = 6;
const int PIN_SERVO_PROGRESS = 9;
const int PIN_SERVO_RESULT = 10;

Servo progressServo;
Servo resultServo;
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

ModulinoKnob knob;
ModulinoMovement movement;
ModulinoThermo thermo;
ModulinoBuzzer buzzer;

unsigned long lastUpdate = 0;
unsigned long lastDisplaySwitch = 0;
int displayMode = 0; // 0=Temp, 1=Knob/Mode, 2=Mic, 3=Movement

void setup() {
  Serial.begin(115200);   // USB
  Serial1.begin(115200);  // Internal Bridge
  
  Wire.begin();
  Modulino.begin();
  knob.begin();
  movement.begin();
  thermo.begin();
  buzzer.begin();

  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {}
  display.clearDisplay();
  
  pinMode(PIN_MIC_ANALOG, INPUT);
  pinMode(PIN_LED_STATUS, OUTPUT);
  progressServo.attach(PIN_SERVO_PROGRESS);
  resultServo.attach(PIN_SERVO_RESULT);
  progressServo.write(0);  
  resultServo.write(90);
  
  buzzer.tone(1000, 200);
  delay(200);
}

void loop() {
  // Listen to BOTH ports
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    processCommand(input);
  }
  if (Serial1.available() > 0) {
    String input = Serial1.readStringUntil('\n');
    processCommand(input);
  }

  // Send Data
  if (millis() - lastUpdate > 100) {
    sendSensorData();
    lastUpdate = millis();
  }
  
  // Cycle Display
  if (millis() - lastDisplaySwitch > 2000) { 
      displayMode++;
      if (displayMode > 3) displayMode = 0;
      updateDisplay();
      lastDisplaySwitch = millis();
  }
}

void sendSensorData() {
  StaticJsonDocument<256> doc;
  
  doc["knob"] = knob.get();
  doc["temp"] = thermo.getTemperature();       
  
  float x = movement.getX();
  doc["movement"] = (abs(x) > 1.2) ? 1 : 0; 
  doc["mic"] = analogRead(PIN_MIC_ANALOG);

  // Send to BOTH ports
  serializeJson(doc, Serial);
  Serial.println();
  serializeJson(doc, Serial1);
  Serial1.println();
}

void updateDisplay() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0,0);
  display.print("STATUS: RUNNING");
  
  display.setTextSize(2);
  display.setCursor(0,25);
  display.setTextColor(SSD1306_WHITE);
  
  if (displayMode == 0) {
     display.print("Temp: "); display.print(thermo.getTemperature(), 1);
  } else if (displayMode == 1) {
     int k = knob.get();
     if(k < 300) display.print("HEART");
     else if(k < 700) display.print("LUNG");
     else display.print("CALIB");
  } else if (displayMode == 2) {
     display.print("Mic: "); display.print(analogRead(PIN_MIC_ANALOG));
  } else if (displayMode == 3) {
      float x = movement.getX();
      display.print("Mov: "); display.print(abs(x) > 1.2 ? "YES" : "NO");
  }
  
  display.display();
}

void processCommand(String input) {
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, input);
  if (error) return;

  if (doc.containsKey("progress")) progressServo.write(doc["progress"]);
  if (doc.containsKey("result")) resultServo.write(doc["result"]);
  
  if (doc.containsKey("buzzer")) {
    int freq = doc["buzzer"];
    if (freq > 0) buzzer.tone(freq, 100); 
  }
  
  if (doc.containsKey("led")) {
    digitalWrite(PIN_LED_STATUS, doc["led"].as<int>());
  }
}
