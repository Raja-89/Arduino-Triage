/*
  COMPONENT TEST 9: QWIIC BUZZER / SPEAKER
  ========================================
  Tests the Qwiic Speaker on Wire1.
  
  IMPORTANT: 
  This requires the "SparkFun Qwiic Speaker" Library.
  
  CONNECTIONS (Qwiic/Wire1):
  - SDA -> SDA1 
  - SCL -> SCL1
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "SparkFun_Qwiic_Speaker_Arduino_Library.h" 

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C 

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
QwiicSpeaker qwiicSpeaker;

void setup() {
  Serial.begin(115200);
  
  // 1. Init Display
  Wire.begin();
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
     for(;;);
  }
  
  // 2. Init Speaker (Wire1)
  Wire1.begin();
  if(qwiicSpeaker.begin(Wire1) == false) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);
    display.println(F("Qwiic Speaker Fail!"));
    display.println(F("Check Qwiic Cable"));
    display.display();
    while(1);
  }
  
  qwiicSpeaker.setVolume(20); // Set Volume (max 255)
}

void loop() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println(F("QWIIC SPEAKER TEST"));
  
  // 1. Visual
  display.fillCircle(64, 32, 12, SSD1306_WHITE);
  display.display();
  
  // 2. Play Sound (Melody)
  // plays a quick rising scale
  qwiicSpeaker.playSound(10); 
  delay(200);
  qwiicSpeaker.playSound(20);
  delay(200);
  
  display.drawCircle(64, 32, 12, SSD1306_WHITE); // Empty
  display.display();
  
  delay(1000);
}
