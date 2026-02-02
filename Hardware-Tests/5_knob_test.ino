/*
  COMPONENT TEST 5: KNOB (ENCODER)
  ================================
  Tests I2C Encoder/Knob functionality (Wire1).
  Possible Address: 0x41 or 0x3A. This code tries 0x41 (SparkFun Qwiic Twist).
  
  LIBRARIES REQUIRED:
  - SparkFun Qwiic Twist Arduino Library
  
  CONNECTIONS (Qwiic/Wire1):
  - SDA -> SDA1 
  - SCL -> SCL1
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "SparkFun_Qwiic_Twist_Arduino_Library.h" 

Adafruit_SSD1306 display(128, 64, &Wire, -1);
TWIST twist; 

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire1.begin();
  
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  // Init Twist on Wire1 with Explicit Address 0x41
  // The scan found 0x41, but library defaults might be different.
  if(twist.begin(Wire1, 0x41) == false) {
    // Try fallback to 0x3F or 0x40 just in case
    if(twist.begin(Wire1, 0x3F) == false) {
       display.clearDisplay();
       display.setCursor(0,0);
       display.println(F("Twist Knob Failed!"));
       display.println(F("Tried 0x41 & 0x3F"));
       display.display();
       while(1);
    }
  }
}

void loop() {
  display.clearDisplay();
  
  // Read Count
  int count = twist.getCount();
  bool clicked = twist.isPressed();
  
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.print("KNOB: "); display.println(count);
  
  if (clicked) {
    display.setCursor(0, 40);
    display.print("CLICKED!");
    // Change color on twist if supported
    twist.setColor(255, 0, 0); 
  } else {
    twist.setColor(0, 255, 0);
  }

  display.display();
  delay(50);
}
