/* 
  🏥 HARDWARE DIAGNOSTIC TEST (FINAL FIX) 🏥
  
  Updates:
  - Fixed Thermo: Uses .getTemperature()
  - Fixed Movement: Uses .getX() / .getY() / .getZ()
  - Display Color: Explained in comments (Hardware is monochrome).
*/

#include <Wire.h>
#include <Servo.h>
#include <Modulino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- CONFIG ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C 

// --- PINS ---
const int PIN_MIC = A1;         
const int PIN_LED = 6;
const int PIN_SERVO_PROG = 9;   
const int PIN_SERVO_RES = 10;   

// --- OBJECTS ---
Servo s1;
Servo s2;
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
ModulinoKnob knob;
ModulinoMovement movement;
ModulinoThermo thermo;
ModulinoBuzzer buzzer;

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== STARTING HARDWARE TEST ===");

  Wire.begin();
  
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("❌ OLED FAILED");
  } else {
    Serial.println("✅ OLED OK");
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE); // Standard White on Black
    // display.invertDisplay(true);      // Uncomment to make it Black on White
    display.setTextSize(1);
    display.setCursor(0,0);
    display.println("TEST MODE ACTIVE");
    display.display();
  }

  // Init Modulino
  Modulino.begin();
  knob.begin();
  movement.begin();
  thermo.begin();
  buzzer.begin();

  pinMode(PIN_MIC, INPUT);
  pinMode(PIN_LED, OUTPUT);
  
  s1.attach(PIN_SERVO_PROG);
  s2.attach(PIN_SERVO_RES);

  // Quick Hardware Wiggle
  digitalWrite(PIN_LED, HIGH); delay(100); digitalWrite(PIN_LED, LOW);
  s1.write(10); s2.write(10); delay(200); s1.write(0); s2.write(90);
  buzzer.tone(2000, 50);

  Serial.println("=== LOOP STARTING ===");
}

void loop() {
  // 1. READ KNOB
  int kVal = knob.get();
  
  // 2. READ TEMP (Fixed API)
  float tVal = thermo.getTemperature(); 
  
  // 3. READ MOVEMENT (Fixed API)
  // The sensor returns Acceleration in G's. 
  // We check if it is moving by seeing if X/Y/Z changes rapidly.
  float x = movement.getX();
  float y = movement.getY();
  float z = movement.getZ();
  // Simple check: Is the vector sum roughly 1G (gravity)?
  // If we just want raw "Is it Moving?", we can check variance.
  bool mVal = (abs(x) > 1.2 || abs(y) > 1.2 || abs(z) > 1.2); 
  // (Threshold 1.2 is simplified. If you shake it, it goes > 1.2 or < 0.8)

  // 4. READ MIC
  int micVal = analogRead(PIN_MIC);

  // PRINT SERIAL
  Serial.print("Knob: "); Serial.print(kVal);
  Serial.print(" | Temp: "); Serial.print(tVal);
  Serial.print(" | Accel X: "); Serial.print(x);
  Serial.print(" | Mic: "); Serial.println(micVal);

  // UPDATE OLED
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("HARDWARE TEST");
  
  display.setCursor(0,15);
  display.print("Knob:"); display.println(kVal);
  
  display.setCursor(0,25);
  display.print("Mic:"); display.println(micVal);
  
  display.setCursor(0,35);
  display.print("Temp:"); display.print(tVal); display.println("C");

  display.setCursor(0,45);
  display.print("X-Axis:"); display.println(x, 2); 
  
  display.display();

  // LED Logic (Blink on large movement)
  if(abs(x) > 1.5) digitalWrite(PIN_LED, HIGH); else digitalWrite(PIN_LED, LOW);
  
  // Servo Mirroring Knob
  int angle = map(kVal, 0, 100, 0, 180); 
  s1.write(angle);

  delay(100);
}
