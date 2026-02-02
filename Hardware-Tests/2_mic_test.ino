/*
  COMPONENT TEST 2: MICROPHONE
  ============================
  Tests the Analog Microphone (AGC/Electret).
  
  CONNECTIONS:
  - OUT -> A0
  - VCC -> 5V (or 3.3V)
  - GND -> GND
  - GAIN -> Disconnected (Floating = 60dB Max Gain)
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C 

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
const int micPin = A0;      

void setup() {
  Serial.begin(115200);
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    for(;;);
  }
}

void loop() {
  // SENSITIVITY CONFIG
  const int NOISE_THRESHOLD = 15; 
  const int MAX_VOLUME = 150; 

  unsigned long startMillis = millis(); 
  unsigned int signalMax = 0;
  unsigned int signalMin = 1024;

  while (millis() - startMillis < 50) {
    int sample = analogRead(micPin);
    if (sample > 0 && sample < 1023) {
      if (sample > signalMax) signalMax = sample;
      if (sample < signalMin) signalMin = sample;
    }
  }
  
  if (signalMax == 0) signalMin = 0;
  int peakToPeak = signalMax - signalMin;

  int displayValue = 0;
  if (peakToPeak > NOISE_THRESHOLD) {
     displayValue = map(peakToPeak, NOISE_THRESHOLD, MAX_VOLUME, 0, 128);
  }
  if (displayValue > 128) displayValue = 128;

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.print("MIC TEST (A0): "); display.print(peakToPeak);
  
  // Bar Graph
  display.fillRect(0, 20, displayValue, 20, SSD1306_WHITE);
  display.drawRect(0, 20, 128, 20, SSD1306_WHITE);

  display.setCursor(0, 50);
  if(displayValue > 10) display.print("DETECTED");
  else display.print("SILENT");

  display.display();
}
