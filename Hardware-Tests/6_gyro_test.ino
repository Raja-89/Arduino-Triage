/*
  COMPONENT TEST 6: GYRO/ACCEL (IMU)
  ==================================
  Tests LSM6DS3 on Wire1.
  Address: 0x6A
  
  LIBRARIES REQUIRED:
  - Adafruit LSM6DS3
  - Adafruit Unified Sensor
  
  CONNECTIONS (Qwiic/Wire1):
  - SDA -> SDA1 
  - SCL -> SCL1
*/

#include <Wire.h>
#include <Adafruit_LSM6DS3.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);
Adafruit_LSM6DS3 lsm6ds3;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire1.begin(); // Wire1 for sensors
  
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  if (!lsm6ds3.begin_I2C(0x6A, &Wire1)) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);
    display.println(F("LSM6DS3 Failed!"));
    display.display();
    while(1);
  }
}

void loop() {
  sensors_event_t accel, gyro, temp;
  lsm6ds3.getEvent(&accel, &gyro, &temp);

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  display.setCursor(0,0);
  display.println(F("IMU (LSM6DS3)"));
  
  display.setCursor(0,15);
  display.print("X: "); display.print(accel.acceleration.x, 1);
  display.print("  Y: "); display.println(accel.acceleration.y, 1);
  
  display.setCursor(0,25);
  display.print("Z: "); display.println(accel.acceleration.z, 1);
  
  // Simple tilt visual
  int barX = map(accel.acceleration.x * 10, -100, 100, 0, 128);
  display.fillRect(barX, 50, 10, 10, SSD1306_WHITE);
  
  display.display();
  delay(100);
}
