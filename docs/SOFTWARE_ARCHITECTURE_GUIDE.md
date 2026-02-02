# 🖥️ Complete Software Architecture Guide

**Smart Rural Triage Station - Software Implementation**

This comprehensive guide covers the entire software stack for your AI-powered medical screening device, from Arduino firmware to Linux AI inference systems.

## 🎯 Software Architecture Overview

### **Dual-Brain Software System**
```
┌─────────────────────────────────────────────────────────────┐
│                    ARDUINO UNO Q                           │
├─────────────────────┬───────────────────────────────────────┤
│   LINUX SIDE        │         MCU SIDE                     │
│   (QRB2210)         │         (STM32U585)                  │
│                     │                                      │
│ ┌─────────────────┐ │ ┌─────────────────────────────────┐  │
│ │   Web Interface │ │ │      Arduino Firmware          │  │
│ │   (Flask/HTML)  │ │ │      (C++/Arduino IDE)          │  │
│ └─────────────────┘ │ └─────────────────────────────────┘  │
│ ┌─────────────────┐ │ ┌─────────────────────────────────┐  │
│ │  AI Inference   │ │ │    Sensor Management            │  │
│ │  (TensorFlow)   │ │ │    (Real-time I/O)              │  │
│ └─────────────────┘ │ └─────────────────────────────────┘  │
│ ┌─────────────────┐ │ ┌─────────────────────────────────┐  │
│ │ Audio Processing│ │ │   Actuator Control              │  │
│ │ (Python/librosa)│ │ │   (Servos/Buzzer/Relay)         │  │
│ └─────────────────┘ │ └─────────────────────────────────┘  │
│ ┌─────────────────┐ │ ┌─────────────────────────────────┐  │
│ │ System Control  │ │ │   Serial Communication         │  │
│ │ (Python)        │ │ │   (JSON Protocol)               │  │
│ └─────────────────┘ │ └─────────────────────────────────┘  │
└─────────────────────┴───────────────────────────────────────┘
                      │
                      ▼
              Serial/USB Communication
                  (JSON Messages)
```

## 📚 Software Stack Breakdown

### **Linux Side Software Stack**
```
┌─────────────────────────────────────────┐
│           USER INTERFACE LAYER          │
├─────────────────────────────────────────┤
│ • Web Dashboard (Flask + HTML/CSS/JS)  │
│ • REST API Endpoints                    │
│ • Real-time WebSocket Communication    │
│ • Demo Mode Interface                   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│         APPLICATION LOGIC LAYER         │
├─────────────────────────────────────────┤
│ • System State Management               │
│ • Triage Decision Engine                │
│ • Multi-modal Sensor Fusion            │
│ • Device Calibration System            │
│ • Data Logging and Analytics            │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│         AI/ML PROCESSING LAYER          │
├─────────────────────────────────────────┤
│ • TensorFlow Lite Inference Engine     │
│ • Audio Feature Extraction             │
│ • Heart Sound Classification           │
│ • Lung Sound Classification            │
│ • Explainable AI Results               │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│        SIGNAL PROCESSING LAYER          │
├─────────────────────────────────────────┤
│ • Real-time Audio Capture              │
│ • Digital Signal Processing            │
│ • Noise Reduction and Filtering        │
│ • Spectrogram Generation               │
│ • Heart Rate Estimation                │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│         HARDWARE INTERFACE LAYER        │
├─────────────────────────────────────────┤
│ • Serial Communication Manager         │
│ • Camera Interface (OpenCV)            │
│ • Audio Device Management              │
│ • File System Operations               │
│ • Network Configuration                │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            OPERATING SYSTEM             │
├─────────────────────────────────────────┤
│ • Debian Linux (Custom Build)          │
│ • Python 3.9+ Runtime                  │
│ • System Services and Daemons          │
│ • Hardware Drivers                     │
└─────────────────────────────────────────┘
```

### **MCU Side Software Stack**
```
┌─────────────────────────────────────────┐
│           APPLICATION LAYER             │
├─────────────────────────────────────────┤
│ • Main Control Loop                     │
│ • State Machine Implementation          │
│ • Safety Monitoring                     │
│ • Error Handling and Recovery           │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│         COMMUNICATION LAYER             │
├─────────────────────────────────────────┤
│ • JSON Message Parser                   │
│ • Serial Protocol Handler               │
│ • Command Queue Management              │
│ • Data Validation                       │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│           HARDWARE LAYER                │
├─────────────────────────────────────────┤
│ • Sensor Reading (ADC, I2C, Digital)   │
│ • Actuator Control (PWM, Digital Out)  │
│ • Interrupt Service Routines           │
│ • Timer Management                      │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            SYSTEM LAYER                 │
├─────────────────────────────────────────┤
│ • Arduino Framework                     │
│ • STM32 HAL (Hardware Abstraction)     │
│ • Real-time Operating System           │
│ • Memory Management                     │
└─────────────────────────────────────────┘
```

## 🔄 Data Flow Architecture

### **Complete System Data Flow**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   SENSORS   │───▶│     MCU      │───▶│    LINUX    │
│             │    │              │    │             │
│ • Knob      │    │ • Read ADC   │    │ • Receive   │
│ • Distance  │    │ • Read I2C   │    │   JSON      │
│ • Movement  │    │ • Read GPIO  │    │ • Parse     │
│ • Temp      │    │ • Format     │    │   Data      │
│ • Audio     │    │   JSON       │    │ • Process   │
│ • Camera    │    │ • Send       │    │   Signals   │
└─────────────┘    │   Serial     │    └─────────────┘
                   └──────────────┘           │
                                              ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  ACTUATORS  │◀───│     MCU      │◀───│  AI ENGINE  │
│             │    │              │    │             │
│ • Servos    │    │ • Parse      │    │ • Audio     │
│ • Buzzer    │    │   Commands   │    │   Analysis  │
│ • Relay     │    │ • Control    │    │ • ML        │
│ • LEDs      │    │   PWM        │    │   Inference │
│             │    │ • Set GPIO   │    │ • Decision  │
│             │    │ • Send       │    │   Logic     │
└─────────────┘    │   Status     │    │ • Generate  │
                   └──────────────┘    │   Commands  │
                                       └─────────────┘
```

### **Message Flow Examples**
```
1. SENSOR READING FLOW:
   Knob Position → MCU ADC → JSON {"knob": 1} → Linux Parser → Mode Selection

2. AUDIO ANALYSIS FLOW:
   Microphone → Linux Audio → DSP → ML Model → Classification → Decision

3. ACTUATOR CONTROL FLOW:
   Decision → Command Generator → JSON {"servo1": 90} → MCU Parser → PWM Output

4. USER INTERFACE FLOW:
   Web Request → Flask Handler → System State → JSON Response → Browser Update
```

## 🧠 AI/ML Architecture

### **Machine Learning Pipeline**
```
┌─────────────────────────────────────────────────────────────┐
│                    ML INFERENCE PIPELINE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Raw Audio Input                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                        │
│  │ Preprocessing   │ • Bandpass Filtering                   │
│  │                 │ • Noise Reduction                      │
│  │                 │ • Normalization                        │
│  └─────────────────┘                                        │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                        │
│  │ Feature         │ • Mel-Spectrogram                      │
│  │ Extraction      │ • MFCC Features                        │
│  │                 │ • Spectral Features                    │
│  │                 │ • Heart Rate Estimation                │
│  └─────────────────┘                                        │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                        │
│  │ Model           │ • Heart Sound CNN                      │
│  │ Inference       │ • Lung Sound CNN                       │
│  │                 │ • TensorFlow Lite                      │
│  │                 │ • Quantized INT8                       │
│  └─────────────────┘                                        │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                        │
│  │ Post-           │ • Confidence Scoring                   │
│  │ Processing      │ • Multi-frame Smoothing                │
│  │                 │ • Explainability                       │
│  └─────────────────┘                                        │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                        │
│  │ Sensor          │ • Audio + Temperature                  │
│  │ Fusion          │ • Movement Validation                  │
│  │                 │ • Distance Confirmation                │
│  │                 │ • Multi-modal Decision                 │
│  └─────────────────┘                                        │
│         │                                                   │
│         ▼                                                   │
│  Final Triage Decision                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Model Architecture Details**

#### **Heart Sound Classification Model**
```
Input: Mel-Spectrogram (64 x 128 x 1)
│
├─ Conv2D(16, 3x3, ReLU)
├─ MaxPool2D(2x2)
├─ Conv2D(32, 3x3, ReLU)
├─ MaxPool2D(2x2)
├─ Conv2D(32, 3x3, ReLU)
├─ GlobalAveragePooling2D()
├─ Dense(64, ReLU)
├─ Dropout(0.5)
└─ Dense(3, Softmax) → [Normal, Murmur, Arrhythmia]

Model Size: <2MB (quantized)
Inference Time: <100ms
Target Accuracy: >85%
```

#### **Lung Sound Classification Model**
```
Input: Mel-Spectrogram (64 x 128 x 1)
│
├─ Conv2D(16, 3x3, ReLU)
├─ MaxPool2D(2x2)
├─ Conv2D(32, 3x3, ReLU)
├─ MaxPool2D(2x2)
├─ Conv2D(64, 3x3, ReLU)
├─ GlobalAveragePooling2D()
├─ Dense(128, ReLU)
├─ Dropout(0.5)
└─ Dense(4, Softmax) → [Normal, Wheeze, Crackle, Stridor]

Model Size: <2MB (quantized)
Inference Time: <100ms
Target Accuracy: >80%
```

## 🔧 Development Environment Setup

### **Linux Side Development Environment**
```bash
# Python Environment Setup
python3 -m venv /opt/triage-station/venv
source /opt/triage-station/venv/bin/activate

# Core Dependencies
pip install numpy==1.24.3
pip install scipy==1.10.1
pip install scikit-learn==1.3.0
pip install pandas==2.0.3

# Audio Processing
pip install librosa==0.10.1
pip install sounddevice==0.4.6
pip install soundfile==0.12.1

# Machine Learning
pip install tensorflow==2.13.0
pip install tflite-runtime==2.13.0

# Web Framework
pip install flask==2.3.2
pip install flask-socketio==5.3.4

# Computer Vision
pip install opencv-python==4.8.0.74

# Communication
pip install pyserial==3.5

# Utilities
pip install pyyaml==6.0.1
pip install requests==2.31.0
```

### **MCU Side Development Environment**
```
Arduino IDE Configuration:
- Board: Arduino UNO Q
- Processor: STM32U585
- Upload Method: USB
- Libraries:
  - ArduinoJson (6.21.3)
  - Servo (1.2.1)
  - Wire (built-in)
  - SPI (built-in)
```

## 📁 Project Directory Structure

### **Complete File Organization**
```
smart-triage-station/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── setup.py
│
├── docs/                           # Documentation
│   ├── SOFTWARE_ARCHITECTURE_GUIDE.md
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   └── USER_MANUAL.md
│
├── firmware/                       # Arduino MCU Code
│   ├── main/
│   │   ├── main.ino               # Main Arduino sketch
│   │   ├── sensors.cpp            # Sensor management
│   │   ├── actuators.cpp          # Actuator control
│   │   ├── communication.cpp      # Serial communication
│   │   └── config.h               # Configuration constants
│   ├── tests/                     # Individual component tests
│   └── libraries/                 # Custom libraries
│
├── linux/                         # Linux Side Code
│   ├── core/                      # Core system modules
│   │   ├── __init__.py
│   │   ├── system_manager.py      # Main system controller
│   │   ├── state_machine.py       # System state management
│   │   ├── config_manager.py      # Configuration handling
│   │   └── logger.py              # Logging system
│   │
│   ├── hardware/                  # Hardware interfaces
│   │   ├── __init__.py
│   │   ├── serial_manager.py      # MCU communication
│   │   ├── camera_manager.py      # Camera interface
│   │   ├── audio_manager.py       # Audio capture
│   │   └── device_manager.py      # Device enumeration
│   │
│   ├── audio/                     # Audio processing
│   │   ├── __init__.py
│   │   ├── capture.py             # Audio capture
│   │   ├── preprocessing.py       # Signal processing
│   │   ├── features.py            # Feature extraction
│   │   ├── heart_analysis.py      # Heart sound analysis
│   │   ├── lung_analysis.py       # Lung sound analysis
│   │   └── visualization.py       # Audio visualization
│   │
│   ├── ml/                        # Machine Learning
│   │   ├── __init__.py
│   │   ├── inference_engine.py    # TFLite inference
│   │   ├── model_manager.py       # Model loading/management
│   │   ├── heart_classifier.py    # Heart sound classifier
│   │   ├── lung_classifier.py     # Lung sound classifier
│   │   └── explainability.py      # AI explainability
│   │
│   ├── triage/                    # Triage logic
│   │   ├── __init__.py
│   │   ├── decision_engine.py     # Main triage logic
│   │   ├── sensor_fusion.py       # Multi-modal fusion
│   │   ├── risk_assessment.py     # Risk scoring
│   │   └── recommendations.py     # Clinical recommendations
│   │
│   ├── calibration/               # Device calibration
│   │   ├── __init__.py
│   │   ├── audio_calibration.py   # Audio system calibration
│   │   ├── sensor_calibration.py  # Sensor calibration
│   │   └── calibration_manager.py # Calibration coordination
│   │
│   ├── web/                       # Web interface
│   │   ├── __init__.py
│   │   ├── app.py                 # Flask application
│   │   ├── api.py                 # REST API endpoints
│   │   ├── websocket.py           # Real-time communication
│   │   └── auth.py                # Authentication (if needed)
│   │
│   ├── utils/                     # Utilities
│   │   ├── __init__.py
│   │   ├── data_validation.py     # Data validation
│   │   ├── file_manager.py        # File operations
│   │   ├── network_utils.py       # Network utilities
│   │   └── math_utils.py          # Mathematical utilities
│   │
│   └── tests/                     # Python tests
│       ├── test_audio.py
│       ├── test_ml.py
│       ├── test_triage.py
│       └── test_integration.py
│
├── models/                        # ML Models
│   ├── heart/
│   │   ├── heart_model.tflite     # Heart sound model
│   │   ├── heart_model.json       # Model metadata
│   │   └── heart_scaler.pkl       # Feature scaler
│   ├── lung/
│   │   ├── lung_model.tflite      # Lung sound model
│   │   ├── lung_model.json        # Model metadata
│   │   └── lung_scaler.pkl        # Feature scaler
│   └── backup/                    # Model backups
│
├── data/                          # Data storage
│   ├── calibration/               # Calibration data
│   ├── logs/                      # System logs
│   ├── recordings/                # Audio recordings (if enabled)
│   └── exports/                   # Data exports
│
├── config/                        # Configuration files
│   ├── system.yaml                # Main system config
│   ├── audio.yaml                 # Audio configuration
│   ├── ml.yaml                    # ML configuration
│   ├── web.yaml                   # Web interface config
│   └── hardware.yaml              # Hardware configuration
│
├── web/                           # Web interface files
│   ├── static/                    # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/                 # HTML templates
│   │   ├── index.html
│   │   ├── dashboard.html
│   │   ├── calibration.html
│   │   └── demo.html
│   └── assets/                    # Additional assets
│
├── scripts/                       # Utility scripts
│   ├── install.sh                 # Installation script
│   ├── start.sh                   # System startup
│   ├── stop.sh                    # System shutdown
│   ├── backup.sh                  # Data backup
│   └── update.sh                  # System update
│
├── tools/                         # Development tools
│   ├── model_converter.py         # TensorFlow to TFLite
│   ├── data_collector.py          # Data collection tool
│   ├── system_monitor.py          # System monitoring
│   └── performance_test.py        # Performance testing
│
└── deployment/                    # Deployment files
    ├── systemd/                   # System service files
    ├── nginx/                     # Web server config
    ├── docker/                    # Docker containers (optional)
    └── ansible/                   # Deployment automation
```

## 🔄 Communication Protocol

### **JSON Message Format**
```json
// MCU to Linux - Sensor Data
{
  "timestamp": 1640995200000,
  "message_type": "sensor_data",
  "data": {
    "knob": {
      "raw_value": 512,
      "mode": 1,
      "voltage": 1.65
    },
    "distance": {
      "value_cm": 5.2,
      "valid": true,
      "in_range": true
    },
    "movement": {
      "detected": false,
      "stable_duration": 2500
    },
    "temperature": {
      "celsius": 36.8,
      "fahrenheit": 98.2,
      "valid": true
    }
  }
}

// Linux to MCU - Control Commands
{
  "timestamp": 1640995201000,
  "message_type": "control_command",
  "commands": {
    "servo1": {
      "angle": 90,
      "speed": "normal"
    },
    "servo2": {
      "angle": 135,
      "speed": "slow"
    },
    "buzzer": {
      "state": "ON",
      "frequency": 1000,
      "duration": 500
    },
    "relay": {
      "state": "OFF"
    },
    "led": {
      "state": "BLINK",
      "pattern": "fast"
    }
  }
}

// Linux to MCU - System Status
{
  "timestamp": 1640995202000,
  "message_type": "system_status",
  "status": {
    "state": "EXAMINING",
    "progress": 75,
    "remaining_time": 2000,
    "error": null
  }
}
```

### **Message Types and Purposes**
```
MCU → Linux Messages:
├── sensor_data        # Regular sensor readings
├── error_report       # Hardware errors
├── calibration_data   # Calibration measurements
├── heartbeat         # System alive signal
└── debug_info        # Debug information

Linux → MCU Messages:
├── control_command    # Actuator control
├── system_status     # System state updates
├── calibration_cmd   # Calibration commands
├── config_update     # Configuration changes
└── reset_command     # System reset
```

## 🎯 Key Software Features

### **1. Real-time Audio Processing**
- **Continuous audio capture** at 8kHz sampling rate
- **Real-time filtering** (bandpass, notch, noise reduction)
- **Feature extraction** (mel-spectrogram, MFCC, spectral features)
- **Heart rate estimation** using envelope detection
- **Streaming processing** with minimal latency

### **2. AI Inference Engine**
- **TensorFlow Lite** optimized for ARM processors
- **Quantized models** (INT8) for fast inference
- **Multi-model support** (heart sounds, lung sounds)
- **Confidence scoring** and uncertainty estimation
- **Explainable AI** with attention visualization

### **3. Multi-modal Sensor Fusion**
- **Data synchronization** across multiple sensors
- **Temporal alignment** of sensor readings
- **Weighted fusion** based on sensor reliability
- **Conflict resolution** when sensors disagree
- **Adaptive thresholds** based on conditions

### **4. Device Calibration System**
- **Audio calibration** for different microphones
- **Sensor calibration** for environmental conditions
- **Automatic calibration** routines
- **Calibration validation** and quality checks
- **Calibration data persistence**

### **5. Web-based User Interface**
- **Real-time dashboard** with live updates
- **Responsive design** for tablets and phones
- **Audio visualization** (waveforms, spectrograms)
- **Results display** with explanations
- **System configuration** interface

### **6. Data Management**
- **Secure data handling** (no audio storage by default)
- **Anonymized logging** for system monitoring
- **Export capabilities** for research (with consent)
- **Backup and recovery** systems
- **Data retention policies**

### **7. System Monitoring**
- **Performance monitoring** (CPU, memory, inference time)
- **Error tracking** and automatic recovery
- **Health checks** for all subsystems
- **Alert system** for critical issues
- **Remote diagnostics** capabilities

This comprehensive software architecture provides the foundation for building a professional-grade medical device with enterprise-level reliability and performance.

## 🚀 Next Steps

The following sections will provide detailed implementation of each component:

1. **Detailed Code Implementation** - Complete source code for all modules
2. **API Documentation** - REST API and WebSocket specifications  
3. **Deployment Guide** - Step-by-step deployment instructions
4. **Testing Framework** - Comprehensive testing procedures
5. **Performance Optimization** - Speed and accuracy improvements

Each section will include thousands of lines of production-ready code with extensive documentation and examples.