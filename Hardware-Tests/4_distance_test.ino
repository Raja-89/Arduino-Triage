/*
  COMPONENT TEST 4: DISTANCE SENSOR
  =================================
  Tests VL53L0X functionality on Secondary I2C Bus (Wire1).
  Address: 0x29
  
  LIBRARIES REQUIRED:
  - Adafruit VL53L0X
  
  CONNECTIONS (Qwiic/Wire1):
  - SDA -> SDA1 
  - SCL -> SCL1
*/

#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

// Objects must be declared globally
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_VL53L0X lox = Adafruit_VL53L0X();

void setup() {
  Serial.begin(115200);
  
  // 1. Init Display Bus
  Wire.begin(); 
  
  // 2. Init Display immediately
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("Display Fail"));
    for(;;);
  }
  
  // 3. Show Splash immediately so we know display works
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println(F("DISPLAY ONLINE"));
  display.println(F("Init Sensor (Wire1)..."));
  display.display(); // PUSH TO SCREEN
  delay(500);

  // 4. Init Sensor Bus
  Wire1.begin();
  
  // 5. Init Sensor
  if (!lox.begin(0x29, false, &Wire1)) {
    display.setCursor(0, 20);
    display.println(F("Sensor NOT Found!"));
    display.println(F("Check Qwiic Cable"));
    display.display();
    while(1); // Stop here
  }
  
  display.println(F("Sensor OK!"));
  display.display();
  delay(500);
}

// ... (Setup remains same, this replaces user loop)

void loop() {
  VL53L0X_RangingMeasurementData_t measure;
  lox.rangingTest(&measure, false); 

  display.clearDisplay();
  
  // Header
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.print(F("DISTANCE (VL53L0X)"));

  if (measure.RangeStatus != 4) {
    int mm = measure.RangeMilliMeter;
    
    // 1. Text Readout
    display.setTextSize(2);
    display.setCursor(0, 20);
    display.print(mm); display.println(F("mm"));
    
    // 2. Visual Bar (Parking Sensor Style)
    // 50mm = Full Bar, 500mm = Empty Bar
    int barLen = map(mm, 50, 500, 128, 0); 
    if (barLen < 0) barLen = 0;
    if (barLen > 128) barLen = 128;
    
    display.fillRect(0, 45, barLen, 14, SSD1306_WHITE);
    display.drawRect(0, 45, 128, 14, SSD1306_WHITE);
    
    // Label for bar
    display.setTextSize(1);
    display.setCursor(0, 60); // Underneath
    if (mm < 50) display.print(F("STOP!"));
    else if (mm < 200) display.print(F("Close"));
    else display.print(F("Clear"));
    
  } else {
    display.setTextSize(2);
    display.setCursor(0, 30);
    display.print(F("Out of Rng"));
  }
  
  display.display();
  delay(50); // Faster update (50ms)
}
