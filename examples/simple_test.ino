/*
  MIC & DISPLAY TEST
  ==================
  Focus: Testing the Microphone Connection on Pin A0.
  
  What to watch on the Screen:
  1. "RAW": This number should flicker rapidly (e.g. 300-600).
     - If STUCK at 0: Pin is grounded or not connected.
     - If STUCK at 1023 (or 4095): Pin is connected to VCC or floating high.
  2. "DIFF": The difference between loud and quiet. 
     - Should jump when you clap or speak.
  
  CONNECTIONS:
  - Mic OUT -> Pin A0
  - Mic VCC -> 5V (or 3.3V)
  - Mic GND -> GND
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
  
  // Try to start display
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("Display failed. Check wiring."));
    for(;;);
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10);
  display.println(F("MIC TEST MODE"));
  display.display();
  delay(1000);
}

void loop() {
  // === SENSITIVITY SETTINGS ===
  // Increase 'NOISE_THRESHOLD' if the bar moves when silent (e.g. try 10, 20, 30)
  const int NOISE_THRESHOLD = 15; 
  
  // Increase 'MAX_VOLUME' if the bar fills up too easily (e.g. try 100, 200)
  const int MAX_VOLUME = 150; 
  // ============================

  unsigned long startMillis = millis(); 
  unsigned int signalMax = 0;
  unsigned int signalMin = 1024;

  // 1. Listen for 50ms
  while (millis() - startMillis < 50) {
    int sample = analogRead(micPin);
    if (sample > 0 && sample < 1023) {
      if (sample > signalMax) signalMax = sample;
      if (sample < signalMin) signalMin = sample;
    }
  }
  
  if (signalMax == 0) signalMin = 0;
  int peakToPeak = signalMax - signalMin;

  // 2. Map Amplitude to Screen Width
  // We use the settings above to "Clamp" the values
  int displayValue = 0;
  if (peakToPeak > NOISE_THRESHOLD) {
     displayValue = map(peakToPeak, NOISE_THRESHOLD, MAX_VOLUME, 0, 128);
  }
  
  // Keep within screen bounds
  if (displayValue < 0) displayValue = 0;
  if (displayValue > 128) displayValue = 128;

  // 3. Update Display
  display.clearDisplay();
  
  // Header
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("RAW: "); display.print(peakToPeak);
  
  display.setCursor(64, 0);
  display.print("Gate: "); display.print(NOISE_THRESHOLD); // Show current gate

  // Visual: Bar Graph
  display.fillRect(0, 20, displayValue, 10, SSD1306_WHITE);
  display.drawRect(0, 20, 128, 10, SSD1306_WHITE);

  // Visual: Circle
  int radius = map(displayValue, 0, 128, 2, 25);
  display.fillCircle(64, 48, radius, SSD1306_WHITE);

  // Visual: Status Text
  display.setCursor(0, 56);
  if(peakToPeak <= NOISE_THRESHOLD) {
     display.print("Silent"); // Below threshold
  } else if (displayValue < 60) {
     display.print("Picking up...");
  } else {
     display.print("LOUD!");
  }

  display.display();
}
