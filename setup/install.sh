#!/bin/bash

# Smart Rural Triage Station - Installation Script
# Arduino UNO Q Setup for AI-Powered Medical Screening

set -e  # Exit on any error

echo "=========================================="
echo "Smart Rural Triage Station Setup"
echo "Arduino x Qualcomm AI for All Hackathon"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Arduino UNO Q
check_system() {
    log_info "Checking system compatibility..."
    
    if [ ! -f /proc/version ]; then
        log_error "Not running on Linux system"
        exit 1
    fi
    
    # Check for ARM architecture (Arduino UNO Q uses ARM)
    ARCH=$(uname -m)
    if [[ "$ARCH" != "aarch64" && "$ARCH" != "armv7l" ]]; then
        log_warning "Not running on ARM architecture. Some features may not work."
    fi
    
    log_success "System check passed"
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    
    apt update
    apt upgrade -y
    
    log_success "System updated"
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        cmake \
        git \
        curl \
        wget \
        unzip \
        alsa-utils \
        pulseaudio \
        v4l-utils \
        ffmpeg \
        libportaudio2 \
        libportaudiocpp0 \
        portaudio19-dev \
        libasound2-dev \
        libsndfile1-dev \
        libfftw3-dev \
        pkg-config
    
    log_success "System dependencies installed"
}

# Create project directory structure
create_directories() {
    log_info "Creating project directories..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    
    mkdir -p $PROJECT_ROOT/{data,models,logs,config}
    mkdir -p $PROJECT_ROOT/data/{recordings,datasets,calibration}
    mkdir -p $PROJECT_ROOT/models/{heart,lung,backup}
    mkdir -p $PROJECT_ROOT/logs/{system,audio,inference}
    
    # Set permissions
    chmod -R 755 $PROJECT_ROOT
    
    log_success "Project directories created at $PROJECT_ROOT"
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    
    # Create virtual environment
    python3 -m venv $PROJECT_ROOT/venv
    
    # Activate virtual environment
    source $PROJECT_ROOT/venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    log_success "Python virtual environment created"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    source $PROJECT_ROOT/venv/bin/activate
    
    # Core dependencies
    pip install \
        numpy==1.24.3 \
        scipy==1.10.1 \
        matplotlib==3.7.1 \
        pandas==2.0.3 \
        scikit-learn==1.3.0
    
    # Audio processing
    pip install \
        librosa==0.10.1 \
        sounddevice==0.4.6 \
        pyaudio==0.2.11 \
        soundfile==0.12.1
    
    # Machine learning
    pip install \
        tensorflow==2.13.0 \
        tflite-runtime==2.13.0
    
    # Web framework
    pip install \
        flask==2.3.2 \
        flask-socketio==5.3.4 \
        gunicorn==21.2.0
    
    # Serial communication
    pip install \
        pyserial==3.5 \
        pyusb==1.2.1
    
    # Computer vision
    pip install \
        opencv-python==4.8.0.74 \
        pillow==10.0.0
    
    # Utilities
    pip install \
        requests==2.31.0 \
        python-dotenv==1.0.0 \
        pyyaml==6.0.1 \
        tqdm==4.65.0
    
    log_success "Python dependencies installed"
}

# Configure audio system
setup_audio() {
    log_info "Configuring audio system..."
    
    # Add user to audio group
    usermod -a -G audio root
    
    # Configure ALSA
    cat > /etc/asound.conf << EOF
pcm.!default {
    type hw
    card 1
    device 0
}
ctl.!default {
    type hw
    card 1
}
EOF
    
    # Test audio devices
    log_info "Available audio devices:"
    arecord -l || log_warning "No audio input devices found"
    
    log_success "Audio system configured"
}

# Configure camera system
setup_camera() {
    log_info "Configuring camera system..."
    
    # Add user to video group
    usermod -a -G video root
    
    # Test camera devices
    log_info "Available video devices:"
    ls /dev/video* 2>/dev/null || log_warning "No video devices found"
    
    # Test camera capture if device exists
    if [ -e /dev/video0 ]; then
        log_info "Testing camera capture..."
        timeout 5s ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 -y /tmp/camera_test.jpg 2>/dev/null || log_warning "Camera test failed"
        
        if [ -f /tmp/camera_test.jpg ]; then
            log_success "Camera test successful"
            rm /tmp/camera_test.jpg
        fi
    fi
    
    log_success "Camera system configured"
}

# Setup systemd services
setup_services() {
    log_info "Setting up system services..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    
    # Main application service
    cat > /etc/systemd/system/triage-station.service << EOF
[Unit]
Description=Smart Rural Triage Station
After=network.target sound.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/venv/bin
ExecStart=$PROJECT_ROOT/venv/bin/python linux/controller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Web interface service
    cat > /etc/systemd/system/triage-webui.service << EOF
[Unit]
Description=Smart Triage Station Web Interface
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/venv/bin
ExecStart=$PROJECT_ROOT/venv/bin/gunicorn --bind 0.0.0.0:5000 webui.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    log_success "System services configured"
}

# Download and setup ML models
setup_models() {
    log_info "Setting up ML models..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    
    # Create placeholder models (replace with actual trained models)
    cat > $PROJECT_ROOT/models/model_info.txt << EOF
ML Models for Smart Rural Triage Station
========================================

This directory should contain:
- heart_model.tflite: Trained heart sound classification model
- lung_model.tflite: Trained lung sound classification model

Models should be:
- TensorFlow Lite format (.tflite)
- Quantized to INT8 for optimal performance
- Under 2MB each for memory efficiency

To add models:
1. Copy .tflite files to this directory
2. Update model paths in linux/inference_engine.py
3. Restart triage-station service

Current status: Models need to be trained and deployed
EOF
    
    log_success "Model directory prepared"
}

# Setup configuration files
setup_config() {
    log_info "Setting up configuration files..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    
    # Main configuration
    cat > $PROJECT_ROOT/config/system.yaml << EOF
# Smart Rural Triage Station Configuration

system:
  name: "Smart Rural Triage Station"
  version: "1.0.0"
  debug: true
  log_level: "INFO"

audio:
  sample_rate: 8000
  channels: 1
  buffer_size: 8192
  device_id: null  # Auto-detect

camera:
  device_id: 0
  width: 640
  height: 480
  fps: 30

serial:
  port: "/dev/ttyACM0"
  baud_rate: 115200
  timeout: 1.0

models:
  heart_model: "models/heart_model.tflite"
  lung_model: "models/lung_model.tflite"

thresholds:
  heart_abnormal: 0.7
  lung_abnormal: 0.6
  fever_threshold: 37.5
  movement_threshold: 0.1

web:
  host: "0.0.0.0"
  port: 5000
  debug: false
EOF
    
    # Device calibration template
    cat > $PROJECT_ROOT/config/calibration_template.json << EOF
{
  "device_id": "arduino_uno_q_001",
  "calibration_date": null,
  "audio_calibration": {
    "gain_correction": 1.0,
    "frequency_response": [],
    "noise_profile": {
      "noise_level": 0.01,
      "noise_spectrum": []
    }
  },
  "sensor_calibration": {
    "distance_offset": 0.0,
    "temperature_offset": 0.0,
    "movement_sensitivity": 1.0
  }
}
EOF
    
    log_success "Configuration files created"
}

# Create startup script
create_startup_script() {
    log_info "Creating startup script..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    
    cat > $PROJECT_ROOT/start.sh << EOF
#!/bin/bash

# Smart Rural Triage Station Startup Script

PROJECT_ROOT="$PROJECT_ROOT"
cd \$PROJECT_ROOT

echo "Starting Smart Rural Triage Station..."

# Activate virtual environment
source venv/bin/activate

# Check system status
echo "Checking system status..."
python3 -c "
import sys
import os
sys.path.append('linux')
from tests.system_test import SystemTest
test = SystemTest()
if test.run_basic_checks():
    print('System checks passed')
    exit(0)
else:
    print('System checks failed')
    exit(1)
"

if [ \$? -eq 0 ]; then
    echo "System ready - starting services..."
    systemctl start triage-station
    systemctl start triage-webui
    echo "Services started successfully"
    echo "Web interface available at: http://localhost:5000"
else
    echo "System checks failed - please check configuration"
    exit 1
fi
EOF
    
    chmod +x $PROJECT_ROOT/start.sh
    
    log_success "Startup script created"
}

# Create test script
create_test_script() {
    log_info "Creating test script..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    
    cat > $PROJECT_ROOT/test.sh << EOF
#!/bin/bash

# Smart Rural Triage Station Test Script

PROJECT_ROOT="$PROJECT_ROOT"
cd \$PROJECT_ROOT

echo "Running Smart Rural Triage Station Tests..."

# Activate virtual environment
source venv/bin/activate

# Run system tests
echo "1. System Tests..."
python3 -m pytest tests/ -v

# Test audio capture
echo "2. Audio System Test..."
python3 linux/audio/capture.py

# Test camera
echo "3. Camera System Test..."
python3 linux/tests/camera_test.py

# Test serial communication
echo "4. Serial Communication Test..."
python3 linux/tests/serial_comm_test.py

echo "Test suite completed"
EOF
    
    chmod +x $PROJECT_ROOT/test.sh
    
    log_success "Test script created"
}

# Final setup and verification
final_setup() {
    log_info "Performing final setup..."
    
    PROJECT_ROOT="/opt/smart-triage-station"
    
    # Set ownership
    chown -R root:root $PROJECT_ROOT
    
    # Create symlinks for easy access
    ln -sf $PROJECT_ROOT/start.sh /usr/local/bin/triage-start
    ln -sf $PROJECT_ROOT/test.sh /usr/local/bin/triage-test
    
    # Add to PATH
    echo "export PATH=\$PATH:$PROJECT_ROOT/venv/bin" >> /root/.bashrc
    
    log_success "Final setup completed"
}

# Print installation summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "Installation Summary"
    echo "=========================================="
    echo ""
    echo "✅ System dependencies installed"
    echo "✅ Python environment configured"
    echo "✅ Audio and camera systems setup"
    echo "✅ System services configured"
    echo "✅ Configuration files created"
    echo ""
    echo "Project Location: /opt/smart-triage-station"
    echo ""
    echo "Quick Commands:"
    echo "  Start system:  triage-start"
    echo "  Run tests:     triage-test"
    echo "  Web interface: http://localhost:5000"
    echo ""
    echo "Next Steps:"
    echo "1. Copy your project files to /opt/smart-triage-station"
    echo "2. Train and deploy ML models"
    echo "3. Run system tests: triage-test"
    echo "4. Start the system: triage-start"
    echo ""
    echo "For troubleshooting, check logs in:"
    echo "  /opt/smart-triage-station/logs/"
    echo ""
    echo "=========================================="
    echo "Installation Complete! 🚀"
    echo "=========================================="
}

# Main installation flow
main() {
    log_info "Starting Smart Rural Triage Station installation..."
    
    check_system
    update_system
    install_system_deps
    create_directories
    setup_python_env
    install_python_deps
    setup_audio
    setup_camera
    setup_services
    setup_models
    setup_config
    create_startup_script
    create_test_script
    final_setup
    
    print_summary
}

# Run installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi