/*
  Smart Rural Triage Station - Main MCU Firmware
  ===============================================
  
  This is the main firmware for the Arduino UNO Q (STM32U585 Core).
  It handles real-time sensor reading, actuator control, display output, and communication with the Linux side.
  
  Hardware Components (Modulino QWIIC Ecosystem):
  - Modulino Knob (I2C) - Mode selection
  - Modulino Distance (I2C) - Placement validation (ToF)
  - Modulino Movement (I2C) - Motion detection (LSM6DSOX)
  - Modulino Thermo (I2C) - Temperature measurement
  - Modulino Buzzer (I2C) - Audio alerts
  - QLED/OLED Display 128x64 (I2C) - Visual Status
    * Conected via 4-Pin Header: GND->GND, VCC->3.3V, SDA->SDA, SCL->SCL
  - Servo Motors (D9, D10) - Visual feedback (PWM)
  - Audio Input (A1 / USB) - Microphone
  
  Communication Protocol:
  - JSON messages over Serial (115200 baud)
  
  Author: Smart Triage Team
  Version: 2.1.0 (Modulino + Display)
  License: MIT
*/

#include <ArduinoJson.h>
#include <Servo.h>
#include <Wire.h>
#include <Modulino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ============================================================================
// CONFIGURATION AND CONSTANTS
// ============================================================================

// Display Settings
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
#define SCREEN_ADDRESS 0x3C
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Pin definitions
const int STATUS_LED_PIN = 13;        // Built-in status LED
const int SERVO1_PIN = 9;             // Progress indicator servo
const int SERVO2_PIN = 10;            // Result display servo

// Timing constants
const unsigned long SENSOR_READ_INTERVAL = 100;    // 100ms between sensor reads
const unsigned long DISPLAY_UPDATE_INTERVAL = 250; // 250ms update rate
const unsigned long HEARTBEAT_INTERVAL = 5000;     // 5s heartbeat interval
const unsigned long SERIAL_TIMEOUT = 1000;         // 1s serial timeout

// Sensor thresholds
const float DISTANCE_MIN_MM = 20.0;     // Minimum valid distance (mm)
const float DISTANCE_MAX_MM = 80.0;     // Maximum valid distance (mm)

// System constants
const int JSON_BUFFER_SIZE = 1024;     // JSON document buffer size
const int SERIAL_BAUD_RATE = 115200;   // Serial communication speed

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

// Modulino Objects
ModulinoKnob knob;
ModulinoDistance distance;
ModulinoMovement movement;
ModulinoThermo thermo;
ModulinoBuzzer buzzer;
ModulinoPixels pixels;

// Servo objects
Servo progressServo;    // Servo 1
Servo resultServo;      // Servo 2

// Timing variables
unsigned long lastSensorRead = 0;
unsigned long lastDisplayUpdate = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastMovementTime = 0;
unsigned long systemStartTime = 0;

// Sensor data
struct SensorData {
  int knobRawValue;
  int knobMode;
  int distanceMm;
  bool distanceValid;
  bool distanceInRange;
  bool movementDetected;
  unsigned long movementStableDuration;
  float temperatureCelsius;
  bool temperatureValid;
};

SensorData currentSensorData;

// System state
enum SystemState {
  STATE_INITIALIZING,
  STATE_IDLE,
  STATE_EXAMINING,
  STATE_RESULTS,
  STATE_ERROR
};

SystemState currentState = STATE_INITIALIZING;

// UI State
String currentStatusMsg = "Initializing...";
String lastResultMsg = "";

// Communication
bool serialConnected = false;
unsigned long lastLinuxMessage = 0;

// ============================================================================
// SETUP FUNCTION
// ============================================================================

void setup() {
  // Initialize serial communication
  Serial.begin(SERIAL_BAUD_RATE);
  Serial.setTimeout(SERIAL_TIMEOUT);
  
  // Wait for serial connection
  unsigned long serialStartTime = millis();
  while (!Serial && (millis() - serialStartTime < 3000)) delay(10);
  
  Serial.println("MCU: Initializing Smart Rural Triage Station (v2.1)...");
  
  // Initialize I2C and Display
  Wire.begin();
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("SmartTriage Booting...");
  display.display();
  
  // Initialize Modulino
  if (!Modulino.begin()) Serial.println("MCU: Modulino Init Failed!");
  
  knob.begin();
  distance.begin();
  movement.begin();
  thermo.begin();
  buzzer.begin();
  pixels.begin();

  // Initialize Servos
  setupServos();
  pixels.set(0, 255, 165, 0); // Orange
  pixels.show();

  setupSensors();
  systemStartTime = millis();
  performStartupSequence();
  sendStartupMessage();
  
  currentState = STATE_IDLE;
  currentStatusMsg = "Ready";
  pixels.set(0, 0, 255, 0); // Green
  pixels.show();
  
  Serial.println("MCU: Initialization Complete");
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  unsigned long currentTime = millis();
  
  handleSerialCommunication();
  
  if (currentTime - lastSensorRead >= SENSOR_READ_INTERVAL) {
    readAllSensors();
    sendSensorData();
    lastSensorRead = currentTime;
  }

  if (currentTime - lastDisplayUpdate >= DISPLAY_UPDATE_INTERVAL) {
    updateDisplay();
    lastDisplayUpdate = currentTime;
  }
  
  if (currentTime - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = currentTime;
  }
  
  processSystemState();
  checkCommunicationTimeout();
  
  delay(10);
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void setupServos() {
  progressServo.attach(SERVO1_PIN);
  resultServo.attach(SERVO2_PIN);
  progressServo.write(90);
  resultServo.write(90);
  delay(500); 
}

void setupSensors() {
  currentSensorData.knobRawValue = 0;
  currentSensorData.knobMode = 0;
  currentSensorData.distanceMm = 0;
  currentSensorData.distanceValid = false;
  currentSensorData.distanceInRange = false;
  currentSensorData.movementDetected = false;
  currentSensorData.movementStableDuration = 0;
  currentSensorData.temperatureCelsius = 0.0;
  currentSensorData.temperatureValid = false;
}

void performStartupSequence() {
  display.clearDisplay();
  display.setCursor(0,20);
  display.setTextSize(2);
  display.println("Starting...");
  display.display();
  
  // Pixel Sequence
  for (int i = 0; i < 3; i++) {
    pixels.set(0, 0, 0, 255); pixels.show(); delay(150);
    pixels.set(0, 0, 0, 0);   pixels.show(); delay(150);
  }
  
  // Servo Wipe
  progressServo.write(0); delay(200);
  progressServo.write(180); delay(200);
  progressServo.write(90);
  
  buzzer.tone(1000, 200);
}

// ============================================================================
// SENSOR READING
// ============================================================================

void readAllSensors() {
  readKnobSensor();
  readDistanceSensorData();
  readMovementSensor();
  readTemperatureSensorData();
}

void readKnobSensor() {
  int val = knob.get();
  currentSensorData.knobRawValue = val;
  
  if (val < 33) {
    currentSensorData.knobMode = 0; // Heart
    if(currentState == STATE_IDLE) pixels.set(1, 255, 0, 0); // Red
  } else if (val < 66) {
    currentSensorData.knobMode = 1; // Lung
    if(currentState == STATE_IDLE) pixels.set(1, 0, 0, 255); // Blue
  } else {
    currentSensorData.knobMode = 2; // Calibration
    if(currentState == STATE_IDLE) pixels.set(1, 255, 255, 0); // Yellow
  }
  pixels.show();
}

void readDistanceSensorData() {
  int distMm = distance.get(); 
  if (distMm < 0) distMm = 0;
  
  currentSensorData.distanceMm = distMm;
  currentSensorData.distanceValid = (distMm > 0 && distMm < 2000);
  currentSensorData.distanceInRange = (distMm >= DISTANCE_MIN_MM && distMm <= DISTANCE_MAX_MM);
}

void readMovementSensor() {
  float x, y, z;
  if (movement.available()) {
    movement.readAccelerometer(x, y, z);
    float accelMag = sqrt(x*x + y*y + z*z);
    bool moving = (abs(accelMag - 1.0) > 0.15); // 0.15g threshold
    
    if (moving) {
      currentSensorData.movementDetected = true;
      lastMovementTime = millis();
      currentSensorData.movementStableDuration = 0;
    } else {
      if (millis() - lastMovementTime > 500) currentSensorData.movementDetected = false;
      currentSensorData.movementStableDuration = millis() - lastMovementTime;
    }
  }
}

void readTemperatureSensorData() {
  float tempC = thermo.getTemperature();
  currentSensorData.temperatureCelsius = tempC;
  currentSensorData.temperatureValid = (tempC > -40.0 && tempC < 125.0); 
}

// ============================================================================
// DISPLAY & UI
// ============================================================================

void updateDisplay() {
  display.clearDisplay();
  
  // Header Bar
  display.setTextSize(1);
  display.setTextColor(SSD1306_BLACK, SSD1306_WHITE); // Invert
  display.setCursor(0,0);
  String modeStr = (currentSensorData.knobMode == 0) ? " HEART MODE " : 
                   (currentSensorData.knobMode == 1) ? " LUNG MODE  " : " CALIBRATION";
  display.println(modeStr);
  
  // Main Content
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,12);
  
  if (currentState == STATE_IDLE) {
    display.print("Dist: "); 
    if(currentSensorData.distanceInRange) display.print("OK ");
    else display.print("ADJUST ");
    display.print(currentSensorData.distanceMm / 10.0, 1); display.println("cm");
    
    display.print("Temp: "); display.print(currentSensorData.temperatureCelsius, 1); display.println(" C");
    
    if(currentSensorData.movementDetected) display.println(">> MOVING <<");
    else display.println(">> STABLE <<");
    
  } else if (currentState == STATE_EXAMINING) {
    display.setTextSize(2);
    display.setCursor(10, 25);
    display.println("SCANNING");
    // Could draw progress bar here
    display.drawRect(10, 45, 108, 10, SSD1306_WHITE);
    // Pulse animation or simple fill based on time?
    // Using simple logic for now:
    int fill = (millis() / 250) % 20;
    display.fillRect(12, 47, fill * 5, 6, SSD1306_WHITE);
    
  } else if (currentState == STATE_RESULTS) {
    display.setTextSize(1);
    display.println("SCAN COMPLETE");
    display.println("----------------");
    display.setTextSize(2);
    display.println(lastResultMsg); // Should send Short Result via Serial? Or Linux controls text?
                                    // For now, assuming Linux sends command or we default
  }
  
  // Footer Status
  display.setTextSize(1);
  display.setCursor(0, 56);
  display.print("Status: ");
  display.println(currentStatusMsg.substring(0, 10)); // Truncate
  
  display.display();
}

// ============================================================================
// COMMUNICATION
// ============================================================================

void handleSerialCommunication() {
  if (Serial.available()) {
    String message = Serial.readStringUntil('\n');
    message.trim();
    if (message.length() > 0) {
      lastLinuxMessage = millis();
      serialConnected = true;
      processLinuxMessage(message);
    }
  }
}

void processLinuxMessage(String message) {
  StaticJsonDocument<JSON_BUFFER_SIZE> doc;
  DeserializationError error = deserializeJson(doc, message);
  if (error) return;
  
  String messageType = doc["message_type"] | "unknown";
  
  if (messageType == "control_command") handleControlCommand(doc);
  else if (messageType == "system_status") handleSystemStatus(doc);
  else if (messageType == "heartbeat") { lastLinuxMessage = millis(); serialConnected = true; }
}

void handleControlCommand(StaticJsonDocument<JSON_BUFFER_SIZE>& doc) {
  JsonObject commands = doc["commands"];
  
  if (commands.containsKey("servo1")) {
    int angle = commands["servo1"]["angle"] | 90;
    progressServo.write(angle);
  }
  if (commands.containsKey("servo2")) {
    int angle = commands["servo2"]["angle"] | 90;
    resultServo.write(angle);
  }
  if (commands.containsKey("buzzer")) {
    JsonObject buz = commands["buzzer"];
    String state = buz["state"] | "OFF";
    if (state == "ON") {
      int freq = buz["frequency"] | 1000;
      int dur = buz["duration"] | 200;
      buzzer.tone(freq, dur);
    }
  }
  if (commands.containsKey("display")) {
    String txt = commands["display"]["text"] | "";
    if (txt.length() > 0) {
      currentStatusMsg = txt;
      if (currentState == STATE_RESULTS) lastResultMsg = txt;
    }
  }
}

void handleSystemStatus(StaticJsonDocument<JSON_BUFFER_SIZE>& doc) {
  JsonObject status = doc["status"];
  String state = status["state"] | "UNKNOWN";
  
  if (state == "IDLE") { currentState = STATE_IDLE; currentStatusMsg = "Ready"; }
  else if (state == "EXAMINING") { currentState = STATE_EXAMINING; currentStatusMsg = "Scanning..."; }
  else if (state == "SHOWING_RESULTS") { currentState = STATE_RESULTS; currentStatusMsg = "Done"; }
  else if (state == "ERROR") { currentState = STATE_ERROR; currentStatusMsg = "Error"; }
}

// ============================================================================
// MESSAGE SENDING
// ============================================================================

void sendSensorData() {
  StaticJsonDocument<JSON_BUFFER_SIZE> doc;
  
  doc["timestamp"] = millis();
  doc["message_type"] = "sensor_data";
  JsonObject data = doc.createNestedObject("data");
  
  JsonObject k = data.createNestedObject("knob");
  k["raw_value"] = currentSensorData.knobRawValue;
  k["mode"] = currentSensorData.knobMode;
  k["voltage"] = currentSensorData.knobRawValue * (3.3 / 100.0);
  
  JsonObject d = data.createNestedObject("distance");
  d["value_mm"] = currentSensorData.distanceMm;
  d["value_cm"] = currentSensorData.distanceMm / 10.0;
  d["valid"] = currentSensorData.distanceValid;
  d["in_range"] = currentSensorData.distanceInRange;
  
  JsonObject m = data.createNestedObject("movement");
  m["detected"] = currentSensorData.movementDetected;
  m["stable_duration"] = currentSensorData.movementStableDuration;
  
  JsonObject t = data.createNestedObject("temperature");
  t["celsius"] = currentSensorData.temperatureCelsius;
  t["valid"] = currentSensorData.temperatureValid;
  
  serializeJson(doc, Serial);
  Serial.println();
}

void sendHeartbeat() {
  StaticJsonDocument<JSON_BUFFER_SIZE> doc;
  doc["timestamp"] = millis();
  doc["message_type"] = "heartbeat";
  doc["uptime"] = millis() - systemStartTime;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendStartupMessage() {
  StaticJsonDocument<JSON_BUFFER_SIZE> doc;
  doc["message_type"] = "startup";
  doc["version"] = "2.1.0";
  serializeJson(doc, Serial);
  Serial.println();
}

// ============================================================================
// UTILITY
// ============================================================================

void processSystemState() {
  switch (currentState) {
    case STATE_IDLE:
      if (currentSensorData.distanceInRange && !currentSensorData.movementDetected && currentSensorData.movementStableDuration > 2000) {
         // Ready (Linux determines switch)
      }
      break;
    case STATE_EXAMINING:
        pixels.set(0, 0, 0, 255); // Flashing Blue?
        if(currentSensorData.movementDetected) buzzer.tone(500, 100);
      break;
  }
}

void checkCommunicationTimeout() {
  if (serialConnected && (millis() - lastLinuxMessage > 30000)) {
    serialConnected = false;
    currentStatusMsg = "Comm Lost";
    pixels.set(0, 255, 0, 0); 
    pixels.show();
  }
}