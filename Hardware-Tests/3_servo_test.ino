/*
  COMPONENT TEST 3: SERVOS + DISPLAY
  ==================================
  Tests 2 Servos sweeping back and forth and shows angle on OLED.
  
  CONNECTIONS:
  - Servo 1 Signal -> Pin 9
  - Servo 2 Signal -> Pin 10
  - Servo VCC      -> 5V
  - Servo GND      -> GND
  - Display        -> SDA/SCL (As usual)
*/

#include <Servo.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C 

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Servo s1;
Servo s2;

void setup() {
  Serial.begin(115200);
  
  // Init Servos
  s1.attach(9);
  s2.attach(10);
  
  // Init Display
  Wire.begin();
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
     for(;;); // Loop forever if display fails
  }
}

void loop() {
  // Sweep Forward (0 -> 180)
  moveServosAndDisplay(0, 180, 1);
  delay(500);
  
  // Sweep Backward (180 -> 0)
  moveServosAndDisplay(180, 0, -1);
  delay(500);
}

// Helper function to move and update screen
void moveServosAndDisplay(int start, int end, int step) {
  // Determine loop direction
  if (step > 0) {
    for (int pos = start; pos <= end; pos += step) {
       updateHardware(pos);
    }
  } else {
    for (int pos = start; pos >= end; pos += step) {
       updateHardware(pos);
    }
  }
}

void updateHardware(int pos) {
  // 1. Move Motors
  s1.write(pos);
  s2.write(180 - pos); // Move opposite
  
  // 2. Update Display (every 5 degrees to be faster)
  if (pos % 5 == 0) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    
    display.setCursor(0,0);
    display.println(F("SERVO TEST"));
    
    // Text Angle
    display.setTextSize(2);
    display.setCursor(30, 20);
    display.print(pos);
    display.print((char)247); // Degree symbol
    
    // Visual Bar
    int barWidth = map(pos, 0, 180, 0, 128);
    display.fillRect(0, 50, barWidth, 10, SSD1306_WHITE);
    display.drawRect(0, 50, 128, 10, SSD1306_WHITE); // Frame
    
    display.display();
  }
  
  delay(15); // Controls speed of sweep
}
