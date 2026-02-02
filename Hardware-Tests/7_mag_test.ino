/*
  COMPONENT TEST 7: MAGNETOMETER
  ==============================
  Tests LIS3MDL on Wire1.
  Address: 0x1E
  
  LIBRARIES REQUIRED:
  - Adafruit LIS3MDL
  
  CONNECTIONS (Qwiic/Wire1):
  - SDA -> SDA1 
  - SCL -> SCL1
*/

#include <Wire.h>
#include <Adafruit_LIS3MDL.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);
Adafruit_LIS3MDL lis3mdl;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire1.begin(); 
  
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  if (!lis3mdl.begin_I2C(0x1E, &Wire1)) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);
    display.println(F("LIS3MDL Failed!"));
    display.display();
    while(1);
  }
}

void loop() {
  sensors_event_t event;
  lis3mdl.getEvent(&event);

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  display.setCursor(0,0);
  display.println(F("MAGNETOMETER"));
  
  display.print("X: "); display.println(event.magnetic.x);
  display.print("Y: "); display.println(event.magnetic.y);
  display.print("Z: "); display.println(event.magnetic.z);
  
  display.display();
  delay(100);
}
