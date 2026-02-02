# 🚀 Complete Deployment Guide

**Smart Rural Triage Station - Full System Deployment**

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Hardware Setup](#hardware-setup)
3. [Software Installation](#software-installation)
4. [Model Deployment](#model-deployment)
5. [System Configuration](#system-configuration)
6. [Testing and Validation](#testing-and-validation)
7. [Troubleshooting](#troubleshooting)

## ✅ Pre-Deployment Checklist

### Hardware Requirements
- [ ] Arduino UNO Q board
- [ ] Logitech Brio 100 webcam
- [ ] All Modulino sensors (knob, distance, movement, thermo, buzzer, relay)
- [ ] 2x Servo motors
- [ ] MAX9814 microphone module
- [ ] Jumper wires and breadboard
- [ ] USB-C cable and power adapter (20W+)
- [ ] MicroSD card (optional, 32GB+)

### Software Requirements
- [ ] Arduino IDE 2.x installed
- [ ] Python 3.9+ installed
- [ ] SSH client (built-in on Linux/Mac, PuTTY on Windows)
- [ ] Web browser (Chrome/Firefox recommended)

### Network Requirements
- [ ] USB connection to Arduino UNO Q
- [ ] (Optional) WiFi network for remote access

## 🔧 Hardware Setup

### Step 1: Component Assembly

Follow the detailed wiring diagram in `hardware/pinmap.md`:

```
MCU Side Connections:
├── A0  → Modulino Knob (Signal)
├── D2  → Distance Sensor (Trigger)
├── D3  → Distance Sensor (Echo)
├── D4  → Movement Sensor (Signal)
├── D5  → Buzzer (Signal)
├── D6  → Relay (Control)
├── D9  → Servo 1 (Progress)
├── D10 → Servo 2 (Result)
├── D13 → Status LED
├── SDA → Temperature Sensor (I2C Data)
└── SCL → Temperature Sensor (I2C Clock)

Power Distribution:
├── 5V  → Servos, Distance Sensor, Relay
├── 3.3V → Modulino Sensors, Microphone
└── GND → Common ground for ALL components
```

**CRITICAL**: Ensure all components share a common ground connection!

### Step 2: Physical Assembly

1. **Mount Arduino UNO Q** on a stable base
2. **Connect Modulino sensors** using provided cables
3. **Attach servos** to mounting brackets
4. **Position camera** for optimal viewing angle
5. **Secure microphone** for stethoscope connection
6. **Verify all connections** before powering on

### Step 3: Power-On Test

1. Connect USB-C cable to Arduino UNO Q
2. Observe power LED (should light up)
3. Wait 90-120 seconds for Linux boot
4. Check status LED blinking pattern

## 💻 Software Installation

### Step 1: Connect to Arduino UNO Q

**Via USB Network:**
```bash
# Find the IP address (usually 192.168.7.2)
ping 192.168.7.2

# Connect via SSH
ssh root@192.168.7.2
# Password: (usually none, just press Enter)
```

**Via Serial Console:**
```bash
# On Linux/Mac
screen /dev/ttyACM0 115200

# On Windows (using PuTTY)
# Port: COM3 (check Device Manager)
# Speed: 115200
```

### Step 2: System Update

```bash
# Update package lists
apt update

# Upgrade system packages
apt upgrade -y

# Install essential tools
apt install -y git vim htop
```

### Step 3: Install Python Dependencies

```bash
# Create project directory
mkdir -p /opt/triage-station
cd /opt/triage-station

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install numpy==1.24.3
pip install scipy==1.10.1
pip install scikit-learn==1.3.0
pip install tensorflow==2.13.0
pip install tflite-runtime==2.13.0
pip install librosa==0.10.1
pip install sounddevice==0.4.6
pip install soundfile==0.12.1
pip install opencv-python==4.8.0.74
pip install flask==2.3.2
pip install flask-socketio==5.3.4
pip install pyserial==3.5
pip install pyyaml==6.0.1
```

### Step 4: Deploy Application Code

**Option A: From Git Repository**
```bash
cd /opt/triage-station
git clone https://github.com/your-repo/smart-triage-station.git .
```

**Option B: Manual File Transfer**
```bash
# On your computer
scp -r linux/ root@192.168.7.2:/opt/triage-station/
scp -r config/ root@192.168.7.2:/opt/triage-station/
scp -r web/ root@192.168.7.2:/opt/triage-station/
```

### Step 5: Upload MCU Firmware

1. Open Arduino IDE
2. Install Arduino UNO Q board support:
   - Go to Tools → Board → Boards Manager
   - Search for "Arduino UNO Q"
   - Install the board package

3. Open `firmware/main/main.ino`
4. Select board: Tools → Board → Arduino UNO Q
5. Select port: Tools → Port → (your Arduino port)
6. Click Upload button

7. Verify upload:
   - Open Serial Monitor (115200 baud)
   - You should see startup messages

## 🤖 Model Deployment

### Step 1: Train Models (if not using pre-trained)

```bash
# On your development machine
cd ml/

# Download datasets
python scripts/download_datasets.py

# Preprocess audio
python scripts/preprocess_audio.py

# Extract features
python scripts/extract_features.py

# Train heart sound model
python scripts/train_heart_model.py

# Train lung sound model
python scripts/train_lung_model.py

# Convert to TFLite
python scripts/convert_to_tflite.py
```

### Step 2: Deploy Models to Device

```bash
# Create model directories on device
ssh root@192.168.7.2 "mkdir -p /opt/triage-station/models/heart /opt/triage-station/models/lung"

# Copy heart sound model
scp ml/models/heart/tflite/heart_model.tflite root@192.168.7.2:/opt/triage-station/models/heart/

# Copy lung sound model
scp ml/models/lung/tflite/lung_model.tflite root@192.168.7.2:/opt/triage-station/models/lung/

# Copy model metadata
scp ml/models/heart/heart_model.json root@192.168.7.2:/opt/triage-station/models/heart/
scp ml/models/lung/lung_model.json root@192.168.7.2:/opt/triage-station/models/lung/
```

### Step 3: Verify Model Deployment

```bash
ssh root@192.168.7.2

# Check model files
ls -lh /opt/triage-station/models/heart/
ls -lh /opt/triage-station/models/lung/

# Test model loading
cd /opt/triage-station
source venv/bin/activate
python3 -c "import tensorflow as tf; print(tf.lite.Interpreter(model_path='models/heart/heart_model.tflite'))"
```

## ⚙️ System Configuration

### Step 1: Configure System Settings

Edit `/opt/triage-station/config/system.yaml`:

```yaml
# System Configuration
system:
  name: "Smart Rural Triage Station"
  version: "1.0.0"
  location: "Rural Health Clinic"

# Hardware Configuration
hardware:
  serial:
    port: "/dev/ttyACM0"
    baud_rate: 115200
    timeout: 1.0
  
  camera:
    device_id: 0
    width: 640
    height: 480
    fps: 30
  
  audio:
    device_id: null  # Auto-detect
    sample_rate: 8000
    channels: 1
    buffer_size: 8192

# ML Configuration
ml:
  heart_model_path: "/opt/triage-station/models/heart/heart_model.tflite"
  lung_model_path: "/opt/triage-station/models/lung/lung_model.tflite"
  confidence_threshold: 0.7

# Triage Configuration
triage:
  thresholds:
    ml_confidence: 0.7
    temperature_fever: 38.0
    heart_rate_high: 100
    heart_rate_low: 50
    respiratory_rate_high: 25
    respiratory_rate_low: 10
  
  fusion_weights:
    ml_prediction: 0.5
    audio_analysis: 0.3
    vital_signs: 0.2

# Web Interface Configuration
web:
  host: "0.0.0.0"
  port: 5000
  debug: false

# Logging Configuration
logging:
  level: "INFO"
  file: "/opt/triage-station/logs/system.log"
  max_size: 10485760  # 10MB
  backup_count: 5

# Calibration Configuration
calibration:
  audio_enabled: true
  sensor_enabled: true
  auto_interval: 3600  # 1 hour

# Examination Configuration
examination:
  duration: 8.0  # seconds
  result_display_time: 10.0  # seconds
```

### Step 2: Create Systemd Service

Create `/etc/systemd/system/triage-station.service`:

```ini
[Unit]
Description=Smart Rural Triage Station
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/triage-station
Environment="PATH=/opt/triage-station/venv/bin"
ExecStart=/opt/triage-station/venv/bin/python3 /opt/triage-station/linux/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
systemctl daemon-reload
systemctl enable triage-station
systemctl start triage-station
systemctl status triage-station
```

### Step 3: Configure Firewall (if needed)

```bash
# Allow web interface access
ufw allow 5000/tcp

# Allow SSH
ufw allow 22/tcp

# Enable firewall
ufw enable
```

## 🧪 Testing and Validation

### Step 1: Hardware Tests

```bash
cd /opt/triage-station
source venv/bin/activate

# Test serial communication
python3 tests/test_serial.py

# Test camera
python3 tests/test_camera.py

# Test audio
python3 tests/test_audio.py

# Test sensors
python3 tests/test_sensors.py
```

### Step 2: ML Inference Tests

```bash
# Test heart sound model
python3 tests/test_heart_inference.py

# Test lung sound model
python3 tests/test_lung_inference.py

# Benchmark performance
python3 tests/benchmark_inference.py
```

### Step 3: End-to-End System Test

```bash
# Run full system test
python3 tests/system_test.py

# Expected output:
# ✓ Serial communication: OK
# ✓ Camera: OK
# ✓ Audio capture: OK
# ✓ ML inference: OK
# ✓ Triage decision: OK
# ✓ Web interface: OK
```

### Step 4: Web Interface Test

1. Open browser and navigate to: `http://192.168.7.2:5000`
2. Verify dashboard loads correctly
3. Test mode selection (knob)
4. Test examination workflow
5. Verify results display

## 🔍 Troubleshooting

### Common Issues

**Issue: Cannot connect via SSH**
```bash
# Check USB connection
lsusb

# Check network interface
ip addr show

# Try alternative IP addresses
ping 192.168.42.1
ping 10.42.0.1
```

**Issue: Serial communication fails**
```bash
# Check serial port
ls -l /dev/ttyACM*

# Check permissions
sudo usermod -a -G dialout $USER

# Test serial connection
screen /dev/ttyACM0 115200
```

**Issue: Audio not working**
```bash
# List audio devices
arecord -l

# Test audio recording
arecord -D hw:1,0 -f cd -t wav -d 5 test.wav

# Check audio levels
alsamixer
```

**Issue: Models not loading**
```bash
# Check model files
ls -lh /opt/triage-station/models/

# Test TFLite runtime
python3 -c "import tflite_runtime.interpreter as tflite; print('OK')"

# Check model format
file /opt/triage-station/models/heart/heart_model.tflite
```

**Issue: High CPU usage**
```bash
# Monitor system resources
htop

# Check running processes
ps aux | grep python

# Reduce inference frequency if needed
# Edit config/system.yaml and increase examination duration
```

### Log Files

Check logs for detailed error information:
```bash
# System log
tail -f /opt/triage-station/logs/system.log

# Service log
journalctl -u triage-station -f

# Kernel log
dmesg | tail
```

## 📊 Performance Monitoring

### System Metrics

```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Temperature
cat /sys/class/thermal/thermal_zone*/temp

# Network statistics
ifconfig
```

### Application Metrics

Access metrics via web interface:
- Dashboard: `http://192.168.7.2:5000/dashboard`
- Metrics: `http://192.168.7.2:5000/api/metrics`
- Status: `http://192.168.7.2:5000/api/status`

## 🔄 Updates and Maintenance

### Software Updates

```bash
# Update system packages
apt update && apt upgrade -y

# Update Python packages
pip install --upgrade -r requirements.txt

# Update application code
cd /opt/triage-station
git pull origin main

# Restart service
systemctl restart triage-station
```

### Model Updates

```bash
# Backup current models
cp -r /opt/triage-station/models /opt/triage-station/models.backup

# Deploy new models
scp new_heart_model.tflite root@192.168.7.2:/opt/triage-station/models/heart/heart_model.tflite

# Restart service
systemctl restart triage-station

# Verify new models
python3 tests/test_heart_inference.py
```

### Database Backup (if applicable)

```bash
# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz /opt/triage-station/logs/

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz /opt/triage-station/config/

# Copy to external storage
scp *.tar.gz user@backup-server:/backups/
```

## 🎯 Production Checklist

Before deploying to production:

- [ ] All hardware tests passing
- [ ] All software tests passing
- [ ] Models achieving target accuracy
- [ ] Web interface accessible
- [ ] Systemd service running
- [ ] Logs being written correctly
- [ ] Calibration completed
- [ ] User training completed
- [ ] Documentation reviewed
- [ ] Backup procedures in place
- [ ] Emergency contacts configured
- [ ] Maintenance schedule established

## 📞 Support

For technical support:
- Email: support@triage-station.example.com
- Documentation: https://docs.triage-station.example.com
- Issue Tracker: https://github.com/your-repo/smart-triage-station/issues

---

**Deployment Complete! Your Smart Rural Triage Station is ready for use.**
