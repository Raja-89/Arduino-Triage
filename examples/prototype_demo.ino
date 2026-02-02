/*
 * SMART RURAL TRIAGE STATION - COMPLETE PROTOTYPE DEMO
 * 
 * This is a comprehensive display-only solution for video demonstration.
 * All functionality is hardcoded to simulate a working medical device.
 * 
 * Hardware Components:
 * - Arduino UNO Q with OLED Display (128x64)
 * - Modulino Knob (for navigation)
 * - Modulino Buzzer (for audio feedback)
 * - 2 Servo Motors (D9: Progress, D10: Results)
 * - 3 LEDs: Green (D2), Blue (D3), White (D4)
 * - Microphone on A1 (for visual feedback)
 * - Temperature sensor (Modulino Thermo)
 * - Movement sensor (Modulino Movement)
 * 
 * LED Connections:
 * - Green LED: Pin D2 (Normal status, system ready)
 * - Blue LED: Pin D3 (Processing, recording)
 * - White LED: Pin D4 (Alert, abnormal results)
 * 
 * Demo Flow:
 * 1. System startup with welcome sound
 * 2. Main menu navigation with knob
 * 3. Heart/Lung measurement simulation
 * 4. Progress bar with servo animation
 * 5. Results display with LED indicators
 * 6. Complete medical triage workflow
 */

#include <ArduinoJson.h>
#include <Servo.h>
#include <Wire.h>
#include <Modulino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- DISPLAY CONFIGURATION ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C

// --- PIN DEFINITIONS ---
const int PIN_MIC_ANALOG = A1;
const int PIN_LED_GREEN = 2;    // Normal/Ready status
const int PIN_LED_BLUE = 3;     // Processing/Recording
const int PIN_LED_WHITE = 4;    // Alert/Abnormal
const int PIN_SERVO_PROGRESS = 9;
const int PIN_SERVO_RESULT = 10;

// --- SYSTEM STATES ---
enum SystemState {
  STATE_STARTUP,
  STATE_MAIN_MENU,
  STATE_SELECT_MODE,
  STATE_POSITIONING,
  STATE_RECORDING,
  STATE_PROCESSING,
  STATE_RESULTS,
  STATE_FINAL_SUMMARY
};

SystemState currentState = STATE_STARTUP;

// --- MEASUREMENT MODES ---
enum MeasurementMode {
  MODE_HEART = 0,
  MODE_LUNG = 1,
  MODE_TEMPERATURE = 2
};

// --- GLOBAL VARIABLES ---
Servo progressServo;
Servo resultServo;
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
ModulinoKnob knob;
ModulinoMovement movement;
ModulinoThermo thermo;
ModulinoBuzzer buzzer;

int menuIndex = 0;
int lastMenuIndex = -1;
MeasurementMode selectedMode = MODE_HEART;
bool wasPressed = false;
unsigned long stateStartTime = 0;
unsigned long lastUpdate = 0;

// --- MEASUREMENT RESULTS ---
struct MeasurementResults {
  bool heartMeasured = false;
  bool lungMeasured = false;
  bool temperatureMeasured = false;
  String heartResult = "Normal";
  String lungResult = "Normal";
  float temperature = 36.5;
  String finalDiagnosis = "Normal";
  int riskLevel = 0; // 0=Normal, 1=Caution, 2=Alert
} results;

// --- DEMO CONTROL VARIABLES ---
bool simulateAbnormal = false; // Change this to true to show abnormal results
int progressValue = 0;
bool recordingComplete = false;

void setup() {
  Serial.begin(115200);
  Serial1.begin(115200);
  Wire.begin();
  
  // Initialize Modulino components
  Modulino.begin();
  knob.begin();
  movement.begin();
  thermo.begin();
  buzzer.begin();
  
  // Initialize display
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  
  // Initialize pins
  pinMode(PIN_MIC_ANALOG, INPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  pinMode(PIN_LED_WHITE, OUTPUT);
  
  // Initialize servos
  progressServo.attach(PIN_SERVO_PROGRESS);
  resultServo.attach(PIN_SERVO_RESULT);
  progressServo.write(0);
  resultServo.write(90); // Neutral position
  
  // Turn off all LEDs initially
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_BLUE, LOW);
  digitalWrite(PIN_LED_WHITE, LOW);
  
  // Startup sequence
  playStartupSequence();
  stateStartTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  
  // Read knob input
  int rawKnob = knob.get();
  int scaledKnob = abs(rawKnob) / 5;
  
  // Handle button press
  bool isPressed = knob.isPressed();
  handleButton(isPressed);
  
  // State machine
  switch (currentState) {
    case STATE_STARTUP:
      handleStartup(currentTime);
      break;
      
    case STATE_MAIN_MENU:
      handleMainMenu(scaledKnob);
      break;
      
    case STATE_SELECT_MODE:
      handleModeSelection(scaledKnob);
      break;
      
    case STATE_POSITIONING:
      handlePositioning(currentTime);
      break;
      
    case STATE_RECORDING:
      handleRecording(currentTime);
      break;
      
    case STATE_PROCESSING:
      handleProcessing(currentTime);
      break;
      
    case STATE_RESULTS:
      handleResults(currentTime);
      break;
      
    case STATE_FINAL_SUMMARY:
      handleFinalSummary();
      break;
  }
  
  // Send sensor data periodically
  if (currentTime - lastUpdate > 100) {
    sendSensorData();
    lastUpdate = currentTime;
  }
  
  delay(50); // Small delay for stability
}

void playStartupSequence() {
  // Visual startup
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10, 20);
  display.println("TRIAGE");
  display.setCursor(15, 40);
  display.println("STATION");
  display.display();
  
  // LED sequence
  digitalWrite(PIN_LED_GREEN, HIGH);
  buzzer.tone(800, 200);
  delay(300);
  
  digitalWrite(PIN_LED_BLUE, HIGH);
  buzzer.tone(1000, 200);
  delay(300);
  
  digitalWrite(PIN_LED_WHITE, HIGH);
  buzzer.tone(1200, 200);
  delay(300);
  
  // Turn off all LEDs
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_BLUE, LOW);
  digitalWrite(PIN_LED_WHITE, LOW);
  
  // Final startup tone
  buzzer.tone(1500, 500);
  delay(1000);
}

void handleStartup(unsigned long currentTime) {
  if (currentTime - stateStartTime > 3000) { // 3 second startup
    currentState = STATE_MAIN_MENU;
    digitalWrite(PIN_LED_GREEN, HIGH); // System ready
    buzzer.tone(1000, 100);
    stateStartTime = currentTime;
  }
}

void handleMainMenu(int scaledKnob) {
  menuIndex = scaledKnob % 4; // 4 menu options
  
  if (menuIndex != lastMenuIndex) {
    buzzer.tone(1500, 20); // Navigation sound
    lastMenuIndex = menuIndex;
  }
  
  displayMainMenu();
}

void handleModeSelection(int scaledKnob) {
  int modeSelect = scaledKnob % 3; // 3 modes: Heart, Lung, Temperature
  selectedMode = (MeasurementMode)modeSelect;
  
  if (modeSelect != lastMenuIndex) {
    buzzer.tone(1500, 20);
    lastMenuIndex = modeSelect;
  }
  
  displayModeSelection();
}

void handlePositioning(unsigned long currentTime) {
  // Simulate positioning validation
  static bool positionValid = false;
  static unsigned long positionStartTime = 0;
  
  if (positionStartTime == 0) {
    positionStartTime = currentTime;
  }
  
  // Simulate gradual positioning
  if (currentTime - positionStartTime > 2000) {
    positionValid = true;
    digitalWrite(PIN_LED_BLUE, HIGH); // Ready to record
  }
  
  displayPositioning(positionValid);
  
  // Auto-advance after positioning is valid
  if (positionValid && currentTime - positionStartTime > 4000) {
    currentState = STATE_RECORDING;
    stateStartTime = currentTime;
    progressValue = 0;
    recordingComplete = false;
    buzzer.tone(800, 300); // Recording start sound
  }
}

void handleRecording(unsigned long currentTime) {
  unsigned long recordingDuration = 8000; // 8 seconds
  unsigned long elapsed = currentTime - stateStartTime;
  
  // Update progress
  progressValue = map(elapsed, 0, recordingDuration, 0, 180);
  progressValue = constrain(progressValue, 0, 180);
  progressServo.write(progressValue);
  
  // Simulate microphone activity
  int micValue = analogRead(PIN_MIC_ANALOG);
  
  displayRecording(elapsed, recordingDuration, micValue);
  
  // Recording complete
  if (elapsed >= recordingDuration && !recordingComplete) {
    recordingComplete = true;
    currentState = STATE_PROCESSING;
    stateStartTime = currentTime;
    digitalWrite(PIN_LED_BLUE, LOW);
    digitalWrite(PIN_LED_WHITE, HIGH); // Processing indicator
    buzzer.tone(1200, 200); // Recording complete sound
  }
}

void handleProcessing(unsigned long currentTime) {
  unsigned long processingDuration = 3000; // 3 seconds
  unsigned long elapsed = currentTime - stateStartTime;
  
  displayProcessing(elapsed, processingDuration);
  
  // Simulate servo movement during processing
  int servoPos = 90 + sin(elapsed / 100.0) * 20; // Oscillate around center
  resultServo.write(servoPos);
  
  if (elapsed >= processingDuration) {
    // Generate results based on selected mode
    generateResults();
    currentState = STATE_RESULTS;
    stateStartTime = currentTime;
    
    // Set result servo position based on diagnosis
    if (results.riskLevel == 0) {
      resultServo.write(45); // Normal position
      digitalWrite(PIN_LED_WHITE, LOW);
      digitalWrite(PIN_LED_GREEN, HIGH);
    } else if (results.riskLevel == 1) {
      resultServo.write(90); // Caution position
      digitalWrite(PIN_LED_WHITE, LOW);
      digitalWrite(PIN_LED_BLUE, HIGH);
    } else {
      resultServo.write(135); // Alert position
      digitalWrite(PIN_LED_WHITE, HIGH);
      digitalWrite(PIN_LED_GREEN, LOW);
      buzzer.tone(2000, 1000); // Alert sound
    }
  }
}

void handleResults(unsigned long currentTime) {
  displayResults();
  
  // Auto-advance to final summary after 5 seconds
  if (currentTime - stateStartTime > 5000) {
    // Mark current measurement as complete
    switch (selectedMode) {
      case MODE_HEART:
        results.heartMeasured = true;
        break;
      case MODE_LUNG:
        results.lungMeasured = true;
        break;
      case MODE_TEMPERATURE:
        results.temperatureMeasured = true;
        break;
    }
    
    // Check if all measurements are complete
    if (results.heartMeasured && results.lungMeasured && results.temperatureMeasured) {
      currentState = STATE_FINAL_SUMMARY;
    } else {
      currentState = STATE_MAIN_MENU; // Return to menu for next measurement
    }
    stateStartTime = currentTime;
  }
}

void handleFinalSummary() {
  displayFinalSummary();
  
  // Generate final diagnosis
  generateFinalDiagnosis();
  
  // Set final LED status
  if (results.riskLevel == 2) {
    digitalWrite(PIN_LED_WHITE, HIGH);
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_BLUE, LOW);
  } else if (results.riskLevel == 1) {
    digitalWrite(PIN_LED_BLUE, HIGH);
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_WHITE, LOW);
  } else {
    digitalWrite(PIN_LED_GREEN, HIGH);
    digitalWrite(PIN_LED_BLUE, LOW);
    digitalWrite(PIN_LED_WHITE, LOW);
  }
}

void generateResults() {
  // Simulate AI processing results
  // You can change simulateAbnormal to true to demonstrate abnormal results
  
  switch (selectedMode) {
    case MODE_HEART:
      if (simulateAbnormal) {
        results.heartResult = "Murmur Detected";
        results.riskLevel = 2; // Alert
      } else {
        results.heartResult = "Normal Rhythm";
        results.riskLevel = 0; // Normal
      }
      break;
      
    case MODE_LUNG:
      if (simulateAbnormal) {
        results.lungResult = "Wheeze Detected";
        results.riskLevel = 1; // Caution
      } else {
        results.lungResult = "Clear Breathing";
        results.riskLevel = 0; // Normal
      }
      break;
      
    case MODE_TEMPERATURE:
      results.temperature = thermo.getTemperature();
      if (results.temperature > 37.5) {
        results.riskLevel = 1; // Fever
      } else {
        results.riskLevel = 0; // Normal
      }
      break;
  }
}

void generateFinalDiagnosis() {
  // Combine all measurements for final diagnosis
  int totalRisk = 0;
  
  if (results.heartResult.indexOf("Murmur") >= 0) totalRisk += 2;
  if (results.lungResult.indexOf("Wheeze") >= 0) totalRisk += 1;
  if (results.temperature > 37.5) totalRisk += 1;
  
  if (totalRisk >= 3) {
    results.finalDiagnosis = "HIGH RISK - Immediate Care";
    results.riskLevel = 2;
  } else if (totalRisk >= 1) {
    results.finalDiagnosis = "MODERATE RISK - Monitor";
    results.riskLevel = 1;
  } else {
    results.finalDiagnosis = "LOW RISK - Normal";
    results.riskLevel = 0;
  }
}

void handleButton(bool pressed) {
  if (pressed && !wasPressed) {
    buzzer.tone(1000, 100); // Click sound
    
    switch (currentState) {
      case STATE_MAIN_MENU:
        if (menuIndex == 0) {
          currentState = STATE_SELECT_MODE;
          lastMenuIndex = -1;
        } else if (menuIndex == 1) {
          displaySystemInfo();
        } else if (menuIndex == 2) {
          displayMeasurementHistory();
        } else if (menuIndex == 3) {
          currentState = STATE_FINAL_SUMMARY;
        }
        break;
        
      case STATE_SELECT_MODE:
        currentState = STATE_POSITIONING;
        stateStartTime = millis();
        digitalWrite(PIN_LED_GREEN, LOW);
        break;
        
      case STATE_RESULTS:
        // Allow manual control of result display
        simulateAbnormal = !simulateAbnormal; // Toggle for demo
        generateResults();
        break;
        
      case STATE_FINAL_SUMMARY:
        // Reset system
        resetSystem();
        break;
        
      default:
        currentState = STATE_MAIN_MENU;
        break;
    }
    
    delay(200); // Debounce
  }
  wasPressed = pressed;
}

void resetSystem() {
  // Reset all measurements
  results.heartMeasured = false;
  results.lungMeasured = false;
  results.temperatureMeasured = false;
  results.heartResult = "Normal";
  results.lungResult = "Normal";
  results.temperature = 36.5;
  results.finalDiagnosis = "Normal";
  results.riskLevel = 0;
  
  // Reset servos
  progressServo.write(0);
  resultServo.write(90);
  
  // Reset LEDs
  digitalWrite(PIN_LED_GREEN, HIGH);
  digitalWrite(PIN_LED_BLUE, LOW);
  digitalWrite(PIN_LED_WHITE, LOW);
  
  // Return to main menu
  currentState = STATE_MAIN_MENU;
  buzzer.tone(800, 200);
}

// --- DISPLAY FUNCTIONS ---

void displayMainMenu() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("TRIAGE STATION - MAIN MENU");
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  display.setCursor(5, 20);
  if(menuIndex == 0) display.print("> START MEASUREMENT");
  else display.print("  START MEASUREMENT");
  
  display.setCursor(5, 30);
  if(menuIndex == 1) display.print("> SYSTEM INFO");
  else display.print("  SYSTEM INFO");
  
  display.setCursor(5, 40);
  if(menuIndex == 2) display.print("> VIEW HISTORY");
  else display.print("  VIEW HISTORY");
  
  display.setCursor(5, 50);
  if(menuIndex == 3) display.print("> FINAL RESULTS");
  else display.print("  FINAL RESULTS");
  
  display.display();
}

void displayModeSelection() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("SELECT MEASUREMENT MODE");
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  display.setTextSize(2);
  display.setCursor(10, 25);
  
  switch (selectedMode) {
    case MODE_HEART:
      display.print("< HEART >");
      break;
    case MODE_LUNG:
      display.print("< LUNG >");
      break;
    case MODE_TEMPERATURE:
      display.print("< TEMP >");
      break;
  }
  
  display.setTextSize(1);
  display.setCursor(0, 55);
  display.print("[CLICK] to SELECT");
  display.display();
}

void displayPositioning(bool valid) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print("POSITIONING - ");
  
  switch (selectedMode) {
    case MODE_HEART:
      display.println("HEART");
      break;
    case MODE_LUNG:
      display.println("LUNG");
      break;
    case MODE_TEMPERATURE:
      display.println("TEMPERATURE");
      break;
  }
  
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  display.setTextSize(2);
  display.setCursor(10, 25);
  
  if (valid) {
    display.print("READY!");
  } else {
    display.print("POSITION");
    display.setCursor(15, 45);
    display.print("DEVICE");
  }
  
  display.display();
}

void displayRecording(unsigned long elapsed, unsigned long duration, int micValue) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print("RECORDING - ");
  
  switch (selectedMode) {
    case MODE_HEART:
      display.println("HEART SOUNDS");
      break;
    case MODE_LUNG:
      display.println("LUNG SOUNDS");
      break;
    case MODE_TEMPERATURE:
      display.println("TEMPERATURE");
      break;
  }
  
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  // Progress bar
  int progress = map(elapsed, 0, duration, 0, 128);
  display.fillRect(0, 20, progress, 8, SSD1306_WHITE);
  display.drawRect(0, 20, 128, 8, SSD1306_WHITE);
  
  // Time remaining
  display.setCursor(0, 35);
  display.print("Time: ");
  display.print((duration - elapsed) / 1000);
  display.print("s");
  
  // Microphone visualization
  display.setCursor(0, 45);
  display.print("Signal: ");
  int barWidth = map(micValue, 0, 1023, 0, 60);
  display.fillRect(50, 45, barWidth, 6, SSD1306_WHITE);
  
  display.setCursor(0, 55);
  display.print("VOICE CAPTURED");
  
  display.display();
}

void displayProcessing(unsigned long elapsed, unsigned long duration) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("PROCESSING...");
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  display.setTextSize(2);
  display.setCursor(20, 25);
  display.print("AI ANALYSIS");
  
  // Processing animation
  int dots = (elapsed / 500) % 4;
  display.setTextSize(1);
  display.setCursor(0, 50);
  display.print("Analyzing");
  for (int i = 0; i < dots; i++) {
    display.print(".");
  }
  
  display.display();
}

void displayResults() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print("RESULTS - ");
  
  switch (selectedMode) {
    case MODE_HEART:
      display.println("HEART");
      display.setCursor(0, 20);
      display.setTextSize(1);
      display.print("Status: ");
      display.println(results.heartResult);
      break;
      
    case MODE_LUNG:
      display.println("LUNG");
      display.setCursor(0, 20);
      display.setTextSize(1);
      display.print("Status: ");
      display.println(results.lungResult);
      break;
      
    case MODE_TEMPERATURE:
      display.println("TEMPERATURE");
      display.setCursor(0, 20);
      display.setTextSize(2);
      display.print(results.temperature, 1);
      display.print(" C");
      break;
  }
  
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  // Risk level indicator
  display.setTextSize(1);
  display.setCursor(0, 45);
  display.print("Risk Level: ");
  
  switch (results.riskLevel) {
    case 0:
      display.print("NORMAL");
      break;
    case 1:
      display.print("CAUTION");
      break;
    case 2:
      display.print("ALERT");
      break;
  }
  
  display.setCursor(0, 55);
  display.print("[CLICK] to toggle result");
  
  display.display();
}

void displayFinalSummary() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("FINAL DIAGNOSIS");
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  display.setCursor(0, 15);
  display.print("Heart: ");
  display.println(results.heartMeasured ? "Done" : "Pending");
  
  display.setCursor(0, 25);
  display.print("Lung: ");
  display.println(results.lungMeasured ? "Done" : "Pending");
  
  display.setCursor(0, 35);
  display.print("Temp: ");
  display.print(results.temperature, 1);
  display.println("C");
  
  display.setCursor(0, 45);
  display.print("Diagnosis:");
  display.setCursor(0, 55);
  display.print(results.finalDiagnosis);
  
  display.display();
}

void displaySystemInfo() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("SYSTEM INFORMATION");
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  display.setCursor(0, 15);
  display.println("Smart Rural Triage Station");
  display.setCursor(0, 25);
  display.println("Version: 1.0 Demo");
  display.setCursor(0, 35);
  display.println("Status: Online");
  display.setCursor(0, 45);
  display.println("AI Models: Loaded");
  display.setCursor(0, 55);
  display.println("[CLICK] to return");
  
  display.display();
}

void displayMeasurementHistory() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("MEASUREMENT HISTORY");
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  display.setCursor(0, 15);
  display.print("Heart: ");
  display.println(results.heartMeasured ? results.heartResult : "Not measured");
  
  display.setCursor(0, 25);
  display.print("Lung: ");
  display.println(results.lungMeasured ? results.lungResult : "Not measured");
  
  display.setCursor(0, 35);
  display.print("Temperature: ");
  if (results.temperatureMeasured) {
    display.print(results.temperature, 1);
    display.println("C");
  } else {
    display.println("Not measured");
  }
  
  display.setCursor(0, 55);
  display.println("[CLICK] to return");
  
  display.display();
}

void sendSensorData() {
  StaticJsonDocument<256> doc;
  doc["knob"] = knob.get();
  doc["temp"] = thermo.getTemperature();
  
  float x = movement.getX();
  doc["movement"] = (abs(x) > 1.2) ? 1 : 0;
  doc["mic"] = analogRead(PIN_MIC_ANALOG);
  doc["state"] = currentState;
  doc["mode"] = selectedMode;
  doc["progress"] = progressValue;
  
  serializeJson(doc, Serial);
  Serial.println();
  serializeJson(doc, Serial1);
  Serial1.println();
}