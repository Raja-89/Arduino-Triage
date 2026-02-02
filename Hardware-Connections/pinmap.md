# 🔌 Hardware Pin Mapping & Wiring Guide

**Arduino UNO Q Pin Assignments for Smart Rural Triage Station**

## 📋 Overview

This document provides the complete pin mapping and wiring guide for connecting all components to the Arduino UNO Q dual-core system.

### System Architecture
- **Linux Side (QRB2210)**: High-level processing, AI inference, web interface
- **MCU Side (STM32U585)**: Real-time I/O, sensor polling, actuator control
- **Communication**: Serial/USB bridge between cores

## 🔧 MCU Side Pin Assignments (STM32U585)

### Analog Inputs
| Pin | Component | Signal | Purpose | Voltage |
|-----|-----------|--------|---------|---------|
| A0 | Modulino Knob | Analog Output | Mode selection (0-2) | 0-3.3V |
| A1 | Audio Input* | Analog Audio | Contact microphone | 0-3.3V |

*Note: Audio input may use USB audio interface instead

### Digital I/O Pins
| Pin | Component | Signal Type | Purpose | Voltage |
|-----|-----------|-------------|---------|---------|
| D2 | Distance Sensor | Digital Output | Ultrasonic Trigger | 3.3V/5V |
| D3 | Distance Sensor | Digital Input | Ultrasonic Echo | 3.3V/5V |
| D4 | Movement Sensor | Digital Input | Motion Detection | 3.3V |
| D5 | Buzzer | PWM Output | Audio Alerts | 3.3V |
| D6 | Relay Module | Digital Output | External Trigger | 3.3V |
| D7 | Status LED | Digital Output | System Status | 3.3V |
| D8 | Reserved | - | Future Expansion | - |

### PWM Outputs (Servos)
| Pin | Component | Signal Type | Purpose | Voltage |
|-----|-----------|-------------|---------|---------|
| D9 | Servo 1 | PWM Output | Progress Indicator | 5V |
| D10 | Servo 2 | PWM Output | Result Display | 5V |

### I2C Interface
| Pin | Component | Signal | Purpose | Voltage |
|-----|-----------|--------|---------|---------|
| SDA | Modulino Thermo | I2C Data | Temperature Reading | 3.3V |
| SCL | Modulino Thermo | I2C Clock | Temperature Reading | 3.3V |

### Power & Ground
| Pin | Purpose | Voltage | Max Current |
|-----|---------|---------|-------------|
| 5V | Servo Power, Distance Sensor | 5.0V | 500mA |
| 3.3V | Modulino Sensors, Logic | 3.3V | 200mA |
| GND | Common Ground | 0V | - |

## 🖥️ Linux Side Connections (QRB2210)

### USB Interfaces
| Port | Component | Interface | Purpose |
|------|-----------|-----------|---------|
| USB-A | Logitech Brio 100 | USB 2.0 | Video Capture |
| USB-A | Audio Interface* | USB Audio | High-quality audio input |
| USB-C | Power/Data | USB-C | System power and programming |

*Optional: Use USB audio interface for better audio quality

### Internal Connections
| Interface | Purpose | Notes |
|-----------|---------|-------|
| Serial/USB CDC | MCU Communication | Bidirectional JSON messages |
| GPIO | Status LEDs | System status indication |
| I2C | Expansion | Future sensor additions |

## 🔌 Detailed Wiring Instructions

### 1. Modulino Knob (Mode Selection)
```
Modulino Knob → Arduino UNO Q
VCC (Red)     → 3.3V
GND (Black)   → GND
SIG (Yellow)  → A0
```

**Function**: Rotary input for selecting operation mode
- Position 0: Heart Sound Analysis
- Position 1: Lung Sound Analysis  
- Position 2: Calibration Mode

### 2. Modulino Distance Sensor (Placement Validation)
```
Distance Sensor → Arduino UNO Q
VCC (Red)       → 5V (check sensor specification)
GND (Black)     → GND
TRIG (Blue)     → D2
ECHO (Green)    → D3
```

**Function**: Ensures proper stethoscope placement distance (3-8cm optimal)

### 3. Modulino Movement Sensor (Motion Detection)
```
Movement Sensor → Arduino UNO Q
VCC (Red)       → 3.3V
GND (Black)     → GND
OUT (Yellow)    → D4
```

**Function**: Detects patient movement to pause analysis during motion

### 4. Modulino Thermo (Temperature Screening)
```
Thermo Sensor → Arduino UNO Q
VCC (Red)     → 3.3V
GND (Black)   → GND
SDA (Blue)    → SDA
SCL (Green)   → SCL
```

**Function**: Body temperature measurement for fever detection

### 5. Modulino Buzzer (Audio Alerts)
```
Buzzer Module → Arduino UNO Q
VCC (Red)     → 3.3V
GND (Black)   → GND
SIG (Yellow)  → D5
```

**Function**: Audible alerts for results
- 1 short beep: Normal result
- Continuous beeping: Abnormal result requiring attention

### 6. Modulino Latch Relay (External Trigger)
```
Relay Module → Arduino UNO Q
VCC (Red)    → 5V
GND (Black)  → GND
IN (Yellow)  → D6
```

**Function**: Triggers external devices (clinic alarm, light, etc.)

### 7. Servo Motors (Visual Feedback)
```
Servo 1 (Progress) → Arduino UNO Q
Red Wire           → 5V
Brown/Black Wire   → GND
Orange/Yellow Wire → D9

Servo 2 (Result) → Arduino UNO Q
Red Wire         → 5V
Brown/Black Wire → GND
Orange/Yellow Wire → D10
```

**Function**: 
- Servo 1: Shows capture/processing progress (0° to 180°)
- Servo 2: Displays result (45° = Normal, 135° = Abnormal)

### 8. Contact Microphone (Audio Input)

#### Option A: Direct Analog Connection
```
MAX9814 Module → Arduino UNO Q
VCC            → 3.3V
GND            → GND
OUT            → A1
GAIN           → 3.3V (maximum gain)
```

#### Option B: USB Audio Interface (Recommended)
```
MAX9814 Module → 3.5mm Jack → USB Audio Interface → UNO Q USB Port
VCC            → 3.3V (from USB power)
GND            → GND
OUT            → 3.5mm Tip
```

### 9. Camera (Positioning Guidance)
```
Logitech Brio 100 → Arduino UNO Q
USB-A Connector   → USB-A Port
```

**Function**: Provides visual positioning guidance and demo visualization

## ⚡ Power Distribution

### Power Requirements
| Component | Voltage | Current | Power |
|-----------|---------|---------|-------|
| Arduino UNO Q | 5V | 2A | 10W |
| Servo Motors (2x) | 5V | 500mA each | 5W |
| Modulino Sensors | 3.3V | 50mA total | 0.2W |
| Camera | 5V | 500mA | 2.5W |
| Audio Interface | 5V | 100mA | 0.5W |
| **Total** | - | **~3.7A** | **~18W** |

### Power Supply Recommendations
- **Primary**: USB-C PD adapter (20W minimum)
- **Backup**: USB-C power bank (10,000mAh+)
- **Development**: Bench power supply (5V, 4A)

## 🔧 Assembly Instructions

### Step 1: Prepare Components
1. Unpack all Modulino sensors and servos
2. Organize jumper wires by length and type
3. Prepare breadboard or perfboard for connections
4. Test Arduino UNO Q boot and connectivity

### Step 2: Power Connections First
1. Connect all GND pins to common ground rail
2. Connect 3.3V rail for low-power sensors
3. Connect 5V rail for servos and high-power components
4. Verify voltage levels with multimeter

### Step 3: Sensor Connections
1. Connect sensors one at a time
2. Test each sensor individually before proceeding
3. Use color-coded wires for easy identification
4. Document any deviations from standard pinout

### Step 4: Actuator Connections
1. Connect servos with proper power supply
2. Test servo movement range and smoothness
3. Connect buzzer and test audio output
4. Connect relay and verify switching operation

### Step 5: Communication Setup
1. Verify MCU-Linux serial communication
2. Test bidirectional data flow
3. Implement error handling and recovery
4. Document communication protocol

### Step 6: Final Integration
1. Connect camera and test video feed
2. Set up audio input (analog or USB)
3. Perform complete system test
4. Calibrate sensors and actuators

## 🧪 Testing & Validation

### Individual Component Tests
```bash
# Test each component individually
arduino-cli compile --fqbn arduino:samd:uno firmware/tests/knob_test.ino
arduino-cli compile --fqbn arduino:samd:uno firmware/tests/distance_test.ino
arduino-cli compile --fqbn arduino:samd:uno firmware/tests/movement_test.ino
# ... etc for each component
```

### System Integration Test
```bash
# Upload complete integration test
arduino-cli compile --fqbn arduino:samd:uno firmware/phase1_integration_test.ino
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:samd:uno firmware/phase1_integration_test.ino
```

### Communication Test
```bash
# Test MCU-Linux communication
cd linux/tests
python3 serial_comm_test.py
```

## 📊 Pin Usage Summary

### MCU Pin Allocation
- **Analog Inputs**: 2/6 used (A0, A1)
- **Digital I/O**: 7/14 used (D2-D8)
- **PWM Outputs**: 2/6 used (D9, D10)
- **I2C**: 2/2 used (SDA, SCL)
- **Available**: 5 digital pins for expansion

### Expansion Possibilities
- **D8**: Additional sensor input
- **D11-D13**: SPI interface for displays
- **A2-A5**: Additional analog sensors
- **I2C**: Multiple sensors on same bus

## ⚠️ Safety & Troubleshooting

### Safety Precautions
- Always connect GND first, power last
- Verify voltage levels before connecting components
- Use current-limited power supply during testing
- Avoid short circuits between power rails

### Common Issues
1. **Servo jitter**: Check power supply capacity and filtering
2. **Sensor noise**: Verify ground connections and shielding
3. **Communication errors**: Check baud rate and cable integrity
4. **Power issues**: Measure actual voltages under load

### Debugging Tools
- Multimeter for voltage/continuity testing
- Oscilloscope for signal analysis
- Logic analyzer for digital communication
- Serial monitor for MCU debugging

## 📝 Documentation Standards

### Wiring Documentation
- Take photos of all connections
- Label wires with component names
- Create schematic diagram
- Document any modifications or deviations

### Testing Records
- Record test results for each component
- Document performance characteristics
- Note any issues or limitations
- Create troubleshooting guide

---

**Note**: This pinmap is optimized for the Arduino UNO Q dual-core architecture. Ensure all connections are verified before powering on the system. Always follow proper ESD precautions when handling electronic components.