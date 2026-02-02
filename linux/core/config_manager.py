#!/usr/bin/env python3
"""
Smart Rural Triage Station - Configuration Manager
==================================================

This module handles system configuration loading, validation, and management.
Supports YAML configuration files with hot-reloading capabilities.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import os
import yaml
import logging
import threading
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file changes."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path == self.config_manager.config_path:
            self.logger.info(f"Configuration file modified: {event.src_path}")
            # Debounce rapid file changes
            time.sleep(0.1)
            self.config_manager._reload_config()


class ConfigManager:
    """
    Configuration manager for the triage station.
    
    Handles loading, validation, and hot-reloading of YAML configuration files.
    Provides thread-safe access to configuration data.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to the main configuration file
        """
        self.config_path = config_path
        self.config = {}
        self.lock = threading.RLock()
        self.observers = []
        self.change_callbacks = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load initial configuration
        self._load_config()
        
        self.logger.info(f"Configuration manager initialized with {config_path}")
    
    def _load_config(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            bool: True if successful
        """
        try:
            if not os.path.exists(self.config_path):
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                self._create_default_config()
                return False
            
            with open(self.config_path, 'r') as file:
                config_data = yaml.safe_load(file)
                
                if config_data is None:
                    config_data = {}
                
                with self.lock:
                    self.config = config_data
                
                self.logger.info("Configuration loaded successfully")
                return True
                
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False
    
    def _create_default_config(self):
        """Create default configuration file."""
        default_config = {
            'system': {
                'name': 'Smart Rural Triage Station',
                'version': '1.0.0',
                'debug': False
            },
            'hardware': {
                'serial': {
                    'port': '/dev/ttyACM0',
                    'baud_rate': 115200,
                    'timeout': 1.0
                },
                'camera': {
                    'device_id': 0,
                    'width': 640,
                    'height': 480,
                    'fps': 30
                }
            },
            'audio': {
                'sample_rate': 8000,
                'channels': 1,
                'buffer_size': 8192,
                'device_id': None,
                'heart_filter': {
                    'low_freq': 20,
                    'high_freq': 400
                },
                'lung_filter': {
                    'low_freq': 100,
                    'high_freq': 2000
                }
            },
            'ml': {
                'heart_model_path': '/opt/triage-station/models/heart/heart_model.tflite',
                'lung_model_path': '/opt/triage-station/models/lung/lung_model.tflite',
                'yamnet_model_path': '/opt/triage-station/models/yamnet/yamnet_model.tflite',
                'confidence_threshold': 0.7,
                'inference_timeout': 5.0
            },
            'triage': {
                'thresholds': {
                    'ml_confidence': 0.7,
                    'temperature_fever': 38.0,
                    'heart_rate_high': 100,
                    'heart_rate_low': 50
                },
                'fusion_weights': {
                    'ml_prediction': 0.5,
                    'audio_analysis': 0.3,
                    'vital_signs': 0.2
                }
            },
            'calibration': {
                'audio_enabled': True,
                'sensor_enabled': True,
                'auto_interval': 3600
            },
            'web': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            },
            'examination': {
                'duration': 8.0,
                'result_display_time': 10.0
            },
            'logging': {
                'level': 'INFO',
                'file': '/opt/triage-station/logs/system.log',
                'max_size': '10MB',
                'backup_count': 5
            }
        }
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as file:
                yaml.dump(default_config, file, default_flow_style=False, indent=2)
            
            with self.lock:
                self.config = default_config
            
            self.logger.info(f"Created default configuration file: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating default configuration: {e}")
    
    def _reload_config(self):
        """Reload configuration from file."""
        if self._load_config():
            # Notify callbacks of configuration change
            for callback in self.change_callbacks:
                try:
                    callback(self.config_path)
                except Exception as e:
                    self.logger.error(f"Error in config change callback: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get complete configuration.
        
        Returns:
            dict: Complete configuration
        """
        with self.lock:
            return self.config.copy()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by key path.
        
        Args:
            key_path: Dot-separated key path (e.g., 'audio.sample_rate')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        with self.lock:
            keys = key_path.split('.')
            value = self.config
            
            try:
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set configuration value by key path.
        
        Args:
            key_path: Dot-separated key path
            value: Value to set
            
        Returns:
            bool: True if successful
        """
        with self.lock:
            keys = key_path.split('.')
            config = self.config
            
            try:
                # Navigate to parent of target key
                for key in keys[:-1]:
                    if key not in config:
                        config[key] = {}
                    config = config[key]
                
                # Set the value
                config[keys[-1]] = value
                
                self.logger.info(f"Configuration updated: {key_path} = {value}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error setting configuration {key_path}: {e}")
                return False
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                config_copy = self.config.copy()
            
            with open(self.config_path, 'w') as file:
                yaml.dump(config_copy, file, default_flow_style=False, indent=2)
            
            self.logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def validate_config(self) -> bool:
        """
        Validate configuration structure and values.
        
        Returns:
            bool: True if valid
        """
        try:
            config = self.get_config()
            
            # Check required sections
            required_sections = ['hardware', 'audio', 'ml', 'triage', 'web']
            for section in required_sections:
                if section not in config:
                    self.logger.error(f"Missing required configuration section: {section}")
                    return False
            
            # Validate hardware configuration
            hardware = config.get('hardware', {})
            serial_config = hardware.get('serial', {})
            if not serial_config.get('port') or not serial_config.get('baud_rate'):
                self.logger.error("Invalid serial configuration")
                return False
            
            # Validate audio configuration
            audio = config.get('audio', {})
            if not audio.get('sample_rate') or audio.get('sample_rate') <= 0:
                self.logger.error("Invalid audio sample rate")
                return False
            
            # Validate ML configuration
            ml = config.get('ml', {})
            if not ml.get('heart_model_path') or not ml.get('lung_model_path'):
                self.logger.error("Missing ML model paths")
                return False
            
            # Validate web configuration
            web = config.get('web', {})
            if not web.get('port') or web.get('port') <= 0:
                self.logger.error("Invalid web port")
                return False
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
            return False
    
    def setup_file_watcher(self, callback: Optional[Callable] = None):
        """
        Setup file system watcher for configuration changes.
        
        Args:
            callback: Optional callback function for changes
        """
        try:
            if callback:
                self.change_callbacks.append(callback)
            
            # Setup file watcher
            event_handler = ConfigFileHandler(self)
            observer = Observer()
            observer.schedule(
                event_handler,
                path=os.path.dirname(self.config_path),
                recursive=False
            )
            observer.start()
            self.observers.append(observer)
            
            self.logger.info("Configuration file watcher started")
            
        except Exception as e:
            self.logger.error(f"Error setting up file watcher: {e}")
    
    def get_model_paths(self) -> Dict[str, str]:
        """
        Get ML model file paths.
        
        Returns:
            dict: Model paths
        """
        return {
            'heart': self.get('ml.heart_model_path', '/opt/triage-station/models/heart/heart_model.tflite'),
            'lung': self.get('ml.lung_model_path', '/opt/triage-station/models/lung/lung_model.tflite'),
            'yamnet': self.get('ml.yamnet_model_path', '/opt/triage-station/models/yamnet/yamnet_model.tflite')
        }
    
    def get_audio_config(self) -> Dict[str, Any]:
        """
        Get audio processing configuration.
        
        Returns:
            dict: Audio configuration
        """
        return self.get('audio', {})
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """
        Get hardware configuration.
        
        Returns:
            dict: Hardware configuration
        """
        return self.get('hardware', {})
    
    def get_triage_config(self) -> Dict[str, Any]:
        """
        Get triage configuration.
        
        Returns:
            dict: Triage configuration
        """
        return self.get('triage', {})
    
    def shutdown(self):
        """Shutdown configuration manager."""
        try:
            # Stop file watchers
            for observer in self.observers:
                observer.stop()
                observer.join(timeout=5.0)
            
            self.observers.clear()
            self.change_callbacks.clear()
            
            self.logger.info("Configuration manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during configuration manager shutdown: {e}")


# Example usage
if __name__ == "__main__":
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration manager
    config_manager = ConfigManager('/tmp/test_config.yaml')
    
    # Test getting values
    print(f"Sample rate: {config_manager.get('audio.sample_rate')}")
    print(f"Web port: {config_manager.get('web.port')}")
    
    # Test setting values
    config_manager.set('audio.sample_rate', 16000)
    print(f"Updated sample rate: {config_manager.get('audio.sample_rate')}")
    
    # Test validation
    is_valid = config_manager.validate_config()
    print(f"Configuration valid: {is_valid}")
    
    # Test model paths
    model_paths = config_manager.get_model_paths()
    print(f"Model paths: {model_paths}")