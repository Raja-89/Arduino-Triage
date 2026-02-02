/*
  COMPONENT TEST 1: OLED DISPLAY
  ==============================
  Tests the I2C OLED Screen.
  
  LIBRARIES REQUIRED (Install via Library Manager):
  - Adafruit GFX Library
  - Adafruit SSD1306
  
  CONNECTIONS:
  - SDA -> SDA (Wire0)
  - SCL -> SCL (Wire0)
  - VCC -> 5V/3.3V
  - GND -> GND
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C 

// Display is on the Primary I2C Bus (Wire)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

void setup() {
  Serial.begin(115200);
  Wire.begin(); 

  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }

  // 1. Text Test
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println(F("TEST 1: DISPLAY"));
  display.println(F("Hello World!"));
  display.println(F("---------------------"));
  display.println(F("Graphics Test..."));
  display.display();
  delay(2000);

  // 2. Shape Test
  display.clearDisplay();
  display.fillCircle(64, 32, 20, SSD1306_WHITE);
  display.drawRect(10, 10, 108, 44, SSD1306_WHITE);
  display.display();
  delay(1000);
  
  // 3. Invert Test
  display.invertDisplay(true);
  delay(1000);
  display.invertDisplay(false);
  delay(1000);
  
  display.clearDisplay();
  display.setCursor(20, 30);
  display.print(F("DISPLAY OK"));
  display.display();
}

void loop() {
  // Do nothing
}
