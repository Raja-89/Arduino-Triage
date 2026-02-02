#!/usr/bin/env python3
"""
Smart Rural Triage Station - System Manager
===========================================

This is the main system controller that orchestrates all components of the
triage station. It manages the state machine, coordinates between different
subsystems, and ensures reliable operation.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
import signal
import sys
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from enum import Enum
import json
import yaml

from .state_machine import SystemStateMachine, SystemState
from .config_manager import ConfigManager
from .logger import setup_logging
try:
    from ..hardware.serial_manager import SerialManager
except ImportError:
    SerialManager = None

try:
    from ..hardware.camera_manager import CameraManager
except ImportError:
    CameraManager = None

try:
    from ..hardware.audio_manager import AudioManager
except ImportError:
    AudioManager = None

try:
    from ..audio.capture import AudioCapture
except ImportError:
    AudioCapture = None

try:
    from ..ml.inference_engine import InferenceEngine
except ImportError:
    InferenceEngine = None

try:
    from ..triage.decision_engine import TriageDecisionEngine
except ImportError:
    TriageDecisionEngine = None

try:
    from ..calibration.calibration_manager import CalibrationManager
except ImportError:
    CalibrationManager = None

try:
    from ..web.app import create_web_app
except ImportError:
    create_web_app = None


class SystemManager:
    """
    Main system manager that coordinates all subsystems.
    
    This class is responsible for:
    - System initialization and shutdown
    - State management and transitions
    - Inter-component communication
    - Error handling and recovery
    - Performance monitoring
    """
    
    def __init__(self, config_path: str = "/opt/triage-station/config/system.yaml"):
        """
        Initialize the system manager.
        
        Args:
            config_path: Path to the main configuration file
        """
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Setup logging
        self.logger = setup_logging(
            level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.config.get('logging', {}).get('file', '/opt/triage-station/logs/system.log')
        )
        
        # System components
        self.state_machine = SystemStateMachine()
        self.serial_manager = None
        self.camera_manager = None
        self.audio_manager = None
        self.audio_capture = None
        self.inference_engine = None
        self.triage_engine = None
        self.calibration_manager = None
        self.web_app = None
        
        # Hardware flags
        self.audio_enabled = False
        self.camera_enabled = False
        
        # System state
        self.running = False
        self.startup_time = None
        self.last_heartbeat = None
        self.error_count = 0
        self.performance_stats = {
            'total_examinations': 0,
            'successful_examinations': 0,
            'average_inference_time': 0.0,
            'system_uptime': 0.0
        }
        
        # Threading
        self.main_loop_thread = None
        self.heartbeat_thread = None
        self.monitoring_thread = None
        
        # Event handlers
        self.event_handlers = {}
        
        self.logger.info("System Manager initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Starting system initialization...")
            
            # Initialize configuration manager
            if not await self._initialize_config():
                return False
            
            # Initialize hardware interfaces
            if not await self._initialize_hardware():
                return False
            
            # Initialize audio processing
            if not await self._initialize_audio():
                return False
            
            # Initialize ML inference engine
            if not await self._initialize_ml():
                return False
            
            # Initialize triage engine
            if not await self._initialize_triage():
                return False
            
            # Initialize calibration system
            if not await self._initialize_calibration():
                return False
            
            # Initialize web interface
            if not await self._initialize_web():
                return False
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Start background threads
            self._start_background_threads()
            
            self.startup_time = datetime.now()
            self.running = True
            
            self.logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            return False
    
    async def _initialize_config(self) -> bool:
        """Initialize configuration management."""
        try:
            # Validate configuration
            if not self.config_manager.validate_config():
                self.logger.error("Configuration validation failed")
                return False
            
            # Setup configuration change monitoring
            self.config_manager.setup_file_watcher(self._on_config_change)
            
            self.logger.info("Configuration manager initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration initialization failed: {e}")
            return False
    
    async def _initialize_hardware(self) -> bool:
        """Initialize hardware interfaces."""
        try:
            # Initialize serial communication with MCU
            if SerialManager:
                serial_config = self.config.get('hardware', {}).get('serial', {})
                self.serial_manager = SerialManager(
                    port=serial_config.get('port', '/dev/ttyACM0'),
                    baud_rate=serial_config.get('baud_rate', 115200),
                    timeout=serial_config.get('timeout', 1.0)
                )
                
                if not await self.serial_manager.initialize():
                    self.logger.error("Serial manager initialization failed")
                    return False
                
                # Setup message handlers
                self.serial_manager.set_message_handler('sensor_data', self._handle_sensor_data)
                self.serial_manager.set_message_handler('error_report', self._handle_mcu_error)
                self.serial_manager.set_message_handler('heartbeat', self._handle_mcu_heartbeat)
            else:
                self.logger.error("SerialManager library missing - cannot communicate with Arduino")
                return False
            
            # Initialize camera
            if CameraManager:
                try:
                    camera_config = self.config.get('hardware', {}).get('camera', {})
                    self.camera_manager = CameraManager(
                        device_id=camera_config.get('device_id', 0),
                        width=camera_config.get('width', 640),
                        height=camera_config.get('height', 480),
                        fps=camera_config.get('fps', 30)
                    )
                    
                    if await self.camera_manager.initialize():
                        self.camera_enabled = True
                        self.logger.info("Camera initialized")
                    else:
                        self.logger.warning("Camera initialization failed - running in NO-CAMERA mode")
                except Exception as e:
                    self.logger.warning(f"Camera init error: {e}")
            else:
                self.logger.warning("Camera library missing - camera disabled")
            
            self.logger.info("Hardware interfaces initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Hardware initialization failed: {e}")
            return False

    async def _initialize_audio(self) -> bool:
        """Initialize audio processing system."""
        try:
            if AudioManager:
                # Initialize audio manager
                audio_config = self.config.get('audio', {})
                self.audio_manager = AudioManager(
                    sample_rate=audio_config.get('sample_rate', 8000),
                    channels=audio_config.get('channels', 1),
                    device_id=audio_config.get('device_id', None)
                )
                
                if await self.audio_manager.initialize():
                    self.audio_enabled = True
                else:
                    self.logger.warning("Audio manager failed - running in SIMULATION mode")
            else:
                self.logger.warning("Audio libraries missing - running in SIMULATION mode")
                self.audio_enabled = False
            
            if self.audio_enabled and AudioCapture:
                # Initialize audio capture
                self.audio_capture = AudioCapture(
                    sample_rate=audio_config.get('sample_rate', 8000),
                    channels=audio_config.get('channels', 1),
                    buffer_size=audio_config.get('buffer_size', 8192)
                )
                
                if not await self.audio_capture.initialize():
                    self.logger.warning("Audio capture failed - disabling audio")
                    self.audio_enabled = False
            
            self.logger.info(f"Audio system initialized (Enabled: {self.audio_enabled})")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio initialization error (non-fatal): {e}")
            return True

    async def _initialize_ml(self) -> bool:
        """Initialize machine learning inference engine."""
        try:
            if InferenceEngine:
                ml_config = self.config.get('ml', {})
                try:
                    self.inference_engine = InferenceEngine(
                        heart_model_path=ml_config.get('heart_model_path', '/opt/triage-station/models/heart/heart_model.tflite'),
                        lung_model_path=ml_config.get('lung_model_path', '/opt/triage-station/models/lung/lung_model.tflite'),
                        confidence_threshold=ml_config.get('confidence_threshold', 0.7)
                    )
                    
                    if not await self.inference_engine.initialize():
                        self.logger.error("ML inference engine initialization failed")
                        # Don't fail system, just disable ML
                        self.inference_engine = None
                        return True
                    
                    self.logger.info("ML inference engine initialized")
                except Exception as e:
                    self.logger.error(f"ML engine creation failed: {e}")
                    self.inference_engine = None
                    return True # Continue without ML
            else:
                self.logger.warning("ML libraries missing - inference disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"ML initialization failed: {e}")
            return True # Continue system anyway

    async def _initialize_triage(self) -> bool:
        """Initialize triage decision engine."""
        try:
            if TriageDecisionEngine:
                triage_config = self.config.get('triage', {})
                self.triage_engine = TriageDecisionEngine(
                    thresholds=triage_config.get('thresholds', {}),
                    fusion_weights=triage_config.get('fusion_weights', {}),
                    risk_factors=triage_config.get('risk_factors', {})
                )
                
                if not await self.triage_engine.initialize():
                    self.logger.error("Triage engine initialization failed")
                    return False
                
                self.logger.info("Triage engine initialized")
            else:
                self.logger.warning("Triage engine missing - using dummy logic")
            return True
            
        except Exception as e:
            self.logger.error(f"Triage initialization failed: {e}")
            return False

    async def _initialize_calibration(self) -> bool:
        """Initialize calibration system."""
        try:
            if CalibrationManager:
                calibration_config = self.config.get('calibration', {})
                self.calibration_manager = CalibrationManager(
                    audio_calibration_enabled=calibration_config.get('audio_enabled', True),
                    sensor_calibration_enabled=calibration_config.get('sensor_enabled', True),
                    auto_calibration_interval=calibration_config.get('auto_interval', 3600)
                )
                
                if not await self.calibration_manager.initialize():
                    self.logger.error("Calibration manager initialization failed")
                    return False
                
                self.logger.info("Calibration system initialized")
            else:
                self.logger.info("Calibration system disabled (missing libraries)")
            return True
            
        except Exception as e:
            self.logger.error(f"Calibration initialization failed: {e}")
            return False

    async def _initialize_web(self) -> bool:
        """Initialize web interface."""
        try:
            if create_web_app:
                web_config = self.config.get('web', {})
                self.web_app = create_web_app(
                    system_manager=self,
                    host=web_config.get('host', '0.0.0.0'),
                    port=web_config.get('port', 5000),
                    debug=web_config.get('debug', False)
                )
                
                self.logger.info("Web interface initialized")
            else:
                self.logger.warning("Web libraries missing - web interface disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Web initialization failed: {e}")
            return False
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _start_background_threads(self):
        """Start background monitoring threads."""
        # Main system loop
        self.main_loop_thread = threading.Thread(
            target=self._main_loop,
            name="SystemMainLoop",
            daemon=True
        )
        self.main_loop_thread.start()
        
        # Heartbeat monitoring
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="HeartbeatMonitor",
            daemon=True
        )
        self.heartbeat_thread.start()
        
        # Performance monitoring
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="PerformanceMonitor",
            daemon=True
        )
        self.monitoring_thread.start()
    
    def _main_loop(self):
        """Main system processing loop."""
        self.logger.info("Main system loop started")
        
        while self.running:
            try:
                # Process state machine
                self.state_machine.process()
                
                # Handle pending events
                self._process_events()
                
                # Update performance statistics
                self._update_performance_stats()
                
                # Sleep to prevent excessive CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.error_count += 1
                
                # If too many errors, initiate shutdown
                if self.error_count > 100:
                    self.logger.critical("Too many errors, initiating emergency shutdown")
                    asyncio.create_task(self.shutdown())
                    break
    
    def _heartbeat_loop(self):
        """Heartbeat monitoring loop."""
        self.logger.info("Heartbeat monitor started")
        
        while self.running:
            try:
                # Send heartbeat to MCU
                if self.serial_manager:
                    heartbeat_msg = {
                        'timestamp': int(time.time() * 1000),
                        'message_type': 'heartbeat',
                        'data': {
                            'system_state': self.state_machine.current_state.name,
                            'uptime': self._get_uptime(),
                            'error_count': self.error_count
                        }
                    }
                    self.serial_manager.send_message(heartbeat_msg)
                
                # Check for MCU heartbeat timeout
                if self.last_heartbeat:
                    time_since_heartbeat = time.time() - self.last_heartbeat
                    if time_since_heartbeat > 10.0:  # 10 second timeout
                        self.logger.warning("MCU heartbeat timeout detected")
                        self._handle_mcu_timeout()
                
                time.sleep(5.0)  # Send heartbeat every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
    
    def _monitoring_loop(self):
        """Performance monitoring loop."""
        self.logger.info("Performance monitor started")
        
        while self.running:
            try:
                # Monitor system resources
                self._monitor_system_resources()
                
                # Monitor component health
                self._monitor_component_health()
                
                # Log performance statistics
                self._log_performance_stats()
                
                time.sleep(60.0)  # Monitor every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
    
    async def start_examination(self, mode: str) -> Dict[str, Any]:
        """
        Start a medical examination.
        
        Args:
            mode: Examination mode ('heart', 'lung', or 'both')
            
        Returns:
            dict: Examination start result
        """
        try:
            self.logger.info(f"Starting examination in {mode} mode")
            
            # Validate current state
            if self.state_machine.current_state != SystemState.IDLE:
                return {
                    'success': False,
                    'error': f'Cannot start examination in {self.state_machine.current_state.name} state'
                }
            
            # Transition to examining state
            if not self.state_machine.transition_to(SystemState.EXAMINING):
                return {
                    'success': False,
                    'error': 'Failed to transition to examining state'
                }
            
            # Initialize examination parameters
            examination_data = {
                'mode': mode,
                'start_time': datetime.now().isoformat(),
                'duration': self.config.get('examination', {}).get('duration', 8.0),
                'sample_rate': self.config.get('audio', {}).get('sample_rate', 8000)
            }
            
            # Send examination start command to MCU
            start_command = {
                'timestamp': int(time.time() * 1000),
                'message_type': 'control_command',
                'commands': {
                    'led': {'state': 'ON', 'pattern': 'solid'},
                    'servo1': {'angle': 0, 'speed': 'normal'},  # Reset progress servo
                    'buzzer': {'state': 'ON', 'frequency': 1000, 'duration': 200},
                    'display': {'text': 'SCANNING...'} # Update display
                }
            }
            
            if self.serial_manager:
                await self.serial_manager.send_message(start_command)
            
            # Start audio capture OR Simulated Loop
            if self.audio_enabled and self.audio_capture:
                await self.audio_capture.start_capture(
                    duration=examination_data['duration'],
                    callback=self._audio_capture_callback
                )
            else:
                self.logger.info("Audio disabled: Starting SIMULATED examination loop")
                asyncio.create_task(self._run_simulated_examination(examination_data['duration']))
            
            # Store examination data
            self.state_machine.set_data('current_examination', examination_data)
            
            self.logger.info("Examination started successfully")
            return {
                'success': True,
                'examination_id': examination_data['start_time'],
                'duration': examination_data['duration']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start examination: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def stop_examination(self) -> Dict[str, Any]:
        """
        Stop the current examination.
        
        Returns:
            dict: Stop result
        """
        try:
            self.logger.info("Stopping examination")
            
            # Stop audio capture
            if self.audio_capture:
                await self.audio_capture.stop_capture()
            
            # Send stop command to MCU
            stop_command = {
                'timestamp': int(time.time() * 1000),
                'message_type': 'control_command',
                'commands': {
                    'led': {'state': 'OFF'},
                    'servo1': {'angle': 90, 'speed': 'normal'},  # Reset progress servo
                    'buzzer': {'state': 'ON', 'frequency': 500, 'duration': 300}  # Stop beep
                }
            }
            
            if self.serial_manager:
                await self.serial_manager.send_message(stop_command)
            
            # Transition back to idle state
            self.state_machine.transition_to(SystemState.IDLE)
            
            self.logger.info("Examination stopped successfully")
            return {'success': True}
            
        except Exception as e:
            self.logger.error(f"Failed to stop examination: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _run_simulated_examination(self, duration: float):
        """Run a simulated examination progress loop."""
        steps = 20
        step_duration = duration / steps
        for i in range(steps + 1):
            if self.state_machine.current_state != SystemState.EXAMINING:
                break # Abort if stopped
            
            progress = i / steps
            await self._audio_capture_callback(None, progress)
            await asyncio.sleep(step_duration)
    
    async def _audio_capture_callback(self, audio_data: Optional[bytes], progress: float):
        """
        Callback function for audio capture progress (or simulation).
        
        Args:
            audio_data: Captured audio data
            progress: Capture progress (0.0 to 1.0)
        """
        try:
            # Update progress servo
            servo_angle = int(progress * 180)
            progress_command = {
                'timestamp': int(time.time() * 1000),
                'message_type': 'control_command',
                'commands': {
                    'servo1': {'angle': servo_angle, 'speed': 'normal'}
                }
            }
            
            if self.serial_manager:
                await self.serial_manager.send_message(progress_command)
            
            # If capture is complete
            if progress >= 1.0:
                if audio_data is None:
                    # Create dummy audio data for simulation
                    dummy_size = int(8000 * 8) # 8 seconds of 8kHz
                    audio_data = bytes([0] * dummy_size)
                
                await self._process_captured_audio(audio_data)
            
        except Exception as e:
            self.logger.error(f"Error in audio capture/sim callback: {e}")
    
    async def _process_captured_audio(self, audio_data: bytes):
        """
        Process (or mock process) captured audio data.
        
        Args:
            audio_data: Raw audio data
        """
        try:
            self.logger.info("Processing captured audio (Real/Simulated)")
            
            # Transition to processing state
            self.state_machine.transition_to(SystemState.PROCESSING)
            
            # Get examination data
            examination_data = self.state_machine.get_data('current_examination')
            mode = examination_data.get('mode', 'heart')
            
            inference_time = 0.1
            
            # If simulated (all zeros), we might want random/mock results?
            # Or if valid audio, try to process. 
            # If audio_enabled is False, we definitely mock results.
            
            if not self.audio_enabled:
                 # MOCK RESULTS
                import random
                heart_result = {
                    'success': True, 'predicted_class': 'Normal', 'confidence': 0.95, 'is_abnormal': False
                } if mode in ['heart', 'both'] else None
                
                lung_result = {
                    'success': True, 'predicted_class': 'Normal', 'confidence': 0.88, 'is_abnormal': False
                } if mode in ['lung', 'both'] else None
                
            else:
                # REAL PROCESSING (Assuming we have models and data)
                start_time = time.time()
                
                if mode == 'heart' or mode == 'both':
                    heart_result = await self.inference_engine.classify_heart_sound(audio_data)
                else:
                    heart_result = None
                
                if mode == 'lung' or mode == 'both':
                    lung_result = await self.inference_engine.classify_lung_sound(audio_data)
                else:
                    lung_result = None
                
                inference_time = time.time() - start_time
            
            # Get current sensor data for fusion
            sensor_data = self.state_machine.get_data('latest_sensor_data', {})
            
            # Make triage decision
            triage_result = await self.triage_engine.make_decision(
                heart_result=heart_result,
                lung_result=lung_result,
                sensor_data=sensor_data,
                examination_data=examination_data
            )
            
            # Store results
            results = {
                'examination_data': examination_data,
                'heart_result': heart_result,
                'lung_result': lung_result,
                'sensor_data': sensor_data,
                'triage_result': triage_result,
                'inference_time': inference_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.state_machine.set_data('examination_results', results)
            
            # Display results
            await self._display_results(results)
            
            # Update performance statistics
            self.performance_stats['total_examinations'] += 1
            self.performance_stats['successful_examinations'] += 1
            self.performance_stats['average_inference_time'] = (
                (self.performance_stats['average_inference_time'] * 
                 (self.performance_stats['total_examinations'] - 1) + inference_time) /
                self.performance_stats['total_examinations']
            )
            
            self.logger.info(f"Audio processing completed in {inference_time:.3f}s")
            
        except Exception as e:
            self.logger.error(f"Error processing captured audio: {e}")
            await self._handle_processing_error(str(e))
    
    async def _display_results(self, results: Dict[str, Any]):
        """
        Display examination results on actuators and web interface.
        
        Args:
            results: Examination results
        """
        try:
            triage_result = results['triage_result']
            risk_level = triage_result['risk_level']
            
            # Determine servo position and buzzer pattern based on risk level
            if risk_level == 'LOW':
                servo_angle = 45  # Green position
                buzzer_frequency = 1000
                buzzer_duration = 200
                buzzer_pattern = 1  # Single beep
            elif risk_level == 'MEDIUM':
                servo_angle = 90  # Yellow position
                buzzer_frequency = 1500
                buzzer_duration = 300
                buzzer_pattern = 2  # Double beep
            else:  # HIGH
                servo_angle = 135  # Red position
                buzzer_frequency = 2000
                buzzer_duration = 500
                buzzer_pattern = 3  # Triple beep
            
            # Send display commands to MCU
            display_command = {
                'timestamp': int(time.time() * 1000),
                'message_type': 'control_command',
                'commands': {
                    'servo2': {'angle': servo_angle, 'speed': 'slow'},
                    'led': {'state': 'SOLID' if risk_level == 'LOW' else 'BLINK'},
                    'relay': {'state': 'ON' if risk_level == 'HIGH' else 'OFF'}
                }
            }
            
            if self.serial_manager:
                await self.serial_manager.send_message(display_command)
            
            # Play buzzer pattern
            for i in range(buzzer_pattern):
                buzzer_command = {
                    'timestamp': int(time.time() * 1000),
                    'message_type': 'control_command',
                    'commands': {
                        'buzzer': {
                            'state': 'ON',
                            'frequency': buzzer_frequency,
                            'duration': buzzer_duration
                        }
                    }
                }
                
                if self.serial_manager:
                    await self.serial_manager.send_message(buzzer_command)
                
                await asyncio.sleep(0.4)  # Pause between beeps
            
            # Transition to results state
            self.state_machine.transition_to(SystemState.SHOWING_RESULTS)
            
            # Auto-return to idle after display time
            display_duration = self.config.get('examination', {}).get('result_display_time', 10.0)
            await asyncio.sleep(display_duration)
            
            # Return to idle state
            await self._return_to_idle()
            
        except Exception as e:
            self.logger.error(f"Error displaying results: {e}")
    
    async def _return_to_idle(self):
        """Return system to idle state."""
        try:
            # Reset actuators
            reset_command = {
                'timestamp': int(time.time() * 1000),
                'message_type': 'control_command',
                'commands': {
                    'servo1': {'angle': 90, 'speed': 'normal'},
                    'servo2': {'angle': 90, 'speed': 'normal'},
                    'led': {'state': 'OFF'},
                    'relay': {'state': 'OFF'}
                }
            }
            
            if self.serial_manager:
                await self.serial_manager.send_message(reset_command)
            
            # Clear examination data
            self.state_machine.clear_data('current_examination')
            self.state_machine.clear_data('examination_results')
            
            # Transition to idle
            self.state_machine.transition_to(SystemState.IDLE)
            
            self.logger.info("System returned to idle state")
            
        except Exception as e:
            self.logger.error(f"Error returning to idle: {e}")
    
    def _handle_sensor_data(self, message: Dict[str, Any]):
        """Handle sensor data from MCU."""
        try:
            sensor_data = message.get('data', {})
            self.state_machine.set_data('latest_sensor_data', sensor_data)
            
            # Process sensor data based on current state
            current_state = self.state_machine.current_state
            
            if current_state == SystemState.IDLE:
                # Check for examination start trigger
                knob_data = sensor_data.get('knob', {})
                if knob_data.get('mode') != self.state_machine.get_data('last_knob_mode', -1):
                    self.state_machine.set_data('last_knob_mode', knob_data.get('mode'))
                    self._emit_event('knob_changed', knob_data)
            
            elif current_state == SystemState.EXAMINING:
                # Monitor for movement during examination
                movement_data = sensor_data.get('movement', {})
                if movement_data.get('detected', False):
                    self._emit_event('movement_detected', movement_data)
                
                # Check distance for proper placement
                distance_data = sensor_data.get('distance', {})
                if not distance_data.get('in_range', True):
                    self._emit_event('distance_out_of_range', distance_data)
            
        except Exception as e:
            self.logger.error(f"Error handling sensor data: {e}")
    
    def _handle_mcu_error(self, message: Dict[str, Any]):
        """Handle error reports from MCU."""
        try:
            error_data = message.get('data', {})
            error_type = error_data.get('type', 'unknown')
            error_message = error_data.get('message', 'No message')
            
            self.logger.error(f"MCU Error [{error_type}]: {error_message}")
            
            # Handle specific error types
            if error_type == 'sensor_failure':
                self._handle_sensor_failure(error_data)
            elif error_type == 'actuator_failure':
                self._handle_actuator_failure(error_data)
            elif error_type == 'communication_error':
                self._handle_communication_error(error_data)
            
            self.error_count += 1
            
        except Exception as e:
            self.logger.error(f"Error handling MCU error: {e}")
    
    def _handle_mcu_heartbeat(self, message: Dict[str, Any]):
        """Handle heartbeat from MCU."""
        self.last_heartbeat = time.time()
        
        # Extract MCU status information
        data = message.get('data', {})
        mcu_uptime = data.get('uptime', 0)
        mcu_error_count = data.get('error_count', 0)
        
        # Log MCU status periodically
        if int(time.time()) % 60 == 0:  # Every minute
            self.logger.debug(f"MCU Status - Uptime: {mcu_uptime}s, Errors: {mcu_error_count}")
    
    def _handle_mcu_timeout(self):
        """Handle MCU heartbeat timeout."""
        self.logger.warning("MCU heartbeat timeout - attempting reconnection")
        
        # Try to reconnect to MCU
        if self.serial_manager:
            asyncio.create_task(self.serial_manager.reconnect())
    
    def _handle_sensor_failure(self, error_data: Dict[str, Any]):
        """Handle sensor failure."""
        sensor_name = error_data.get('sensor', 'unknown')
        self.logger.warning(f"Sensor failure detected: {sensor_name}")
        
        # Disable affected functionality
        # Implementation depends on which sensor failed
    
    def _handle_actuator_failure(self, error_data: Dict[str, Any]):
        """Handle actuator failure."""
        actuator_name = error_data.get('actuator', 'unknown')
        self.logger.warning(f"Actuator failure detected: {actuator_name}")
        
        # Continue operation without failed actuator
    
    def _handle_communication_error(self, error_data: Dict[str, Any]):
        """Handle communication errors."""
        self.logger.warning("Communication error detected")
        
        # Attempt to recover communication
        if self.serial_manager:
            asyncio.create_task(self.serial_manager.reset_connection())
    
    async def _handle_processing_error(self, error_message: str):
        """Handle audio processing errors."""
        self.logger.error(f"Audio processing error: {error_message}")
        
        # Display error to user
        error_command = {
            'timestamp': int(time.time() * 1000),
            'message_type': 'control_command',
            'commands': {
                'led': {'state': 'BLINK', 'pattern': 'fast'},
                'buzzer': {'state': 'ON', 'frequency': 500, 'duration': 1000}
            }
        }
        
        if self.serial_manager:
            await self.serial_manager.send_message(error_command)
        
        # Return to idle after error display
        await asyncio.sleep(3.0)
        await self._return_to_idle()
    
    def _emit_event(self, event_type: str, data: Any):
        """Emit an event to registered handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def _process_events(self):
        """Process pending events."""
        # Implementation for event processing
        pass
    
    def _update_performance_stats(self):
        """Update performance statistics."""
        if self.startup_time:
            self.performance_stats['system_uptime'] = (
                datetime.now() - self.startup_time
            ).total_seconds()
    
    def _monitor_system_resources(self):
        """Monitor system resource usage."""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Log if usage is high
            if cpu_percent > 80:
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
            
            if memory_percent > 80:
                self.logger.warning(f"High memory usage: {memory_percent}%")
            
            if disk_percent > 90:
                self.logger.warning(f"High disk usage: {disk_percent}%")
            
        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            self.logger.error(f"Error monitoring system resources: {e}")
    
    def _monitor_component_health(self):
        """Monitor health of system components."""
        components = {
            'serial_manager': self.serial_manager,
            'camera_manager': self.camera_manager,
            'audio_manager': self.audio_manager,
            'inference_engine': self.inference_engine,
            'triage_engine': self.triage_engine
        }
        
        for name, component in components.items():
            if component and hasattr(component, 'is_healthy'):
                if not component.is_healthy():
                    self.logger.warning(f"Component health check failed: {name}")
    
    def _log_performance_stats(self):
        """Log performance statistics."""
        stats = self.performance_stats.copy()
        stats['current_state'] = self.state_machine.current_state.name
        stats['error_count'] = self.error_count
        
        self.logger.info(f"Performance Stats: {stats}")
    
    def _get_uptime(self) -> float:
        """Get system uptime in seconds."""
        if self.startup_time:
            return (datetime.now() - self.startup_time).total_seconds()
        return 0.0
    
    def _on_config_change(self, config_path: str):
        """Handle configuration file changes."""
        self.logger.info(f"Configuration file changed: {config_path}")
        
        # Reload configuration
        self.config = self.config_manager.get_config()
        
        # Apply configuration changes
        # Implementation depends on what changed
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'state': self.state_machine.current_state.name,
            'uptime': self._get_uptime(),
            'error_count': self.error_count,
            'performance_stats': self.performance_stats.copy(),
            'component_status': {
                'serial_manager': self.serial_manager.is_connected() if self.serial_manager else False,
                'camera_manager': self.camera_manager.is_active() if self.camera_manager else False,
                'audio_manager': self.audio_manager.is_active() if self.audio_manager else False,
                'inference_engine': self.inference_engine.is_loaded() if self.inference_engine else False
            },
            'last_heartbeat': self.last_heartbeat,
            'latest_sensor_data': self.state_machine.get_data('latest_sensor_data', {}),
            'examination_results': self.state_machine.get_data('examination_results', {})
        }
    
    async def shutdown(self):
        """Gracefully shutdown the system."""
        try:
            self.logger.info("Initiating system shutdown...")
            
            self.running = False
            
            # Stop background threads
            if self.main_loop_thread and self.main_loop_thread.is_alive():
                self.main_loop_thread.join(timeout=5.0)
            
            if self.heartbeat_thread and self.heartbeat_thread.is_alive():
                self.heartbeat_thread.join(timeout=5.0)
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            
            # Shutdown components
            if self.audio_capture:
                await self.audio_capture.shutdown()
            
            if self.audio_manager:
                await self.audio_manager.shutdown()
            
            if self.camera_manager:
                await self.camera_manager.shutdown()
            
            if self.serial_manager:
                await self.serial_manager.shutdown()
            
            if self.inference_engine:
                await self.inference_engine.shutdown()
            
            if self.triage_engine:
                await self.triage_engine.shutdown()
            
            if self.calibration_manager:
                await self.calibration_manager.shutdown()
            
            self.logger.info("System shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Main entry point
async def main():
    """Main entry point for the system."""
    system_manager = SystemManager()
    
    try:
        # Initialize system
        if not await system_manager.initialize():
            print("System initialization failed")
            sys.exit(1)
        
        print("Smart Rural Triage Station started successfully")
        print("Press Ctrl+C to shutdown")
        
        # Keep the system running
        while system_manager.running:
            await asyncio.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"System error: {e}")
    finally:
        await system_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())