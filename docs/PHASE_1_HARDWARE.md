# 🔧 PHASE 1: Hardware Foundation & Basic I/O

**Objective**: Establish stable hardware platform with all components working and communicating properly.

## 🎯 Phase 1 Goals

By the end of this phase, you must have:
- ✅ Arduino UNO Q Linux system verified and accessible
- ✅ All Modulino sensors reading correctly
- ✅ Servos, buzzer, and relay responding to commands
- ✅ MCU ↔ Linux communication established
- ✅ Camera feed working
- ✅ Complete pin mapping documented
- ✅ System architecture validated

**⚠️ CRITICAL**: Do not proceed to Phase 2 until ALL items above are working. Hardware issues compound exponentially later.

## 📚 Hardware Fundamentals for Beginners

### What is Arduino?
Arduino is an open-source electronics platform that makes it easy to create interactive projects. Think of it as a small computer that can:
- Read inputs (sensors, buttons, switches)
- Process information (run your code)
- Control outputs (LEDs, motors, speakers)

**Key Concepts:**
- **Microcontroller**: The "brain" - a tiny computer chip that runs your program
- **Digital Pins**: Can be ON (HIGH/5V) or OFF (LOW/0V) - like light switches
- **Analog Pins**: Can read varying voltages (0V to 5V) - like dimmer switches
- **PWM**: Pulse Width Modulation - rapidly switching ON/OFF to simulate analog output
- **I2C/SPI**: Communication protocols for talking to multiple devices

### Arduino UNO Q - Your Dual-Brain System

The Arduino UNO Q is special because it has **TWO processors**:

#### 1. **Linux Side (QRB2210 - The Smart Brain)**
- **What it is**: A powerful ARM processor running full Linux OS
- **What it does**: Heavy computing, AI processing, web interfaces, camera handling
- **Think of it as**: A mini computer like Raspberry Pi
- **Specifications**:
  - Quad-core ARM Cortex-A53 @ 2.0GHz
  - 2GB RAM, 8GB storage
  - Runs Python, TensorFlow, web servers
  - Handles WiFi, Bluetooth, USB devices

#### 2. **MCU Side (STM32U585 - The Fast Brain)**
- **What it is**: A real-time microcontroller (traditional Arduino-like)
- **What it does**: Fast sensor reading, motor control, immediate responses
- **Think of it as**: The reflexes of your system
- **Specifications**:
  - ARM Cortex-M33 @ 160MHz
  - 2MB Flash, 786KB RAM
  - Real-time responses (microsecond timing)
  - Direct hardware control

**Why Two Brains?**
- Linux brain: "I need to analyze this heart sound with AI" (takes 100ms)
- MCU brain: "Patient moved! Stop recording NOW!" (takes 1ms)

### Understanding Pins and Connections

#### Digital Pins (D0-D13)
**What they are**: Pins that can be either ON (5V) or OFF (0V)

**Uses:**
- **Input**: Reading buttons, switches, motion sensors
  ```cpp
  int buttonState = digitalRead(2); // Read pin D2
  if (buttonState == HIGH) {
    // Button is pressed
  }
  ```
- **Output**: Controlling LEDs, relays, buzzers
  ```cpp
  digitalWrite(13, HIGH); // Turn ON LED on pin D13
  digitalWrite(13, LOW);  // Turn OFF LED on pin D13
  ```

#### Analog Pins (A0-A5)
**What they are**: Pins that can read varying voltages (0V to 5V)

**How they work**: 
- 0V = reading of 0
- 2.5V = reading of 512
- 5V = reading of 1023

**Uses:**
- Reading sensors that give variable output (temperature, light, sound)
- Reading potentiometers (knobs)
  ```cpp
  int sensorValue = analogRead(A0); // Read voltage on pin A0
  float voltage = sensorValue * (5.0 / 1023.0); // Convert to actual voltage
  ```

#### PWM Pins (marked with ~)
**What PWM is**: Rapidly switching a pin ON and OFF to simulate analog output

**Example**: To make an LED 50% bright:
- Turn ON for 5ms, OFF for 5ms, repeat
- Your eye sees it as half brightness

**Uses**: Controlling servo motors, LED brightness, motor speed
```cpp
analogWrite(9, 128); // 50% power to pin D9 (128 out of 255)
```

#### Power Pins
- **5V**: Provides 5 volts for powering components
- **3.3V**: Provides 3.3 volts for sensitive components
- **GND**: Ground (0V) - the reference point for all voltages
- **VIN**: Input voltage if powering Arduino from external source

**CRITICAL**: All components must share the same GND (ground) connection!

#### Communication Pins
- **SDA/SCL**: I2C communication (multiple sensors on 2 wires)
- **MOSI/MISO/SCK**: SPI communication (faster than I2C)
- **TX/RX**: Serial communication (talking to computers)

### Understanding Your Components

#### 1. Modulino Knob (Rotary Potentiometer)
**What it is**: A variable resistor that changes resistance when you turn it

**How it works**:
- Connected to 3.3V, GND, and analog pin
- As you rotate, voltage changes from 0V to 3.3V
- Arduino reads this voltage change

**In our project**: Selects operation mode (Heart/Lung/Calibration)

**Wiring**:
```
Knob → Arduino
VCC  → 3.3V (power)
GND  → GND (ground)
SIG  → A0 (signal to read)
```

#### 2. Modulino Distance Sensor (Ultrasonic)
**What it is**: Uses sound waves to measure distance (like bat echolocation)

**How it works**:
1. TRIG pin sends out ultrasonic pulse
2. Sound bounces off object and returns
3. ECHO pin receives the returned sound
4. Time difference = distance

**Physics**: Distance = (Time × Speed of Sound) ÷ 2

**In our project**: Ensures stethoscope is at correct distance from chest

**Wiring**:
```
Distance Sensor → Arduino
VCC  → 5V (needs more power)
GND  → GND
TRIG → D2 (trigger pulse)
ECHO → D3 (receive echo)
```

#### 3. Modulino Movement Sensor (PIR or Accelerometer)
**What it is**: Detects motion or movement

**Types**:
- **PIR (Passive Infrared)**: Detects heat movement (like security cameras)
- **Accelerometer**: Detects physical movement/vibration

**How it works**: Outputs HIGH when movement detected, LOW when still

**In our project**: Pauses recording if patient moves during examination

**Wiring**:
```
Movement Sensor → Arduino
VCC → 3.3V
GND → GND
OUT → D4 (digital signal)
```

#### 4. Modulino Thermo (Temperature Sensor)
**What it is**: Measures temperature digitally

**How it works**: Uses I2C communication to send temperature data

**I2C Explained**:
- **SDA**: Serial Data (actual information)
- **SCL**: Serial Clock (timing signal)
- Multiple sensors can share same SDA/SCL wires
- Each sensor has unique address

**In our project**: Detects fever as additional health indicator

**Wiring**:
```
Thermo Sensor → Arduino
VCC → 3.3V
GND → GND
SDA → SDA pin (data)
SCL → SCL pin (clock)
```

#### 5. Modulino Buzzer (Piezo Speaker)
**What it is**: Converts electrical signals to sound waves

**How it works**: 
- Piezo crystal vibrates when voltage applied
- Frequency of vibration = pitch of sound
- ON/OFF pattern = different beep patterns

**In our project**: Audio alerts for examination results

**Wiring**:
```
Buzzer → Arduino
VCC → 3.3V
GND → GND
SIG → D5 (PWM for different tones)
```

#### 6. Modulino Latch Relay (Electronic Switch)
**What it is**: Electrically controlled switch for high-power devices

**How it works**:
- Small control voltage (3.3V) controls large load (120V/240V)
- Like using a small button to turn on a big machine
- **Normally Open (NO)**: Switch open until activated
- **Normally Closed (NC)**: Switch closed until activated

**In our project**: Triggers external clinic alarm or light

**Wiring**:
```
Relay → Arduino
VCC → 5V (needs more power)
GND → GND
IN  → D6 (control signal)

Load Connection:
COM → One wire of device
NO  → Other wire of device
```

#### 7. Servo Motors (Precise Position Control)
**What they are**: Motors that can move to exact positions (0° to 180°)

**How they work**:
- PWM signal tells servo what angle to move to
- Internal feedback ensures accurate positioning
- Different pulse widths = different angles

**PWM Control**:
- 1ms pulse = 0°
- 1.5ms pulse = 90°
- 2ms pulse = 180°

**In our project**: 
- Servo 1: Progress indicator during recording
- Servo 2: Result display (angle indicates normal/abnormal)

**Wiring**:
```
Servo → Arduino
Red (Power)    → 5V
Brown (Ground) → GND
Orange (Signal) → D9 or D10 (PWM pin)
```

#### 8. Contact Microphone (Audio Input)
**What it is**: Converts sound vibrations to electrical signals

**MAX9814 Module Features**:
- **AGC**: Automatic Gain Control (adjusts volume automatically)
- **Amplifier**: Makes weak signals stronger
- **Frequency Response**: 20Hz-20kHz (covers heart sounds)

**How it works**:
1. Sound waves vibrate microphone diaphragm
2. Vibrations converted to electrical voltage changes
3. Amplifier boosts weak signal
4. Arduino reads voltage changes as audio

**In our project**: Captures heart and lung sounds through stethoscope

**Wiring Options**:

**Option A - Direct Analog**:
```
MAX9814 → Arduino
VCC  → 3.3V
GND  → GND
OUT  → A1 (analog input)
GAIN → 3.3V (maximum amplification)
```

**Option B - USB Audio (Better Quality)**:
```
MAX9814 → 3.5mm Jack → USB Audio Interface → Arduino USB Port
```

#### 9. Logitech Brio 100 (USB Camera)
**What it is**: Digital camera for video capture

**Specifications**:
- Resolution: Up to 1080p
- Frame rate: 30fps
- Interface: USB 2.0
- Auto-focus and auto-exposure

**In our project**: 
- Positioning guidance (shows where to place stethoscope)
- Demo visualization for judges
- Future: Patient presence detection

**Connection**: Simply plug into USB port on Linux side

### Voltage and Power Fundamentals

#### Understanding Voltage
**Voltage** is electrical pressure (like water pressure in pipes)
- **5V**: Standard Arduino logic level (HIGH state)
- **3.3V**: Lower voltage for sensitive components
- **0V (GND)**: Reference point (like sea level for altitude)

#### Current and Power
- **Current (Amps)**: How much electricity flows (like water flow rate)
- **Power (Watts)**: Voltage × Current (total energy used)

**Component Power Requirements**:
```
Arduino UNO Q:     5V, 2A    = 10W
Servo Motors:      5V, 0.5A  = 2.5W each
Modulino Sensors:  3.3V, 50mA = 0.16W total
Camera:           5V, 0.5A   = 2.5W
Total:            ~18W (need 20W+ power supply)
```

#### Why Ground (GND) is Critical
**Ground** is the reference point for all voltages. Think of it like this:
- If 5V is "mountain top" and GND is "sea level"
- All components must agree on where "sea level" is
- Without common ground, components can't communicate

**Always connect ALL GND pins together!**

### Communication Protocols Explained

#### Serial Communication (UART)
**What it is**: Sending data one bit at a time over a wire

**How it works**:
- **TX**: Transmit (sending data out)
- **RX**: Receive (getting data in)
- **Baud Rate**: Speed of communication (115200 = 115,200 bits per second)

**In our project**: MCU talks to Linux side via serial

#### I2C Communication
**What it is**: Multiple devices sharing 2 wires for communication

**How it works**:
- **SDA**: Serial Data (actual information)
- **SCL**: Serial Clock (timing synchronization)
- Each device has unique address (like house numbers)
- Master (Arduino) talks to slaves (sensors)

**Advantages**: Many sensors on just 2 wires

#### JSON Protocol (Our Choice)
**What it is**: Human-readable data format

**Example**:
```json
{
  "knob": 1,
  "distance": 5.2,
  "temperature": 36.8,
  "movement": false
}
```

**Why we use it**: Easy to read, debug, and extend

## 🧰 Tools and Materials You'll Need

### Essential Tools (Get These First!)
- **Multimeter**: For measuring voltage, current, resistance
  - **Why**: Troubleshoot connections, verify power levels
  - **Cost**: ₹500-1500
  - **How to use**: Set to DC voltage, touch probes to measure

- **Breadboard**: Solderless prototyping board
  - **Why**: Make temporary connections without soldering
  - **Cost**: ₹100-200
  - **How it works**: Internal metal strips connect holes in rows

- **Jumper Wires**: Pre-made connection wires
  - **Male-to-Male**: Connect breadboard to breadboard
  - **Male-to-Female**: Connect Arduino pins to breadboard
  - **Female-to-Female**: Connect modules to modules

- **USB-C Cable**: For powering and programming Arduino UNO Q
- **MicroSD Card**: For storing data and logs (optional)

### Understanding Breadboards
```
Breadboard Layout:
    + - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
    | Power Rails (connected vertically)                      |
    | + + + + + + + + + + + + + + + + + + + + + + + + + + + + |
    | - - - - - - - - - - - - - - - - - - - - - - - - - - - - |
    |                                                         |
    | a b c d e   f g h i j  ← Tie Points (connected horizontally)
    | 1 ○ ○ ○ ○ ○   ○ ○ ○ ○ ○  ← Row 1 (a1-e1 connected, f1-j1 connected)
    | 2 ○ ○ ○ ○ ○   ○ ○ ○ ○ ○  ← Row 2 (a2-e2 connected, f2-j2 connected)
    | 3 ○ ○ ○ ○ ○   ○ ○ ○ ○ ○  ← Each row is separate
    |   ...                     
    | 30○ ○ ○ ○ ○   ○ ○ ○ ○ ○  ← Row 30
    +-------------------------------------------+
```

**Key Points**:
- Rows are connected horizontally (a1-e1 are connected)
- Columns are NOT connected vertically
- Power rails run vertically along the sides
- Center gap separates left and right sides

### Components from Your Kit
- [ ] **Arduino UNO Q board** - Your dual-brain computer
- [ ] **Logitech Brio 100 webcam** - For positioning guidance
- [ ] **Modulino movement sensor** - Detects patient motion
- [ ] **Modulino distance sensor** - Measures stethoscope placement
- [ ] **Modulino thermo sensor** - Temperature measurement
- [ ] **Modulino knob** - Mode selection input
- [ ] **Modulino buzzer** - Audio alerts
- [ ] **Modulino latch relay** - External device control
- [ ] **2x servo motors** - Visual feedback displays
- [ ] **Male-to-male jumper wires** - Breadboard connections
- [ ] **Male-to-female jumper wires** - Arduino to component connections
- [ ] **USB-C cables and adapters** - Power and data

### Additional Components to Buy
- [ ] **MAX9814 electret microphone module** (₹200-300)
  - **What it does**: Captures audio with automatic gain control
  - **Why needed**: Heart/lung sound input
  - **Alternative**: Any amplified microphone module

- [ ] **Small breadboard or perfboard** (₹100)
  - **What it does**: Provides connection points for wiring
  - **Size needed**: Half-size breadboard (400 tie points)

- [ ] **3.5mm audio jack** (₹50)
  - **What it does**: Connects to stethoscope
  - **Type needed**: Stereo jack (TRS connector)

- [ ] **Resistors assortment** (₹100)
  - **Values needed**: 220Ω, 1kΩ, 10kΩ
  - **Why needed**: Current limiting, pull-up/pull-down

- [ ] **Capacitors** (₹50)
  - **Values needed**: 100nF ceramic, 100µF electrolytic
  - **Why needed**: Power filtering, noise reduction

- [ ] **Optional: 128x64 OLED display** (₹200)
  - **What it does**: Shows status without computer
  - **Interface**: I2C (uses SDA/SCL pins)

## 🏗️ System Architecture Deep Dive (CRITICAL UNDERSTANDING!)

### Why Dual-Core Architecture?
Traditional Arduino projects use one brain (microcontroller) for everything. But we need:
- **Fast responses** for safety (stop recording if patient moves)
- **Heavy computing** for AI analysis
- **Real-time control** for sensors and motors
- **Complex interfaces** like web dashboards

**Solution**: Use BOTH brains for what they do best!

### Detailed Brain Responsibilities:

#### **Linux Side (QRB2210 MPU) - The "Smart Brain"**
**What it handles**:
- **Audio capture and processing**: Recording heart sounds, filtering noise
- **AI inference**: Running TensorFlow Lite models for classification
- **Camera handling**: Video capture, positioning guidance
- **Web UI**: Dashboard, visualization, demo interface
- **High-level decision logic**: Combining all sensor data for final diagnosis
- **Data storage**: Logs, configuration, calibration data

**Why Linux is perfect for this**:
- **Multitasking**: Can do many things simultaneously
- **Rich libraries**: TensorFlow, OpenCV, Flask for web
- **File system**: Can save and load data
- **Network**: WiFi, Bluetooth, USB devices
- **Memory**: 2GB RAM for complex processing

**Think of it as**: The doctor's brain - analyzes, thinks, makes decisions

#### **MCU Side (STM32U585) - The "Fast Brain"**
**What it handles**:
- **Real-time I/O operations**: Reading sensors every millisecond
- **Modulino sensor polling**: Knob, distance, movement, temperature
- **Servo and actuator control**: Precise motor positioning
- **Buzzer control**: Immediate audio feedback
- **Relay control**: External device switching
- **Safety monitoring**: Emergency stops, error detection

**Why MCU is perfect for this**:
- **Real-time**: Guaranteed response times (microseconds)
- **Direct hardware control**: No operating system delays
- **Low power**: Efficient for continuous monitoring
- **Reliable**: Won't crash or freeze
- **Precise timing**: Critical for servo control and sensor reading

**Think of it as**: The nurse's reflexes - immediate responses, safety first

### Communication Between Brains
**Method**: Serial communication over USB CDC
**Protocol**: JSON messages (human-readable)
**Speed**: 115200 baud (115,200 bits per second)
**Direction**: Bidirectional (both can send and receive)

**Example Communication**:
```
MCU → Linux (every 100ms):
{
  "timestamp": 12345,
  "knob": 1,
  "distance": 5.2,
  "movement": false,
  "temperature": 36.8
}

Linux → MCU (when needed):
{
  "servo1": 90,
  "servo2": 45,
  "buzzer": "ON",
  "relay": "OFF"
}
```

**Why JSON?**
- **Human readable**: Easy to debug
- **Flexible**: Can add new fields easily
- **Standard**: Works with all programming languages
- **Self-describing**: Field names explain what data means

### Complete Data Flow Architecture
```
Physical World → Sensors → MCU → Linux → AI → Decision → Actuators → Physical World

Detailed Flow:
1. Patient places stethoscope on chest
2. Distance sensor (MCU) confirms correct placement
3. Movement sensor (MCU) ensures patient is still
4. Microphone (Linux) captures heart sounds
5. Audio processing (Linux) filters and extracts features
6. AI model (Linux) classifies sounds as normal/abnormal
7. Decision logic (Linux) combines audio + temperature + movement
8. Commands sent to MCU for servo/buzzer/relay response
9. Results displayed on web interface (Linux)
```

### Why This Architecture Wins Hackathons
1. **Professional approach**: Shows understanding of real-world constraints
2. **Scalable design**: Can add more sensors/features easily
3. **Fault tolerance**: If one brain fails, other can still function
4. **Performance**: Each brain optimized for its tasks
5. **Demonstrable**: Can show real-time responses during demo

👉 **Write this decision in `/docs/architecture.md` for judges to see your technical thinking!**

## 📋 Pre-Phase Checklist

### Components Verification
- [x] Arduino UNO Q board
- [x] Logitech Brio 100 webcam
- [x] Modulino movement sensor
- [x] Modulino distance sensor
- [x] Modulino thermo sensor
- [x] Modulino knob
- [x] Modulino buzzer
- [x] Modulino latch relay
- [x] 2x servo motors
- [x] Male-to-male jumper wires
- [x] Male-to-female jumper wires
- [x] USB-C cables and adapters

### Additional Components to Buy
- [ ] MAX9814 electret microphone module (₹200-300)
- [ ] Small breadboard or perfboard (₹100)
- [ ] 3.5mm audio jack (₹50)
- [ ] Optional: 128x64 OLED display (₹200)

## 🏗️ System Architecture Decision

### Dual-Core Split:
**Linux Side (QRB2210 MPU)**:
- Audio capture and processing
- Camera handling
- AI inference (TensorFlow Lite)
- Web UI hosting
- High-level decision logic
- Sensor data fusion

**MCU Side (STM32U585)**:
- Real-time I/O operations
- Modulino sensor polling
- Servo and actuator control
- Low-latency responses
- Safety monitoring

### Communication Protocol:
- **Method**: Serial over USB CDC
- **Format**: JSON messages
- **Baud Rate**: 115200
- **Direction**: Bidirectional

## 🔌 Pin Mapping & Connections

### MCU Side Connections (STM32U585)

| Component | Pin | Type | Purpose |
|-----------|-----|------|---------|
| Modulino Knob | A0 | Analog Input | Mode selection (0-2) |
| Modulino Distance | D2, D3 | Digital I/O | Trigger/Echo pins |
| Modulino Movement | D4 | Digital Input | Motion detection |
| Modulino Thermo | SDA, SCL | I2C | Temperature reading |
| Modulino Buzzer | D5 | PWM Output | Audio alerts |
| Modulino Relay | D6 | Digital Output | External trigger |
| Servo 1 (Progress) | D9 | PWM Output | Progress indication |
| Servo 2 (Result) | D10 | PWM Output | Result display |
| Status LED | D13 | Digital Output | System status |

### Linux Side Connections (QRB2210)

| Component | Interface | Device Path | Purpose |
|-----------|-----------|-------------|---------|
| USB Webcam | USB 2.0 | /dev/video0 | Positioning guidance |
| Audio Input | USB Audio | /dev/snd/ | Contact microphone |
| MCU Communication | USB CDC | /dev/ttyACM0 | Serial to MCU |

### Power Distribution

- **5V Rail**: Servos, relay module, distance sensor
- **3.3V Rail**: Most Modulino sensors, microphone module
- **GND**: Common ground for all components

**⚠️ IMPORTANT**: Ensure all components share common ground to prevent communication issues.

## 🔧 Step-by-Step Implementation (Beginner-Friendly!)

### STEP 1: Arduino UNO Q System Verification

#### 1.1 First Power-On (Your First Moment of Truth!)
**What you're doing**: Checking if your Arduino UNO Q is alive and healthy

**Physical Steps**:
1. **Unbox carefully**: Arduino UNO Q is sensitive to static electricity
   - Touch a metal object first to discharge static
   - Handle by edges, avoid touching components

2. **Inspect the board**: Look for any obvious damage
   - **Check for**: Bent pins, cracked components, loose connections
   - **Normal**: Small components, shiny metal traces, clean solder joints

3. **Connect USB-C cable**: 
   - Use the cable that came with your kit
   - Connect to your computer's USB port
   - **You should see**: Power LED lights up (usually red or green)

4. **Wait for boot**: Linux takes time to start
   - **First boot**: 90-120 seconds (be patient!)
   - **Subsequent boots**: 60-90 seconds
   - **You'll hear**: Possibly some quiet fan noise

**What's happening inside**:
- Power circuits activate
- Linux kernel loads from storage
- Network interfaces initialize
- USB gadget mode activates

#### 1.2 Network Connection Test (Connecting to Your Arduino)
**What you're doing**: Establishing communication with the Linux side

**On Windows**:
1. **Open Device Manager**:
   - Right-click "This PC" → Properties → Device Manager
   - Look under "Network adapters"
   - **You should see**: "USB Ethernet Gadget" or "RNDIS/Ethernet Gadget"

2. **Find the IP address**:
   - Open Command Prompt (cmd)
   - Type: `ipconfig`
   - Look for adapter with name containing "USB" or "RNDIS"
   - **Common IPs**: 192.168.7.2, 192.168.42.1, or 10.42.0.1

3. **Test web access**:
   - Open web browser
   - Try: `http://192.168.7.2` (most common)
   - **Success**: You see a web page (might be basic)
   - **Failure**: "This site can't be reached" - try other IP addresses

**Troubleshooting Network Issues**:
- **No USB device**: Try different USB cable or port
- **Device detected but no network**: Wait longer, Linux might still be booting
- **Can't access web**: Try `http://192.168.42.1` or `http://10.42.0.1`

#### 1.3 SSH Access Verification (Command Line Access)
**What SSH is**: Secure Shell - a way to type commands directly on the Arduino's Linux system

**Why you need it**: To install software, run programs, and debug issues

**How to connect**:

**On Windows (using built-in SSH)**:
1. Open Command Prompt or PowerShell
2. Type: `ssh root@192.168.7.2`
3. **First time**: You'll see a security warning - type "yes"
4. **Password**: Usually none (just press Enter) or try "arduino"

**On Windows (using PuTTY if SSH doesn't work)**:
1. Download PuTTY from putty.org
2. Host Name: 192.168.7.2
3. Port: 22
4. Connection Type: SSH
5. Click "Open"

**Success looks like**:
```bash
root@arduino-uno-q:~# 
```

**What this means**: You're now typing commands directly on the Arduino's Linux system!

#### 1.4 System Information Gathering (Know Your Hardware)
**What you're doing**: Documenting your system's capabilities

**Commands to run** (type these in SSH):

```bash
# Check Linux version
uname -a
# Output example: Linux arduino-uno-q 5.15.0 #1 SMP aarch64 GNU/Linux

# Check available storage
df -h
# Shows how much space you have for programs and data

# Check available memory
free -h
# Shows RAM usage (you have 2GB total)

# Check CPU information
lscpu
# Shows your quad-core ARM processor details

# Check connected USB devices
lsusb
# Shows camera, audio devices, etc.

# Check network interfaces
ip addr show
# Shows all network connections
```

**Document everything**: Create a file with this information for troubleshooting later

#### 1.5 System Health Check
**What you're doing**: Making sure everything is working properly

**Temperature check**:
```bash
# Check CPU temperature (should be under 70°C)
cat /sys/class/thermal/thermal_zone*/temp
```

**Storage check**:
```bash
# Make sure you have enough space (need at least 2GB free)
df -h /
```

**Process check**:
```bash
# See what programs are running
top
# Press 'q' to quit
```

**Create system info file**:
```bash
# Create a file with your system information
nano /root/system_info.txt
```

Type in the information you gathered, then:
- Press `Ctrl+X` to exit
- Press `Y` to save
- Press `Enter` to confirm filename

## 🔧 Common Hardware Troubleshooting

### Distance Sensor Issues
- **Problem**: Readings are always 0 or very erratic.
- **Solution**: 
  - Ensure VCC is connected to **5V**, not 3.3V.
  - Check TRIG and ECHO pin connections. 
  - Avoid soft surfaces (fabric, carpet) that absorb sound.
  - **Reflections**: Ensure the sensor is perpendicular to the target surface.

### Servo Jitter
- **Problem**: Servos shake or make noise when they should be still.
- **Solution**:
  - **Power**: Servos draw a lot of current. If powering from USB, it might not be enough. Try an external 5V power supply (connect grounds!).
  - **Code**: Detach the servo when not moving (`servo.detach()`) and reattach only when needed.

### Camera Not Detected
- **Problem**: `lsusb` doesn't show the camera or `/dev/video0` is missing.
- **Solution**:
  - **Cable**: Use a high-quality USB cable. Some charging cables don't transmit data.
  - **Power**: The camera might need more power than the port provides. Try a powered USB hub.
  - **Permissions**: Run commands with `sudo` or check user permissions for video devices.

### I2C Device Not Found
- **Problem**: `scanI2CDevices()` returns 0 devices.
- **Solution**:
  - **Wiring**: SCL and SDA must be correct. Swap them and try again if unsure.
  - **Pull-up Resistors**: I2C often needs 4.7kΩ resistors from SDA and SCL to 3.3V. Many modules have these built-in, but some don't.
  - **Address**: Verify the device address in your code matches the datasheet.

### General Stability
- **Problem**: System restarts randomly or sensors stop working.
- **Solution**:
  - **Grounding**: This is the #1 cause of issues. Ensure **ALL** GND pins from all components share a common connection.


### STEP 2: Individual Component Testing (One at a Time!)

**CRITICAL RULE**: Test ONE component at a time. If you connect everything at once and something doesn't work, you won't know which component is the problem!

#### 2.1 Modulino Knob Test (Your First Sensor!)

**What this component does**: 
- Rotary potentiometer (variable resistor)
- Changes resistance as you turn it
- Arduino reads this as changing voltage

**Physical Connection**:
```
Modulino Knob → Arduino UNO Q
Red wire (VCC) → 3.3V pin
Black wire (GND) → GND pin
Yellow wire (SIG) → A0 pin
```

**How to make connections**:
1. **Power OFF**: Always disconnect power when wiring
2. **Use breadboard**: Insert wires into breadboard first
3. **Use jumper wires**: Connect breadboard to Arduino pins
4. **Double-check**: VCC to 3.3V, GND to GND, Signal to A0

**Test Code** (Upload this to MCU side):

Create file: `firmware/tests/knob_test.ino`
```cpp
// Knob Test Program
// This program reads the knob position and prints it

void setup() {
  // Start serial communication at 115200 baud
  Serial.begin(115200);
  
  // Wait for serial connection
  while (!Serial) {
    delay(10);
  }
  
  Serial.println("=== KNOB TEST STARTING ===");
  Serial.println("Turn the knob and watch the values change");
  Serial.println("Values should be 0-1023");
  Serial.println("Mode 0: 0-341, Mode 1: 342-682, Mode 2: 683-1023");
  Serial.println();
}

void loop() {
  // Read the analog value from pin A0
  int rawValue = analogRead(A0);
  
  // Convert to mode (0, 1, or 2)
  int mode = map(rawValue, 0, 1023, 0, 2);
  
  // Calculate voltage (for understanding)
  float voltage = rawValue * (3.3 / 1023.0);
  
  // Print all information
  Serial.print("Raw Value: ");
  Serial.print(rawValue);
  Serial.print(" | Voltage: ");
  Serial.print(voltage, 2);
  Serial.print("V | Mode: ");
  Serial.print(mode);
  
  // Add mode description
  if (mode == 0) {
    Serial.println(" (Heart Analysis)");
  } else if (mode == 1) {
    Serial.println(" (Lung Analysis)");
  } else {
    Serial.println(" (Calibration)");
  }
  
  delay(500); // Wait half a second before next reading
}
```

**How to upload and test**:
1. **Connect Arduino to computer** via USB
2. **Open Arduino IDE** (download from arduino.cc if needed)
3. **Select board**: Tools → Board → Arduino UNO Q
4. **Select port**: Tools → Port → (your Arduino's port)
5. **Copy and paste** the code above
6. **Click Upload** button (arrow icon)
7. **Open Serial Monitor**: Tools → Serial Monitor
8. **Set baud rate**: 115200 in dropdown

**Success criteria**:
- [ ] Values change smoothly when you turn knob
- [ ] No sudden jumps or erratic readings
- [ ] Mode changes clearly at different positions
- [ ] Values stay stable when knob is not moving

**Troubleshooting**:
- **No readings**: Check power connections (3.3V and GND)
- **Erratic readings**: Check signal wire connection to A0
- **Values don't change**: Knob might be broken or not connected
- **Upload fails**: Check board and port selection

#### 2.2 Modulino Distance Sensor Test (Ultrasonic Magic!)

**What this component does**:
- Sends out ultrasonic sound pulse (like bat echolocation)
- Measures time for echo to return
- Calculates distance based on sound speed

**Physics behind it**:
- Sound travels at ~343 meters/second in air
- Distance = (Time × Speed) ÷ 2 (divide by 2 because sound travels to object and back)

**Physical Connection**:
```
Distance Sensor → Arduino UNO Q
VCC (Red) → 5V pin (needs more power than 3.3V)
GND (Black) → GND pin
TRIG (Blue) → D2 pin (sends trigger pulse)
ECHO (Green) → D3 pin (receives echo)
```

**Test Code**:

Create file: `firmware/tests/distance_test.ino`
```cpp
// Distance Sensor Test Program
// This program measures distance using ultrasonic sensor

const int trigPin = 2;  // Trigger pin connected to D2
const int echoPin = 3;  // Echo pin connected to D3

void setup() {
  Serial.begin(115200);
  
  // Set pin modes
  pinMode(trigPin, OUTPUT);  // Trigger sends signal OUT
  pinMode(echoPin, INPUT);   // Echo receives signal IN
  
  Serial.println("=== DISTANCE SENSOR TEST ===");
  Serial.println("Place objects at different distances");
  Serial.println("Optimal range: 2cm to 400cm");
  Serial.println("For stethoscope: 3-8cm is ideal");
  Serial.println();
}

void loop() {
  // Send trigger pulse
  digitalWrite(trigPin, LOW);   // Make sure trigger is off
  delayMicroseconds(2);         // Wait 2 microseconds
  digitalWrite(trigPin, HIGH);  // Send 10 microsecond pulse
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);   // Turn off pulse
  
  // Measure echo time
  long duration = pulseIn(echoPin, HIGH);
  
  // Calculate distance in centimeters
  // Speed of sound = 343 m/s = 0.0343 cm/microsecond
  // Distance = (duration * 0.0343) / 2
  // Simplified: distance = duration / 29.1
  long distance = (duration / 2) / 29.1;
  
  // Print results
  Serial.print("Duration: ");
  Serial.print(duration);
  Serial.print(" microseconds | Distance: ");
  Serial.print(distance);
  Serial.print(" cm");
  
  // Add placement guidance
  if (distance < 2) {
    Serial.println(" - TOO CLOSE!");
  } else if (distance >= 2 && distance <= 8) {
    Serial.println(" - PERFECT for stethoscope");
  } else if (distance > 8 && distance <= 20) {
    Serial.println(" - Acceptable");
  } else if (distance > 20) {
    Serial.println(" - Too far");
  } else {
    Serial.println(" - Out of range");
  }
  
  delay(500); // Wait half second between measurements
}
```

**Testing procedure**:
1. Upload code to Arduino
2. Open Serial Monitor
3. **Test with ruler**: Place objects at known distances
4. **Verify accuracy**: Readings should match ruler measurements
5. **Test range**: Try 2cm, 5cm, 10cm, 20cm distances

**Success criteria**:
- [ ] Accurate distance readings (within 1cm of actual)
- [ ] Stable readings when object is stationary
- [ ] Responds quickly to distance changes
- [ ] Works in 3-8cm range (critical for our project)

**Troubleshooting**:
- **Always reads 0**: Check power (needs 5V, not 3.3V)
- **Erratic readings**: Check trigger and echo wire connections
- **No response**: Sensor might be damaged or wrong pins
- **Inaccurate**: Calibrate by testing with ruler at known distances

#### 2.3 Modulino Movement Sensor Test (Motion Detection)

**What this component does**:
- **PIR (Passive Infrared)**: Detects heat movement from living beings
- **Accelerometer**: Detects physical vibration or movement
- Outputs HIGH when movement detected, LOW when still

**Why we need it**: If patient moves during heart sound recording, we get noise and false readings

**Physical Connection**:
```
Movement Sensor → Arduino UNO Q
VCC (Red) → 3.3V pin
GND (Black) → GND pin
OUT (Yellow) → D4 pin (digital input)
```

**Test Code**:

Create file: `firmware/tests/movement_test.ino`
```cpp
// Movement Sensor Test Program
// Detects when patient or device moves

const int motionPin = 4;  // Motion sensor connected to D4
int lastMotionState = LOW;
unsigned long motionStartTime = 0;
unsigned long stillStartTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(motionPin, INPUT);
  
  Serial.println("=== MOVEMENT SENSOR TEST ===");
  Serial.println("Move around and watch for detection");
  Serial.println("Sensor needs 30-60 seconds to calibrate");
  Serial.println("Wait for 'Ready' message before testing");
  Serial.println();
  
  // Calibration period
  Serial.println("Calibrating sensor...");
  for (int i = 30; i > 0; i--) {
    Serial.print("Wait ");
    Serial.print(i);
    Serial.println(" seconds (stay still)");
    delay(1000);
  }
  Serial.println("Sensor ready! Start moving to test.");
  Serial.println();
}

void loop() {
  int motionState = digitalRead(motionPin);
  
  // Check for state change
  if (motionState != lastMotionState) {
    if (motionState == HIGH) {
      // Motion detected
      motionStartTime = millis();
      Serial.println("🚨 MOTION DETECTED! Recording would PAUSE");
    } else {
      // Motion stopped
      stillStartTime = millis();
      unsigned long motionDuration = stillStartTime - motionStartTime;
      Serial.print("✅ Motion stopped. Duration: ");
      Serial.print(motionDuration);
      Serial.println(" ms");
    }
    lastMotionState = motionState;
  }
  
  // Show current state every 2 seconds
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 2000) {
    if (motionState == HIGH) {
      Serial.println("Status: MOTION - Recording paused");
    } else {
      unsigned long stillDuration = millis() - stillStartTime;
      Serial.print("Status: STILL for ");
      Serial.print(stillDuration / 1000);
      Serial.println(" seconds - OK to record");
    }
    lastPrint = millis();
  }
  
  delay(100); // Check 10 times per second
}
```

**Testing procedure**:
1. Upload code and open Serial Monitor
2. **Wait for calibration**: Don't move for 30 seconds
3. **Test motion detection**: Wave hand near sensor
4. **Test stillness detection**: Stay completely still
5. **Test sensitivity**: Try small movements vs large movements

**Success criteria**:
- [ ] Detects when you move around the sensor
- [ ] Returns to LOW when you stop moving
- [ ] Reasonable sensitivity (not too sensitive to small vibrations)
- [ ] Quick response time (under 1 second)

#### 2.4 Modulino Thermo Test (Temperature Measurement)

**What this component does**:
- Measures temperature digitally (no analog conversion needed)
- Uses I2C communication protocol
- Provides accurate temperature readings in Celsius

**Why we need it**: Fever detection adds important context to heart/lung analysis

**Physical Connection**:
```
Thermo Sensor → Arduino UNO Q
VCC (Red) → 3.3V pin
GND (Black) → GND pin
SDA (Blue) → SDA pin (I2C data line)
SCL (Green) → SCL pin (I2C clock line)
```

**Understanding I2C**:
- **I2C**: Inter-Integrated Circuit communication
- **SDA**: Serial Data (actual temperature data)
- **SCL**: Serial Clock (timing synchronization)
- **Address**: Each I2C device has unique address (like house number)
- **Multiple devices**: Can connect many sensors to same SDA/SCL wires

**Test Code**:

Create file: `firmware/tests/thermo_test.ino`
```cpp
// Temperature Sensor Test Program
// Reads temperature via I2C communication

#include <Wire.h>

// I2C address of temperature sensor (common addresses: 0x48, 0x49, 0x4A, 0x4B)
// You might need to scan for the correct address
const int TEMP_SENSOR_ADDRESS = 0x48;

void setup() {
  Serial.begin(115200);
  Wire.begin(); // Initialize I2C communication
  
  Serial.println("=== TEMPERATURE SENSOR TEST ===");
  Serial.println("Scanning for I2C devices...");
  
  // Scan for I2C devices
  scanI2CDevices();
  
  Serial.println("Starting temperature readings...");
  Serial.println("Normal room temperature: 20-25°C");
  Serial.println("Body temperature: 36-37°C");
  Serial.println("Fever threshold: >37.5°C");
  Serial.println();
}

void loop() {
  float temperature = readTemperature();
  
  if (temperature != -999) { // -999 indicates error
    Serial.print("Temperature: ");
    Serial.print(temperature, 1);
    Serial.print("°C | ");
    Serial.print((temperature * 9.0/5.0) + 32, 1);
    Serial.print("°F");
    
    // Add health context
    if (temperature < 35.0) {
      Serial.println(" - Too low (check sensor)");
    } else if (temperature >= 35.0 && temperature < 37.5) {
      Serial.println(" - Normal");
    } else if (temperature >= 37.5 && temperature < 39.0) {
      Serial.println(" - Fever detected! 🌡️");
    } else if (temperature >= 39.0) {
      Serial.println(" - High fever! 🚨");
    } else {
      Serial.println(" - Too high (check sensor)");
    }
  } else {
    Serial.println("Error reading temperature sensor");
  }
  
  delay(2000); // Read every 2 seconds
}

void scanI2CDevices() {
  byte error, address;
  int deviceCount = 0;
  
  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      deviceCount++;
    }
  }
  
  if (deviceCount == 0) {
    Serial.println("No I2C devices found. Check wiring!");
  } else {
    Serial.print("Found ");
    Serial.print(deviceCount);
    Serial.println(" I2C device(s)");
  }
  Serial.println();
}

float readTemperature() {
  // This is a generic I2C temperature reading
  // You might need to modify this based on your specific sensor
  
  Wire.beginTransmission(TEMP_SENSOR_ADDRESS);
  Wire.write(0x00); // Temperature register
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    return -999; // Error code
  }
  
  Wire.requestFrom(TEMP_SENSOR_ADDRESS, 2);
  
  if (Wire.available() >= 2) {
    byte msb = Wire.read();
    byte lsb = Wire.read();
    
    // Convert to temperature (this varies by sensor)
    // This is for a typical 12-bit temperature sensor
    int rawTemp = (msb << 8) | lsb;
    float temperature = rawTemp * 0.0625; // 0.0625°C per bit for 12-bit sensor
    
    return temperature;
  }
  
  return -999; // Error code
}
```

**Testing procedure**:
1. Upload code and open Serial Monitor
2. **Check I2C scan**: Should find device at some address
3. **Test room temperature**: Should read 20-25°C
4. **Test body temperature**: Touch sensor with finger (should increase)
5. **Test stability**: Readings should be consistent

**Success criteria**:
- [ ] I2C device detected during scan
- [ ] Reasonable temperature readings (not -999 error)
- [ ] Temperature changes when you touch/heat the sensor
- [ ] Stable readings when temperature is constant

**Troubleshooting**:
- **No I2C device found**: Check SDA/SCL connections
- **Error readings (-999)**: Wrong I2C address or faulty sensor
- **Unrealistic temperatures**: Sensor might need calibration
- **Unstable readings**: Check power supply and connections

### STEP 3: Actuator Testing (Making Things Move and Sound!)

**What are actuators?**: Components that DO things - make sounds, move objects, switch devices

#### 3.1 Modulino Buzzer Test (Audio Feedback)

**What this component does**:
- **Piezo buzzer**: Uses piezoelectric crystal that vibrates when voltage applied
- **Frequency control**: Different frequencies = different pitches
- **Pattern control**: ON/OFF patterns create different alert types

**How piezo works**:
- Apply voltage → crystal deforms
- Remove voltage → crystal returns to shape
- Rapid voltage changes → vibrations → sound waves

**Physical Connection**:
```
Buzzer Module → Arduino UNO Q
VCC (Red) → 3.3V pin
GND (Black) → GND pin
SIG (Yellow) → D5 pin (PWM capable)
```

**Test Code**:

Create file: `firmware/tests/buzzer_test.ino`
```cpp
// Buzzer Test Program
// Tests different sounds for different alerts

const int buzzerPin = 5; // PWM pin for tone control

void setup() {
  Serial.begin(115200);
  pinMode(buzzerPin, OUTPUT);
  
  Serial.println("=== BUZZER TEST ===");
  Serial.println("Testing different alert patterns");
  Serial.println("Listen for different sounds");
  Serial.println();
}

void loop() {
  // Test 1: Single beep (Normal result)
  Serial.println("Test 1: Single beep - Normal result");
  singleBeep();
  delay(2000);
  
  // Test 2: Double beep (Warning)
  Serial.println("Test 2: Double beep - Warning");
  doubleBeep();
  delay(2000);
  
  // Test 3: Continuous beep (Alert/Abnormal)
  Serial.println("Test 3: Continuous beep - Alert!");
  continuousBeep();
  delay(3000);
  
  // Test 4: Different frequencies
  Serial.println("Test 4: Different frequencies");
  frequencyTest();
  delay(2000);
  
  Serial.println("Test cycle complete. Repeating...");
  Serial.println();
  delay(2000);
}

void singleBeep() {
  // One short beep at 1000Hz
  tone(buzzerPin, 1000, 200); // frequency, duration
  delay(300); // Wait for beep to finish
}

void doubleBeep() {
  // Two short beeps
  tone(buzzerPin, 1000, 150);
  delay(200);
  tone(buzzerPin, 1000, 150);
  delay(300);
}

void continuousBeep() {
  // Continuous beeping for 2 seconds
  for (int i = 0; i < 10; i++) {
    tone(buzzerPin, 1500, 100);
    delay(150);
  }
}

void frequencyTest() {
  // Test different frequencies
  int frequencies[] = {500, 750, 1000, 1500, 2000};
  
  for (int i = 0; i < 5; i++) {
    Serial.print("Playing ");
    Serial.print(frequencies[i]);
    Serial.println(" Hz");
    
    tone(buzzerPin, frequencies[i], 300);
    delay(500);
  }
}
```

**Testing procedure**:
1. Upload code and open Serial Monitor
2. **Listen carefully**: Each test should sound different
3. **Volume check**: Should be audible but not painfully loud
4. **Pattern recognition**: Can you distinguish between alert types?

**Success criteria**:
- [ ] Clear, audible beep sounds
- [ ] Different patterns clearly distinguishable
- [ ] No crackling or distortion
- [ ] Consistent volume across different frequencies

#### 3.2 Modulino Latch Relay Test (Electronic Switch)

**What this component does**:
- **Electronic switch**: Controls high-power devices with low-power signal
- **Isolation**: Separates Arduino circuits from external devices
- **Safety**: Protects Arduino from high voltage/current

**How relays work**:
1. Small current through coil creates magnetic field
2. Magnetic field pulls metal switch contacts together
3. External circuit completes through switch contacts
4. When coil power removed, spring opens contacts

**Relay terminology**:
- **COM**: Common terminal (like center of switch)
- **NO**: Normally Open (disconnected when relay OFF)
- **NC**: Normally Closed (connected when relay OFF)
- **Coil**: Control circuit (connected to Arduino)

**Physical Connection**:
```
Relay Module → Arduino UNO Q
VCC (Red) → 5V pin (relays need more power)
GND (Black) → GND pin
IN (Yellow) → D6 pin (control signal)

For testing (safe low voltage):
COM → One wire of LED + resistor
NO → Other wire of LED + resistor
Power LED circuit with 3V battery
```

**Test Code**:

Create file: `firmware/tests/relay_test.ino`
```cpp
// Relay Test Program
// Tests electronic switching capability

const int relayPin = 6;
bool relayState = false;

void setup() {
  Serial.begin(115200);
  pinMode(relayPin, OUTPUT);
  
  // Start with relay OFF
  digitalWrite(relayPin, LOW);
  
  Serial.println("=== RELAY TEST ===");
  Serial.println("Listen for clicking sounds");
  Serial.println("If you connected a test LED, it should turn on/off");
  Serial.println("NEVER connect high voltage during testing!");
  Serial.println();
}

void loop() {
  // Turn relay ON
  Serial.println("Relay ON - Should hear CLICK");
  digitalWrite(relayPin, HIGH);
  relayState = true;
  printRelayStatus();
  delay(2000);
  
  // Turn relay OFF
  Serial.println("Relay OFF - Should hear CLICK");
  digitalWrite(relayPin, LOW);
  relayState = false;
  printRelayStatus();
  delay(2000);
  
  // Rapid switching test
  Serial.println("Rapid switching test...");
  for (int i = 0; i < 5; i++) {
    digitalWrite(relayPin, HIGH);
    delay(200);
    digitalWrite(relayPin, LOW);
    delay(200);
  }
  
  Serial.println("Test cycle complete");
  Serial.println();
  delay(3000);
}

void printRelayStatus() {
  Serial.print("Relay state: ");
  if (relayState) {
    Serial.println("CLOSED (conducting)");
    Serial.println("COM and NO are connected");
  } else {
    Serial.println("OPEN (not conducting)");
    Serial.println("COM and NO are disconnected");
  }
}
```

**Testing procedure**:
1. Upload code and open Serial Monitor
2. **Listen for clicks**: Should hear distinct clicking sound
3. **Visual test**: If LED connected, should turn on/off
4. **Timing test**: Clicks should match Serial Monitor messages

**Success criteria**:
- [ ] Audible click when relay switches
- [ ] LED (if connected) turns on/off with relay
- [ ] Consistent switching - no missed operations
- [ ] No sparking or burning smell

**⚠️ SAFETY WARNING**: Never connect high voltage (120V/240V) during testing! Use only low voltage (3-12V) test circuits.

#### 3.3 Servo Motors Test (Precise Position Control)

**What servo motors do**:
- **Precise positioning**: Can move to exact angles (0° to 180°)
- **Feedback control**: Internal sensor ensures accurate positioning
- **Hold position**: Actively maintains position against external force

**How servos work**:
1. **PWM signal**: Pulse width tells servo what angle to move to
2. **Internal control**: Servo compares actual position to desired position
3. **Motor correction**: Internal motor adjusts until position matches
4. **Continuous correction**: Servo constantly maintains position

**PWM timing for servos**:
- **1.0ms pulse** = 0° position
- **1.5ms pulse** = 90° position (center)
- **2.0ms pulse** = 180° position
- **Pulse period**: 20ms (50Hz frequency)

**Physical Connection**:
```
Servo 1 (Progress Indicator) → Arduino UNO Q
Red wire (Power) → 5V pin
Brown/Black wire (Ground) → GND pin
Orange/Yellow wire (Signal) → D9 pin (PWM)

Servo 2 (Result Display) → Arduino UNO Q
Red wire (Power) → 5V pin
Brown/Black wire (Ground) → GND pin
Orange/Yellow wire (Signal) → D10 pin (PWM)
```

**Test Code**:

Create file: `firmware/tests/servo_test.ino`
```cpp
// Servo Test Program
// Tests precise position control

#include <Servo.h>

Servo progressServo;  // Servo 1 - shows progress
Servo resultServo;    // Servo 2 - shows results

void setup() {
  Serial.begin(115200);
  
  // Attach servos to pins
  progressServo.attach(9);
  resultServo.attach(10);
  
  Serial.println("=== SERVO TEST ===");
  Serial.println("Watch servos move to different positions");
  Serial.println("Servos should move smoothly without jitter");
  Serial.println();
  
  // Move to center position
  progressServo.write(90);
  resultServo.write(90);
  delay(1000);
}

void loop() {
  // Test 1: Progress servo sweep (0° to 180°)
  Serial.println("Test 1: Progress servo sweep (simulating capture progress)");
  for (int angle = 0; angle <= 180; angle += 10) {
    progressServo.write(angle);
    Serial.print("Progress: ");
    Serial.print(angle);
    Serial.print("° (");
    Serial.print((angle * 100) / 180);
    Serial.println("% complete)");
    delay(200);
  }
  delay(1000);
  
  // Test 2: Result servo positions
  Serial.println("Test 2: Result servo - different result positions");
  
  // Normal result (45°)
  Serial.println("Result: NORMAL (45°)");
  resultServo.write(45);
  delay(2000);
  
  // Warning result (90°)
  Serial.println("Result: WARNING (90°)");
  resultServo.write(90);
  delay(2000);
  
  // Abnormal result (135°)
  Serial.println("Result: ABNORMAL (135°)");
  resultServo.write(135);
  delay(2000);
  
  // Test 3: Precision test
  Serial.println("Test 3: Precision test - small movements");
  for (int angle = 85; angle <= 95; angle++) {
    resultServo.write(angle);
    Serial.print("Fine position: ");
    Serial.print(angle);
    Serial.println("°");
    delay(300);
  }
  
  // Test 4: Speed test
  Serial.println("Test 4: Speed test - rapid movements");
  for (int i = 0; i < 5; i++) {
    progressServo.write(0);
    delay(500);
    progressServo.write(180);
    delay(500);
  }
  
  // Return to center
  Serial.println("Returning to center positions");
  progressServo.write(90);
  resultServo.write(90);
  
  Serial.println("Test cycle complete");
  Serial.println();
  delay(3000);
}
```

**Testing procedure**:
1. Upload code and open Serial Monitor
2. **Watch movement**: Servos should move smoothly to each position
3. **Check accuracy**: Servo should stop at commanded position
4. **Listen for noise**: Should be quiet operation, no grinding
5. **Test holding**: Try gently pushing servo - should resist movement

**Success criteria**:
- [ ] Smooth movement without jitter or jumping
- [ ] Accurate positioning (servo stops where commanded)
- [ ] Quiet operation (no grinding or excessive noise)
- [ ] Strong holding torque (resists manual movement)
- [ ] Consistent performance across full range

**Troubleshooting**:
- **Servo jitters**: Check power supply (servos need stable 5V)
- **Doesn't move**: Check signal wire connection to PWM pin
- **Moves to wrong position**: Servo might be damaged or need calibration
- **Weak holding**: Insufficient power or damaged servo gears

#### 2.3 Modulino Movement Sensor Test

**Wiring**:
- VCC → 3.3V
- GND → GND
- OUT → D4

**Test Code** (`firmware/tests/movement_test.ino`):
```cpp
const int motionPin = 4;

void setup() {
  Serial.begin(115200);
  pinMode(motionPin, INPUT);
  Serial.println("Movement Sensor Test Starting...");
}

void loop() {
  int motionState = digitalRead(motionPin);
  
  if (motionState == HIGH) {
    Serial.println("MOTION DETECTED");
  } else {
    Serial.println("No motion");
  }
  
  delay(200);
}
```

**Success Criteria**:
- [ ] Detects board movement reliably
- [ ] Stable LOW when stationary
- [ ] Quick response to motion
- [ ] Define motion threshold for pause logic

#### 2.4 Modulino Thermo Sensor Test

**Wiring** (I2C):
- VCC → 3.3V
- GND → GND
- SDA → SDA pin
- SCL → SCL pin

**Test Code** (`firmware/tests/thermo_test.ino`):
```cpp
#include <Wire.h>

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Serial.println("Temperature Sensor Test Starting...");
}

void loop() {
  // Implementation depends on specific sensor
  // Common sensors: DS18B20, DHT22, or I2C temp sensor
  
  float temperature = readTemperature();
  
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.println(" °C");
  
  delay(1000);
}

float readTemperature() {
  // Implement based on your specific sensor
  // Return temperature in Celsius
  return 25.0; // Placeholder
}
```

**Success Criteria**:
- [ ] Accurate temperature readings
- [ ] Reasonable room temperature (~20-25°C)
- [ ] Stable readings over time
- [ ] Define fever threshold (>37.5°C)

### STEP 3: Actuator Testing

#### 3.1 Servo Motors Test

**Wiring**:
- Servo 1: Signal → D9, Power → 5V, Ground → GND
- Servo 2: Signal → D10, Power → 5V, Ground → GND

**Test Code** (`firmware/tests/servo_test.ino`):
```cpp
#include <Servo.h>

Servo progressServo;
Servo resultServo;

void setup() {
  Serial.begin(115200);
  progressServo.attach(9);
  resultServo.attach(10);
  Serial.println("Servo Test Starting...");
}

void loop() {
  // Test progress servo (0-180 sweep)
  Serial.println("Testing Progress Servo...");
  for (int pos = 0; pos <= 180; pos += 10) {
    progressServo.write(pos);
    delay(100);
  }
  
  // Test result servo (specific positions)
  Serial.println("Testing Result Servo...");
  resultServo.write(45);  // Green position
  delay(1000);
  resultServo.write(135); // Red position
  delay(1000);
  resultServo.write(90);  // Neutral position
  delay(1000);
}
```

**Success Criteria**:
- [ ] Smooth servo movement without jitter
- [ ] Accurate positioning
- [ ] No power supply issues
- [ ] Define position mapping (0°=Green, 90°=Neutral, 180°=Red)

#### 3.2 Buzzer Test

**Wiring**:
- Positive → D5
- Negative → GND

**Test Code** (`firmware/tests/buzzer_test.ino`):
```cpp
const int buzzerPin = 5;

void setup() {
  Serial.begin(115200);
  pinMode(buzzerPin, OUTPUT);
  Serial.println("Buzzer Test Starting...");
}

void loop() {
  Serial.println("Single beep (Normal)");
  digitalWrite(buzzerPin, HIGH);
  delay(200);
  digitalWrite(buzzerPin, LOW);
  delay(2000);
  
  Serial.println("Continuous beep (Alert)");
  for (int i = 0; i < 5; i++) {
    digitalWrite(buzzerPin, HIGH);
    delay(100);
    digitalWrite(buzzerPin, LOW);
    delay(100);
  }
  delay(2000);
}
```

**Success Criteria**:
- [ ] Clear, audible beep sounds
- [ ] Distinct patterns for different alerts
- [ ] No interference with other components
- [ ] Define beep patterns (1 beep=OK, continuous=Alert)

#### 3.3 Relay Test

**Wiring**:
- VCC → 5V
- GND → GND
- IN → D6

**Test Code** (`firmware/tests/relay_test.ino`):
```cpp
const int relayPin = 6;

void setup() {
  Serial.begin(115200);
  pinMode(relayPin, OUTPUT);
  Serial.println("Relay Test Starting...");
}

void loop() {
  Serial.println("Relay ON");
  digitalWrite(relayPin, HIGH);
  delay(2000);
  
  Serial.println("Relay OFF");
  digitalWrite(relayPin, LOW);
  delay(2000);
}
```

**Success Criteria**:
- [ ] Audible click when switching
- [ ] LED indicator changes state
- [ ] Stable switching operation
- [ ] Document normally open/closed configuration

### STEP 4: Camera System Test

#### 4.1 Linux Camera Verification
```bash
# SSH into UNO Q
ssh root@192.168.7.2

# Check for camera device
ls /dev/video*

# Test camera capture
apt update
apt install fswebcam

# Capture test image
fswebcam -r 640x480 --no-banner test_image.jpg

# View image properties
file test_image.jpg
```

#### 4.2 Python Camera Test
Create file: `linux/tests/camera_test.py`
```python
import cv2
import time

def test_camera():
    print("Testing camera...")
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return False
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Capture a few frames
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            print(f"Frame {i}: {frame.shape}")
            cv2.imwrite(f'test_frame_{i}.jpg', frame)
        else:
            print(f"Failed to capture frame {i}")
        
        time.sleep(0.5)
    
    cap.release()
    print("Camera test completed")
    return True

if __name__ == "__main__":
    test_camera()
```

**Success Criteria**:
- [ ] Camera device detected at /dev/video0
- [ ] Successful frame capture
- [ ] Reasonable image quality
- [ ] Stable frame rate

### STEP 5: MCU-Linux Communication

#### 5.1 MCU Serial Communication Code
Create file: `firmware/tests/serial_comm_test.ino`
```cpp
#include <ArduinoJson.h>

void setup() {
  Serial.begin(115200);
  Serial.println("MCU Communication Test Starting...");
}

void loop() {
  // Send sensor data to Linux
  StaticJsonDocument<200> sensorData;
  sensorData["timestamp"] = millis();
  sensorData["knob"] = analogRead(A0);
  sensorData["distance"] = readDistance();
  sensorData["movement"] = digitalRead(4);
  sensorData["temperature"] = 25.0; // Placeholder
  
  serializeJson(sensorData, Serial);
  Serial.println();
  
  // Check for commands from Linux
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
  
  delay(1000);
}

void processCommand(String cmd) {
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, cmd);
  
  if (error) {
    Serial.println("JSON parse error");
    return;
  }
  
  // Process servo commands
  if (doc.containsKey("servo1")) {
    int angle = doc["servo1"];
    Serial.print("Setting servo1 to: ");
    Serial.println(angle);
    // progressServo.write(angle);
  }
  
  if (doc.containsKey("buzzer")) {
    String state = doc["buzzer"];
    Serial.print("Setting buzzer to: ");
    Serial.println(state);
    // digitalWrite(buzzerPin, state == "ON" ? HIGH : LOW);
  }
}

long readDistance() {
  // Implement distance reading
  return 50; // Placeholder
}
```

#### 5.2 Linux Serial Communication Test
Create file: `linux/tests/serial_comm_test.py`
```python
import serial
import json
import time
import threading

class SerialCommTest:
    def __init__(self, port='/dev/ttyACM0', baud=115200):
        self.serial_port = serial.Serial(port, baud, timeout=1)
        self.running = True
        
    def read_sensor_data(self):
        """Read sensor data from MCU"""
        while self.running:
            try:
                line = self.serial_port.readline().decode().strip()
                if line:
                    data = json.loads(line)
                    print(f"Received: {data}")
            except json.JSONDecodeError:
                print(f"Invalid JSON: {line}")
            except Exception as e:
                print(f"Error: {e}")
    
    def send_command(self, command):
        """Send command to MCU"""
        cmd_json = json.dumps(command)
        self.serial_port.write((cmd_json + '\n').encode())
        print(f"Sent: {cmd_json}")
    
    def test_communication(self):
        # Start reading thread
        read_thread = threading.Thread(target=self.read_sensor_data)
        read_thread.daemon = True
        read_thread.start()
        
        # Send test commands
        time.sleep(2)
        
        print("Testing servo command...")
        self.send_command({"servo1": 90})
        time.sleep(1)
        
        print("Testing buzzer command...")
        self.send_command({"buzzer": "ON"})
        time.sleep(1)
        self.send_command({"buzzer": "OFF"})
        
        # Let it run for a while
        time.sleep(10)
        self.running = False

if __name__ == "__main__":
    test = SerialCommTest()
    test.test_communication()
```

**Success Criteria**:
- [ ] JSON messages sent from MCU to Linux
- [ ] Commands sent from Linux to MCU
- [ ] Bidirectional communication working
- [ ] No data corruption or loss

### STEP 6: System Integration Test

#### 6.1 Complete System Test
Create file: `firmware/phase1_integration_test.ino`
```cpp
#include <ArduinoJson.h>
#include <Servo.h>

// Pin definitions
const int knobPin = A0;
const int trigPin = 2;
const int echoPin = 3;
const int motionPin = 4;
const int buzzerPin = 5;
const int relayPin = 6;
const int servo1Pin = 9;
const int servo2Pin = 10;

Servo progressServo;
Servo resultServo;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(motionPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(relayPin, OUTPUT);
  
  // Initialize servos
  progressServo.attach(servo1Pin);
  resultServo.attach(servo2Pin);
  
  // Set initial positions
  progressServo.write(0);
  resultServo.write(90);
  
  Serial.println("Phase 1 Integration Test Ready");
}

void loop() {
  // Read all sensors
  StaticJsonDocument<300> sensorData;
  sensorData["timestamp"] = millis();
  sensorData["knob"] = readKnob();
  sensorData["distance"] = readDistance();
  sensorData["movement"] = digitalRead(motionPin);
  sensorData["temperature"] = readTemperature();
  
  // Send to Linux
  serializeJson(sensorData, Serial);
  Serial.println();
  
  // Process Linux commands
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
  
  delay(500);
}

int readKnob() {
  int raw = analogRead(knobPin);
  return map(raw, 0, 1023, 0, 2);
}

long readDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH);
  return (duration/2) / 29.1;
}

float readTemperature() {
  // Implement based on your sensor
  return 25.0; // Placeholder
}

void processCommand(String cmd) {
  StaticJsonDocument<200> doc;
  if (deserializeJson(doc, cmd) != DeserializationError::Ok) {
    return;
  }
  
  if (doc.containsKey("servo1")) {
    progressServo.write(doc["servo1"]);
  }
  
  if (doc.containsKey("servo2")) {
    resultServo.write(doc["servo2"]);
  }
  
  if (doc.containsKey("buzzer")) {
    digitalWrite(buzzerPin, doc["buzzer"] == "ON" ? HIGH : LOW);
  }
  
  if (doc.containsKey("relay")) {
    digitalWrite(relayPin, doc["relay"] == "ON" ? HIGH : LOW);
  }
}
```

## 📋 Phase 1 Completion Checklist

### Hardware Verification
- [ ] Arduino UNO Q boots to Linux successfully
- [ ] SSH access working (document IP address)
- [ ] All Modulino sensors connected and reading
- [ ] Servos moving smoothly without jitter
- [ ] Buzzer producing clear sounds
- [ ] Relay clicking and switching properly
- [ ] Camera capturing frames successfully

### Communication Testing
- [ ] MCU sending JSON sensor data to Linux
- [ ] Linux sending commands to MCU
- [ ] No data corruption or communication errors
- [ ] Stable bidirectional communication

### Documentation
- [ ] Complete pin mapping documented
- [ ] System information recorded
- [ ] Wiring diagram photographed
- [ ] Component specifications noted
- [ ] Known issues and workarounds documented

### Performance Validation
- [ ] Sensor readings stable and accurate
- [ ] Actuator responses timely and precise
- [ ] System runs continuously without crashes
- [ ] Power consumption within acceptable limits

## 📁 Phase 1 Deliverables

Create these files before proceeding:

1. **hardware/pinmap.md** - Complete pin assignments
2. **hardware/wiring_photos/** - Clear wiring photographs
3. **hardware/system_info.txt** - UNO Q system specifications
4. **firmware/phase1_test.ino** - Complete integration test
5. **linux/tests/system_test.py** - Linux-side validation
6. **docs/phase1_results.md** - Test results and performance data

## ⚠️ Common Issues & Solutions

### Arduino UNO Q Not Booting
- Check USB-C cable and power supply
- Try different USB ports
- Wait full 90 seconds for boot
- Check for EDL mode recovery

### Serial Communication Failing
- Verify baud rate (115200)
- Check device path (/dev/ttyACM0)
- Ensure common ground connections
- Test with simple echo commands

### Sensor Readings Unstable
- Check power supply stability
- Verify ground connections
- Add decoupling capacitors if needed
- Check for electromagnetic interference

### Servo Jitter or Erratic Movement
- Ensure adequate power supply (5V, sufficient current)
- Check PWM signal integrity
- Add power filtering capacitors
- Verify servo specifications

## 🚀 Next Steps

Once Phase 1 is complete:
1. Document all working configurations
2. Create system backup/snapshot
3. Proceed to **PHASE 2: Audio Pipeline & Preprocessing**

**Remember**: A solid hardware foundation is critical for success. Don't rush this phase!