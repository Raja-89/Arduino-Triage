# Smart Rural Triage Station - Software Implementation Guide

**Complete Guide for Hardware Team Members**

This document explains the software architecture and implementation details for team members who have the hardware but need to understand the software side.

---

## 🎯 **Quick Overview**

The software system has two main parts:
1. **Arduino Firmware** (C++) - Runs on the MCU, handles sensors/actuators
2. **Linux System** (Python) - Runs on the Linux side, handles AI and web interface

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE SYSTEM OVERVIEW                     │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser  │  Arduino IDE  │  SSH Terminal  │  File Manager  │
│  (Dashboard)  │  (Firmware)   │  (Commands)    │  (Files)       │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ARDUINO UNO Q BOARD                         │
├─────────────────────────────────────────────────────────────────┤
│  Linux Side (QRB2210)     │     MCU Side (STM32U585)          │
│  - Python System          │     - Arduino Firmware             │
│  - AI Processing           │     - Sensor Reading               │
│  - Web Interface           │     - Actuator Control             │
│  - Audio Processing        │     - Real-time I/O                │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HARDWARE COMPONENTS                        │
├─────────────────────────────────────────────────────────────────┤
│  Modulino Sensors    │  Modulino Actuators  │  Audio/Camera     │
│  - Distance          │  - Servos             │  - Microphone     │
│  - Temperature       │  - Buzzer             │  - Camera         │
│  - Movement          │  - Relay              │  - Speakers       │
│  - Knob              │  - LED                │                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 **Step-by-Step Implementation Checklist**

### **Phase 1: Hardware Setup** ✅
- [ ] Connect all Modulino components
- [ ] Wire audio input (microphone/stethoscope)
- [ ] Connect camera (optional)
- [ ] Test basic connectivity
- [ ] Verify power supply

### **Phase 2: Arduino Firmware** ✅
- [ ] Upload `firmware/main/main.ino` using Arduino IDE
- [ ] Test serial communication
- [ ] Verify sensor readings
- [ ] Test actuator control

### **Phase 3: Linux System Setup** ✅
- [ ] Run installation script
- [ ] Copy software files
- [ ] Install Python dependencies
- [ ] Configure system settings

### **Phase 4: ML Models** ⚠️ **NEEDS ATTENTION**
- [ ] Obtain trained `.tflite` model files
- [ ] Place models in correct directories
- [ ] Test model loading
- [ ] Validate inference accuracy

### **Phase 5: System Integration** ✅
- [ ] Test MCU-Linux communication
- [ ] Verify audio pipeline
- [ ] Test web interface
- [ ] Run end-to-end examination

---

## 🗂️ **File Structure & Responsibilities**

### **Arduino Side (MCU)**
```
firmware/main/main.ino                 # MAIN MCU FIRMWARE
├── Handles all Modulino sensors       # Distance, temp, movement, knob
├── Controls all actuators             # Servos, buzzer, relay, LED
├── Serial communication with Linux    # JSON message protocol
└── Real-time sensor monitoring        # 100ms sensor reads, 5s heartbeat
```

**What it does:**
- Reads sensors every 100ms
- Sends sensor data to Linux via serial
- Receives control commands from Linux
- Controls servos, buzzer, LED, relay
- Manages system state (IDLE, EXAMINING, etc.)

### **Linux Side (Main System)**
```
main.py                               # SYSTEM ENTRY POINT
├── Starts all system components
├── Handles graceful shutdown
└── Manages system lifecycle

linux/core/system_manager.py          # MAIN SYSTEM CONTROLLER
├── Coordinates all components         # Audio, ML, hardware, web
├── Manages examination workflow       # Start → Capture → Process → Results
├── Handles state transitions          # IDLE → EXAMINING → PROCESSING → RESULTS
└── Error handling and recovery        # System monitoring and restart

linux/core/state_machine.py           # STATE MANAGEMENT
├── Defines system states             # IDLE, EXAMINING, PROCESSING, etc.
├── Manages state transitions          # Valid state changes only
├── Stores examination data            # Current progress, results
└── Handles timeouts and errors        # Auto-recovery mechanisms

linux/core/config_manager.py          # CONFIGURATION SYSTEM
├── Loads YAML configuration files     # system.yaml, audio.yaml
├── Hot-reload configuration changes   # No restart needed
├── Validates configuration            # Prevents invalid settings
└── Provides config to all components  # Centralized settings
```

### **Hardware Interface Layer**
```
linux/hardware/serial_manager.py      # MCU COMMUNICATION
├── Serial communication with Arduino  # JSON message protocol
├── Message parsing and validation     # Handles sensor data, commands
├── Connection management              # Auto-reconnect, error handling
└── Protocol implementation            # Heartbeat, commands, status

linux/hardware/audio_manager.py       # AUDIO SYSTEM
├── Audio device management            # Microphone detection, setup
├── Audio capture and recording        # Real-time audio streaming
├── Device compatibility testing       # Ensures audio works
└── Audio quality monitoring           # Signal level, noise detection

linux/hardware/camera_manager.py      # CAMERA SYSTEM (Optional)
├── Camera initialization and control  # USB camera management
├── Frame capture and processing       # Real-time video feed
├── Positioning guidance               # Visual feedback for placement
└── Image saving and analysis          # Capture examination images
```

### **Audio Processing Pipeline**
```
linux/audio/capture.py                # AUDIO CAPTURE
├── Real-time audio recording          # 8-second examination capture
├── Progress tracking and callbacks    # Updates UI during recording
├── Quality monitoring                 # Signal level, clipping detection
└── Automatic gain control             # Optimizes audio levels

linux/audio/preprocessing.py          # SIGNAL PROCESSING
├── Audio filtering                    # Remove noise, enhance signal
├── Noise reduction                    # Spectral subtraction
├── Normalization                      # Consistent audio levels
└── Artifact removal                   # Click removal, DC offset

linux/audio/features.py               # FEATURE EXTRACTION
├── Mel-spectrogram computation        # Time-frequency representation
├── MFCC extraction                    # Mel-frequency cepstral coefficients
├── Medical-specific features          # Heart rate, respiratory patterns
└── Feature vector creation            # ML model input preparation
```

### **Machine Learning System**
```
linux/ml/inference_engine.py          # ML INFERENCE ENGINE ✅
├── TensorFlow Lite model loading      # Heart and lung models
├── Real-time inference                # <200ms processing time
├── Confidence scoring                 # Prediction reliability
└── Model management                   # Loading, validation, fallback

MISSING: Actual .tflite model files    # ⚠️ NEEDS TRAINED MODELS
├── models/heart/heart_model.tflite    # Heart sound classification
├── models/lung/lung_model.tflite      # Lung sound classification
└── models/yamnet/yamnet_model.tflite  # General audio classification
```

### **Triage Decision System**
```
linux/triage/decision_engine.py       # TRIAGE LOGIC ✅
├── Multi-modal sensor fusion         # Combines audio + sensor data
├── Risk assessment                    # LOW/MEDIUM/HIGH risk levels
├── Clinical recommendations          # Referral suggestions
└── Explainable AI reasoning           # Why this decision was made
```

### **Calibration System**
```
linux/calibration/calibration_manager.py    # CALIBRATION COORDINATOR ✅
├── Manages all calibration procedures       # Audio + sensor calibration
├── Automatic calibration scheduling         # Periodic recalibration
├── Calibration status tracking              # Last calibration, quality
└── Calibration data management              # Store/load calibration

linux/calibration/audio_calibration.py      # AUDIO CALIBRATION ✅
├── Noise floor measurement                  # Ambient noise assessment
├── Microphone sensitivity calibration      # Gain adjustment
├── Frequency response measurement           # Audio quality validation
└── Calibration validation                   # Verify calibration success
```

### **Web Interface**
```
linux/web/app.py                      # WEB APPLICATION ✅
├── Flask web server                   # HTTP server for dashboard
├── REST API endpoints                 # /api/status, /api/examination/*
├── WebSocket communication            # Real-time updates
└── System control interface           # Start/stop examinations

linux/web/templates/                   # WEB PAGES ✅
├── base.html                          # Common layout and navigation
├── index.html                         # Main dashboard
├── examination.html                   # Examination control page
└── error.html                         # Error display page
```

### **Configuration Files**
```
config/system.yaml                     # MAIN SYSTEM CONFIG ✅
├── Hardware settings                  # Serial ports, device IDs
├── Audio configuration                # Sample rates, buffer sizes
├── ML model paths                     # Model file locations
└── Triage thresholds                  # Risk assessment parameters

config/audio.yaml                      # AUDIO CONFIG ✅
├── Audio processing parameters        # Filtering, noise reduction
├── Feature extraction settings        # MFCC, mel-spectrogram
├── Medical analysis parameters        # Heart/lung frequency bands
└── Calibration settings               # Calibration procedures
```

---

## 🔄 **System Workflow - How Everything Works Together**

### **1. System Startup**
```
main.py
├── Loads configuration from config/system.yaml
├── Initializes SystemManager
├── SystemManager starts all components:
│   ├── SerialManager (connects to Arduino)
│   ├── AudioManager (initializes microphone)
│   ├── CameraManager (optional, for positioning)
│   ├── InferenceEngine (loads ML models)
│   ├── TriageEngine (initializes decision logic)
│   ├── CalibrationManager (loads calibration data)
│   └── WebApp (starts web server on port 5000)
└── System enters IDLE state, ready for examinations
```

### **2. Examination Workflow**
```
User clicks "Start Examination" on web interface
├── Web interface sends POST to /api/examination/start
├── SystemManager.start_examination() called
├── State machine transitions: IDLE → EXAMINING
├── Arduino receives control command via SerialManager
├── Arduino activates LED, resets servos, plays confirmation beep
├── AudioCapture starts 8-second recording
├── Progress updates sent to web interface via WebSocket
├── Audio data processed through preprocessing pipeline
├── Features extracted (mel-spectrogram, MFCCs)
├── ML inference performed on features
├── Sensor data combined with ML results
├── TriageEngine makes final decision
├── Results displayed on servos and web interface
├── State machine transitions: EXAMINING → PROCESSING → SHOWING_RESULTS → IDLE
└── System ready for next examination
```

### **3. Real-time Monitoring**
```
Continuous background processes:
├── Arduino sends sensor data every 100ms
├── SerialManager parses and forwards to SystemManager
├── SystemManager updates state machine data
├── Web interface receives updates via WebSocket
├── Dashboard displays real-time sensor readings
├── System monitors for errors and handles recovery
└── Calibration manager checks if recalibration needed
```

---

## 🚨 **What's Missing - ML Models**

### **Current Status**
- ✅ ML inference engine is implemented
- ✅ Model loading code is ready
- ✅ Feature extraction pipeline is complete
- ⚠️ **MISSING: Actual trained model files**

### **What You Need**
1. **Heart Sound Model** (`models/heart/heart_model.tflite`)
   - Input: Mel-spectrogram features (64 mel bands)
   - Output: 2 classes (Normal, Abnormal)
   - Size: <2MB for edge deployment

2. **Lung Sound Model** (`models/lung/lung_model.tflite`)
   - Input: Mel-spectrogram features (64 mel bands)
   - Output: 4 classes (Normal, Wheeze, Crackle, Both)
   - Size: <2MB for edge deployment

3. **YAMNet Model** (`models/yamnet/yamnet_model.tflite`) - Optional
   - General audio classification
   - Used for noise detection and quality assessment

### **Model Placement**
```bash
# Create model directories
sudo mkdir -p /opt/triage-station/models/{heart,lung,yamnet}

# Copy your trained models
sudo cp heart_model.tflite /opt/triage-station/models/heart/
sudo cp lung_model.tflite /opt/triage-station/models/lung/
sudo cp yamnet_model.tflite /opt/triage-station/models/yamnet/

# Set permissions
sudo chown -R triage:triage /opt/triage-station/models/
```

### **Model Testing**
```python
# Test model loading
python3 -c "
import sys
sys.path.append('/opt/triage-station/linux')
from ml.inference_engine import InferenceEngine

engine = InferenceEngine(
    heart_model_path='/opt/triage-station/models/heart/heart_model.tflite',
    lung_model_path='/opt/triage-station/models/lung/lung_model.tflite'
)

if engine.initialize():
    print('✅ Models loaded successfully')
else:
    print('❌ Model loading failed')
"
```

---

## 🛠️ **Implementation Commands**

### **1. Initial Setup**
```bash
# Connect to Arduino Uno Q
ssh root@192.168.7.2

# Run installation script
cd /path/to/project
sudo bash setup/install.sh

# This will:
# - Install system dependencies
# - Create Python virtual environment
# - Install Python packages
# - Create directory structure
# - Setup systemd services
# - Configure permissions
```

### **2. Deploy Software**
```bash
# Copy project files
sudo cp -r linux/ /opt/triage-station/
sudo cp -r config/ /opt/triage-station/
sudo cp main.py /opt/triage-station/
sudo cp requirements.txt /opt/triage-station/

# Set permissions
sudo chown -R triage:triage /opt/triage-station/
```

### **3. Upload Arduino Firmware**
```bash
# Using Arduino IDE:
# 1. Open firmware/main/main.ino
# 2. Select Arduino Uno Q board
# 3. Select correct port (usually /dev/ttyACM0)
# 4. Click Upload

# Or using arduino-cli:
arduino-cli compile --fqbn arduino:mbed_opta:opta firmware/main/
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:mbed_opta:opta firmware/main/
```

### **4. Start System**
```bash
# Start the service
sudo systemctl start triage-station

# Check status
sudo systemctl status triage-station

# View logs
sudo journalctl -u triage-station -f

# Or run manually for testing
cd /opt/triage-station
source venv/bin/activate
python main.py
```

### **5. Access Web Interface**
```bash
# Open browser to:
http://192.168.7.2:5000

# Or if accessing locally:
http://localhost:5000
```

---

## 🔧 **Testing & Troubleshooting**

### **Test Individual Components**
```bash
# Test serial communication
python3 /opt/triage-station/linux/hardware/serial_manager.py

# Test audio system
python3 /opt/triage-station/linux/hardware/audio_manager.py

# Test camera (if connected)
python3 /opt/triage-station/linux/hardware/camera_manager.py

# Test ML inference (needs models)
python3 /opt/triage-station/linux/ml/inference_engine.py
```

### **Common Issues & Solutions**

1. **Arduino Not Detected**
   ```bash
   # Check USB connection
   lsusb | grep Arduino
   
   # Check serial ports
   ls /dev/ttyACM*
   
   # Fix permissions
   sudo usermod -a -G dialout $USER
   ```

2. **Audio Not Working**
   ```bash
   # List audio devices
   arecord -l
   
   # Test audio capture
   arecord -d 5 test.wav
   
   # Check permissions
   sudo usermod -a -G audio $USER
   ```

3. **Web Interface Not Loading**
   ```bash
   # Check if service is running
   sudo systemctl status triage-station
   
   # Check port availability
   sudo netstat -tlnp | grep 5000
   
   # Check firewall
   sudo ufw allow 5000
   ```

4. **Models Not Loading**
   ```bash
   # Check model files exist
   ls -la /opt/triage-station/models/*/
   
   # Check file permissions
   sudo chown -R triage:triage /opt/triage-station/models/
   
   # Test model loading
   python3 -c "import tensorflow as tf; print(tf.__version__)"
   ```

---

## 📊 **System Monitoring**

### **Real-time Status**
```bash
# System logs
sudo journalctl -u triage-station -f

# System resources
htop

# Disk usage
df -h /opt/triage-station/

# Network connections
sudo netstat -tlnp | grep python
```

### **Performance Metrics**
- **Memory Usage**: Should be <512MB
- **CPU Usage**: Should be <50% during inference
- **Inference Time**: Should be <200ms
- **Audio Latency**: Should be <100ms

---

## 🎯 **Next Steps for Your Friend**

1. **Hardware Verification**
   - Ensure all Modulino components are connected
   - Test basic Arduino functionality
   - Verify audio input is working

2. **Software Installation**
   - Run the installation script
   - Upload Arduino firmware
   - Test serial communication

3. **Model Integration**
   - Obtain trained `.tflite` model files
   - Place them in the correct directories
   - Test model loading and inference

4. **System Testing**
   - Run end-to-end examination test
   - Verify web interface functionality
   - Test all sensors and actuators

5. **Demo Preparation**
   - Practice examination workflow
   - Prepare test audio samples
   - Ensure system reliability

---

## 📞 **Support & Communication**

### **Key Files to Monitor**
- `/opt/triage-station/logs/system.log` - Main system log
- `/var/log/syslog` - System-wide logs
- `sudo journalctl -u triage-station` - Service logs

### **Important Commands**
```bash
# Restart system
sudo systemctl restart triage-station

# Stop system
sudo systemctl stop triage-station

# Check system status
sudo systemctl status triage-station

# Update configuration
sudo nano /opt/triage-station/config/system.yaml
sudo systemctl restart triage-station
```

### **Emergency Recovery**
```bash
# If system is stuck, force restart
sudo systemctl stop triage-station
sudo pkill -f python
sudo systemctl start triage-station

# Reset to defaults
sudo cp config/system.yaml /opt/triage-station/config/
sudo systemctl restart triage-station
```

---

**This guide covers everything your friend needs to know about the software implementation. The only missing piece is the trained ML models - everything else is complete and ready to deploy!**