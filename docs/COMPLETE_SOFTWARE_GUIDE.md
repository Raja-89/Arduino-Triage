# 📚 Complete Software Implementation Guide

**Smart Rural Triage Station - Full Software Stack**

## 🎯 Overview

This document provides a complete overview of the software implementation for the Smart Rural Triage Station, covering all aspects from Arduino firmware to AI model deployment.

## 📦 Software Components

### 1. Arduino MCU Firmware (`firmware/main/main.ino`)

**Purpose**: Real-time sensor reading and actuator control

**Key Features**:
- JSON-based serial communication protocol
- Real-time sensor polling (100ms intervals)
- Servo motor control for visual feedback
- Buzzer control for audio alerts
- Movement and distance validation
- Temperature monitoring
- Heartbeat monitoring

**Communication Protocol**:
```json
// MCU → Linux: Sensor Data
{
  "timestamp": 1234567890,
  "message_type": "sensor_data",
  "data": {
    "knob": {"mode": 1, "raw_value": 512},
    "distance": {"value_cm": 5.2, "valid": true},
    "movement": {"detected": false},
    "temperature": {"celsius": 36.8}
  }
}

// Linux → MCU: Control Commands
{
  "timestamp": 1234567890,
  "message_type": "control_command",
  "commands": {
    "servo1": {"angle": 90},
    "buzzer": {"state": "ON", "frequency": 1000}
  }
}
```

### 2. System Manager (`linux/core/system_manager.py`)

**Purpose**: Main system orchestration and coordination

**Responsibilities**:
- Initialize all subsystems
- Manage system state transitions
- Coordinate between components
- Handle errors and recovery
- Monitor system health
- Manage examination workflow

**Key Methods**:
- `initialize()`: Setup all components
- `start_examination()`: Begin medical examination
- `stop_examination()`: End examination
- `shutdown()`: Graceful system shutdown

### 3. State Machine (`linux/core/state_machine.py`)

**Purpose**: Manage system operational states

**States**:
- `INITIALIZING`: System startup
- `IDLE`: Ready for examination
- `CALIBRATING`: Performing calibration
- `EXAMINING`: Active data capture
- `PROCESSING`: AI inference
- `SHOWING_RESULTS`: Display results
- `ERROR`: Error state
- `MAINTENANCE`: Maintenance mode
- `SHUTDOWN`: Shutting down

**State Transitions**:
```
INITIALIZING → IDLE
IDLE → EXAMINING → PROCESSING → SHOWING_RESULTS → IDLE
IDLE → CALIBRATING → IDLE
Any State → ERROR → IDLE
Any State → SHUTDOWN
```

### 4. Audio Processing Pipeline

#### Audio Capture (`linux/audio/capture.py`)
- Real-time audio streaming
- Configurable sample rate (8kHz default)
- Buffer management
- Callback-based processing

#### Preprocessing (`linux/audio/preprocessing.py`)
- Bandpass filtering (heart: 20-400Hz, lung: 100-2000Hz)
- Notch filtering (50Hz mains hum)
- Noise reduction
- Amplitude normalization

#### Feature Extraction (`linux/audio/features.py`)
- Mel-spectrogram computation
- MFCC extraction
- Spectral features
- Heart rate estimation
- Wheeze/crackle detection

#### Heart Sound Analysis (`linux/audio/heart_analysis.py`)
- S1/S2 detection
- Murmur analysis
- Heart rate calculation
- Quality metrics

#### Lung Sound Analysis (`linux/audio/lung_analysis.py`)
- Wheeze detection (continuous sounds)
- Crackle detection (explosive sounds)
- Respiratory rate estimation
- Breath sound analysis

### 5. Machine Learning Inference

#### Inference Engine (`linux/ml/inference_engine.py`)

**Purpose**: Run TensorFlow Lite models for classification

**Features**:
- TFLite model loading and management
- INT8 quantized inference
- Performance monitoring
- Confidence scoring
- Multi-model support

**Model Architecture**:
```python
# Heart Sound Model
Input: (64, 128, 1) mel-spectrogram
├─ Conv2D(16, 3x3) + BatchNorm + MaxPool
├─ Conv2D(32, 3x3) + BatchNorm + MaxPool
├─ Conv2D(32, 3x3) + BatchNorm + GlobalAvgPool
├─ Dense(64) + Dropout(0.5)
└─ Dense(3, softmax) → [Normal, Murmur, Extrasystole]

Output: Class probabilities + confidence score
Model Size: <2MB (quantized)
Inference Time: <100ms
```

**Usage Example**:
```python
# Initialize engine
engine = InferenceEngine(
    heart_model_path='/path/to/heart_model.tflite',
    lung_model_path='/path/to/lung_model.tflite'
)
await engine.initialize()

# Run inference
result = await engine.classify_heart_sound(mel_spectrogram)
# Returns: {
#   'predicted_class': 'Normal',
#   'confidence': 0.92,
#   'probabilities': {...},
#   'inference_time_ms': 87.3
# }
```

### 6. Triage Decision Engine

#### Decision Engine (`linux/triage/decision_engine.py`)

**Purpose**: Multi-modal sensor fusion and risk assessment

**Decision Process**:
1. Analyze ML predictions (heart/lung)
2. Evaluate vital signs (temperature, movement)
3. Calculate weighted risk scores
4. Determine risk level (LOW/MEDIUM/HIGH)
5. Generate recommendations
6. Create explainable reasoning

**Risk Scoring**:
```python
# Weighted fusion
overall_risk = (
    ml_prediction_score * 0.5 +
    audio_analysis_score * 0.3 +
    vital_signs_score * 0.2
)

# Risk levels
if overall_risk >= 0.7: risk_level = 'HIGH'
elif overall_risk >= 0.4: risk_level = 'MEDIUM'
else: risk_level = 'LOW'
```

**Output Example**:
```json
{
  "risk_level": "MEDIUM",
  "risk_score": 0.52,
  "risk_factors": [
    "Abnormal heart sound detected: Murmur",
    "Fever detected: 38.2°C"
  ],
  "recommendations": [
    "Cardiac auscultation by physician recommended",
    "Fever management and infection workup"
  ],
  "explanation": "MEDIUM RISK: Some abnormalities detected...",
  "requires_referral": true,
  "urgency": "ROUTINE",
  "confidence": 0.85
}
```

### 7. Hardware Interfaces

#### Serial Manager (`linux/hardware/serial_manager.py`)
- Bidirectional JSON communication
- Auto-reconnection
- Message queuing
- Error handling
- Statistics tracking

#### Camera Manager (`linux/hardware/camera_manager.py`)
- Video capture
- Frame processing
- Position detection
- Image capture

#### Audio Manager (`linux/hardware/audio_manager.py`)
- Device enumeration
- Stream management
- Format conversion
- Buffer handling

### 8. Calibration System

#### Calibration Manager (`linux/calibration/calibration_manager.py`)

**Purpose**: Device-specific calibration

**Calibration Types**:
1. **Audio Calibration**
   - Ambient noise measurement
   - Microphone response characterization
   - Gain correction calculation
   - Frequency response equalization

2. **Sensor Calibration**
   - Distance sensor offset
   - Temperature sensor offset
   - Movement sensitivity adjustment

**Calibration Workflow**:
```python
# Perform calibration
calibration_manager = CalibrationManager()
await calibration_manager.initialize()

# Full calibration
results = await calibration_manager.perform_full_calibration()

# Results stored in config/calibration.json
# Applied automatically during inference
```

### 9. Web Interface

#### Flask Application (`linux/web/app.py`)

**Endpoints**:
- `GET /`: Main dashboard
- `GET /api/status`: System status
- `POST /api/examination/start`: Start examination
- `POST /api/examination/stop`: Stop examination
- `GET /api/results`: Get latest results
- `GET /api/metrics`: Performance metrics
- `WebSocket /ws`: Real-time updates

**Dashboard Features**:
- Live camera feed with positioning overlay
- Real-time audio waveform/spectrogram
- Mode selection interface
- Results display with explanations
- System status indicators
- Performance metrics

## 🔄 Complete Examination Workflow

### Step-by-Step Process

1. **System Idle**
   - Status LED slow blink
   - Waiting for mode selection
   - Monitoring sensors

2. **Mode Selection**
   - User rotates knob
   - MCU reads knob position
   - Sends mode to Linux
   - Display updates

3. **Positioning**
   - Camera detects stethoscope
   - Distance sensor validates placement
   - Visual guidance on screen
   - Servo indicates readiness

4. **Examination Start**
   - User confirms start
   - System checks:
     - Distance in range
     - Patient still (no movement)
     - Audio system ready
   - Buzzer confirmation beep

5. **Audio Capture** (8 seconds)
   - Real-time audio streaming
   - Progress servo moves 0° → 180°
   - Waveform displayed on screen
   - Movement monitoring active

6. **Signal Processing**
   - Bandpass filtering
   - Noise reduction
   - Feature extraction
   - Mel-spectrogram generation

7. **ML Inference**
   - Load appropriate model (heart/lung)
   - Run TFLite inference
   - Calculate confidence scores
   - Generate predictions

8. **Triage Decision**
   - Combine ML results
   - Analyze vital signs
   - Calculate risk score
   - Determine risk level
   - Generate recommendations

9. **Results Display**
   - Result servo position:
     - 45° = LOW risk (green)
     - 90° = MEDIUM risk (yellow)
     - 135° = HIGH risk (red)
   - Buzzer pattern:
     - 1 beep = LOW
     - 2 beeps = MEDIUM
     - 3 beeps = HIGH
   - Relay triggers if HIGH risk
   - Web interface shows detailed results

10. **Return to Idle**
    - Display results for 10 seconds
    - Reset actuators
    - Clear examination data
    - Ready for next examination

## 🎓 ML Training Pipeline

### Complete Training Workflow

1. **Dataset Preparation**
   ```bash
   # Download datasets
   python ml/scripts/download_datasets.py
   
   # Preprocess audio
   python ml/scripts/preprocess_audio.py
   
   # Extract features
   python ml/scripts/extract_features.py
   ```

2. **Model Training**
   ```bash
   # Train heart sound model
   python ml/scripts/train_heart_model.py
   
   # Train lung sound model
   python ml/scripts/train_lung_model.py
   ```

3. **Model Optimization**
   ```bash
   # Convert to TFLite with INT8 quantization
   python ml/scripts/convert_to_tflite.py
   
   # Benchmark performance
   python ml/scripts/benchmark_model.py
   ```

4. **Model Deployment**
   ```bash
   # Copy to device
   scp models/heart_model.tflite root@192.168.7.2:/opt/triage-station/models/heart/
   scp models/lung_model.tflite root@192.168.7.2:/opt/triage-station/models/lung/
   
   # Restart service
   ssh root@192.168.7.2 "systemctl restart triage-station"
   ```

### Model Performance Targets

**Heart Sound Model**:
- Accuracy: >85%
- Sensitivity: >90% (abnormal detection)
- Specificity: >85%
- Inference Time: <100ms
- Model Size: <2MB

**Lung Sound Model**:
- Accuracy: >80%
- Sensitivity: >85% (abnormal detection)
- Specificity: >80%
- Inference Time: <100ms
- Model Size: <2MB

## 🔧 Configuration Management

### System Configuration (`config/system.yaml`)

All system parameters are configurable:
- Hardware settings (ports, devices)
- Audio parameters (sample rate, buffer size)
- ML thresholds (confidence, risk levels)
- Triage weights (sensor fusion)
- Web interface settings
- Logging configuration

### Runtime Configuration Updates

```python
# Load configuration
config_manager = ConfigManager('config/system.yaml')
config = config_manager.get_config()

# Update configuration
config_manager.update_config('ml.confidence_threshold', 0.8)

# Reload without restart
config_manager.reload()
```

## 📊 Performance Monitoring

### System Metrics

- CPU usage
- Memory usage
- Inference time
- Audio latency
- Frame rate
- Error rate
- Uptime

### Application Metrics

- Examinations per hour
- Average inference time
- Model accuracy (if ground truth available)
- System availability
- Error frequency

### Logging

```python
# Structured logging
logger.info("Examination started", extra={
    'mode': 'heart',
    'patient_id': 'anonymous',
    'timestamp': datetime.now()
})

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Logs stored in: /opt/triage-station/logs/
```

## 🚀 Deployment Checklist

- [ ] Hardware assembled and tested
- [ ] MCU firmware uploaded
- [ ] Linux system updated
- [ ] Python dependencies installed
- [ ] Application code deployed
- [ ] ML models deployed
- [ ] Configuration customized
- [ ] Calibration performed
- [ ] System tests passing
- [ ] Web interface accessible
- [ ] Systemd service running
- [ ] Logs being written
- [ ] Documentation reviewed
- [ ] User training completed

## 📚 Additional Resources

- **Hardware Guide**: `docs/PHASE_1_HARDWARE.md`
- **Audio Pipeline**: `docs/PHASE_2_AUDIO.md`
- **ML Training**: `docs/ML_TRAINING_GUIDE.md`
- **Deployment**: `docs/COMPLETE_DEPLOYMENT_GUIDE.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`

---

**This completes the comprehensive software implementation guide. All components are production-ready and fully documented.**
