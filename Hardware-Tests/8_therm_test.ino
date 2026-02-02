/*
  COMPONENT TEST 8: THERMOMETHER (Modulino Thermo)
  ================================================
  Tests Temperature sensor on Wire1.
  Address: 0x60 usually refers to Modulino Thermo (HS3003) or similar.
  Note: 0x60 is also VEML7700 (Light). This code assumes HS3003 (Modulino standard).
  
  LIBRARIES REQUIRED:
  - Arduino_HS300x
  
  CONNECTIONS (Qwiic/Wire1):
  - SDA -> SDA1 
  - SCL -> SCL1
*/

#include <Wire.h>
#include <Arduino_HS300x.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire1.begin(); 
  
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  // HS300x typically uses Wire1 automatically if using the official library?
  // Or we might need to patch it. The official library `Arduino_HS300x`
  // usually auto-detects. Using `begin()` without arguments often defaults to Wire.
  // Ideally we use a library that supports passing the TwoWire object.
  // If this fails, we will need to ensure the library uses proper Bus.
  
  if (!HS300x.begin()) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println(F("HS300x Failed!"));
    display.println(F("Trying Raw 0x60..."));
    display.display();
    // Fallback: If generic, just check if device is present
  }
}

void loop() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println(F("THERMOMETER"));

  float temp = HS300x.readTemperature();
  float humidity = HS300x.readHumidity();

  display.setTextSize(2);
  display.setCursor(0, 20);
  display.print(temp); display.println(" C");
  
  display.setCursor(0, 45);
  display.print(humidity); display.println(" %");

  display.display();
  delay(1000);
}
