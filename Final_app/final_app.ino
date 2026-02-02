/*
  ARDUINO APP LAB: SMART SENSING HUB
  ==================================
  Central Sketch for integrating:
  - OLED Display (Wire)
  - Knob, Speaker, Temp, Gyro (Wire1)
  - Microphone (A0)
  
  MODES (Controlled by Knob):
  0: DASHBOARD (Monitor Sensors)
  1: DATA STREAM (Send to PC)
  2: ALARM / SECURITY (Wait for PC Command)
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "SparkFun_Qwiic_Twist_Arduino_Library.h" 
#include "SparkFun_Qwiic_Speaker_Arduino_Library.h" 
#include <Arduino_HS300x.h>
#include <Adafruit_LSM6DS3.h>
#include <Adafruit_Sensor.h>

// --- CONFIG ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C 
const int PIN_MIC = A0;

// --- OBJECTS ---
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
TWIST twist;
QwiicSpeaker speaker;
Adafruit_LSM6DS3 imu;
// HS300x is a singleton "HS300x"

// --- STATE ---
int currentMode = 0; // 0=Dash, 1=Stream, 2=Alarm
unsigned long lastUpdate = 0;

void setup() {
  Serial.begin(115200);
  
  // 1. INIT BUSES
  Wire.begin();
  Wire1.begin();
  
  // 2. INIT DISPLAY
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
     Serial.println(F("Disp Fail")); while(1);
  }
  showSplash("Starting...");
  
  // 3. INIT SENSORS (Wire1)
  bool err = false;
  
  // Knob (Try 0x41 then 0x3F)
  if(!twist.begin(Wire1, 0x41)) {
     if(!twist.begin(Wire1, 0x3F)) err = true;
  }
  
  // Speaker
  if(!speaker.begin(Wire1)) {
    // Optional: err = true; (Don't fail whole app if speaker missing)
  } else {
    speaker.setVolume(20);
  }

  // IMU (Gyro)
  if(!imu.begin_I2C(0x6A, &Wire1)) {
    // err = true; 
  }

  // Temp
  if(!HS300x.begin()) {
    // err = true;
  }

  if(err) showSplash("Sensor Error!");
  else showSplash("System Ready");
  
  delay(1000);
}

void loop() {
  // 1. READ INPUTS
  readKnob();
  
  // 2. RUN MODES
  switch(currentMode) {
    case 0: modeDashboard(); break;
    case 1: modeStream(); break;
    case 2: modeAlarm(); break;
  }
  
  delay(50); // Small regulation
}

// --- HELPER FUNCTIONS ---

void showSplash(const char* msg) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,20);
  display.println(F("APP LAB HUB"));
  display.drawLine(0, 30, 128, 30, SSD1306_WHITE);
  display.setCursor(0, 40);
  display.println(msg);
  display.display();
}

void readKnob() {
  // Read knob count to switch modes (0, 1, 2)
  int count = twist.getCount();
  
  // Normalize to 0-2 range
  // User can twist infinitely, so we use modulo or map logic
  // Simple logic: every 2 clicks changes mode
  int selected = (abs(count) / 2) % 3;
  
  if (selected != currentMode) {
    currentMode = selected;
    // Update Knob Color
    if(currentMode == 0) twist.setColor(0, 0, 255); // Blue = Dash
    if(currentMode == 1) twist.setColor(0, 255, 0); // Green = Stream
    if(currentMode == 2) twist.setColor(255, 0, 0); // Red = Alarm
  }
}

void modeDashboard() {
  // Gathers data and shows pretty UI
  float t = HS300x.readTemperature();
  int mic = analogRead(PIN_MIC);
  
  // Get IMU
  sensors_event_t a, g, temp;
  imu.getEvent(&a, &g, &temp);

  display.clearDisplay();
  
  // Header
  display.setTextSize(1);
  display.setCursor(0,0);
  display.print(F("DASHBOARD"));
  
  // Temp
  display.setCursor(0, 15);
  display.print(F("Temp: ")); display.print(t, 1); display.print(F(" C"));
  
  // Mic Bar
  int bar = map(mic, 0, 600, 0, 50); // Tune this!
  display.setCursor(0, 28);
  display.print(F("Snd: "));
  display.fillRect(30, 28, bar, 8, SSD1306_WHITE);
  
  // Gyro Ball
  // Draw a circle that moves based on X/Y tilt
  int ballX = map(a.acceleration.x, -10, 10, 0, 128);
  display.fillCircle(ballX, 55, 4, SSD1306_WHITE);
  display.drawRect(0, 45, 128, 19, SSD1306_WHITE); // Floor
  
  display.display();
}

void modeStream() {
  // Sends CSV data to Serial for Python
  // Format: "D, <Temp>, <Mic>, <AccelX>"
  float t = HS300x.readTemperature();
  int mic = analogRead(PIN_MIC);
  sensors_event_t a, g, temp;
  imu.getEvent(&a, &g, &temp);
  
  Serial.print("D,");
  Serial.print(t); Serial.print(",");
  Serial.print(mic); Serial.print(",");
  Serial.println(a.acceleration.x);
  
  // UI
  display.clearDisplay();
  display.setCursor(0,0);
  display.println(F("STREAMING DATA..."));
  display.setCursor(0,30);
  display.print(F("To Serial/PC"));
  display.display();
}

void modeAlarm() {
  // Waits for 'A' from Serial
  if(Serial.available() > 0) {
    char c = Serial.read();
    if (c == 'A' || c == 'a') {
      triggerAlarm();
    }
  }
  
  display.clearDisplay();
  display.setCursor(0,0);
  display.println(F("SECURITY MODE"));
  display.setCursor(0, 30);
  display.println(F("Scanning..."));
  display.drawRect(10, 20, 108, 30, SSD1306_WHITE); // Viewfinder box
  display.display();
}

void triggerAlarm() {
  display.invertDisplay(true);
  display.clearDisplay();
  display.setCursor(20, 20);
  display.setTextSize(2);
  display.println(F("ALARM!"));
  display.display();
  
  // Play Pulse
  speaker.playSound(5); // Adjust sound index
  delay(100);
  speaker.playSound(5);
  delay(100);
  
  display.invertDisplay(false);
}
