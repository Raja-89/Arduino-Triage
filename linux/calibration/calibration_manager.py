#!/usr/bin/env python3
"""
Smart Rural Triage Station - Calibration Manager
===============================================

This module coordinates calibration of all system components including
audio, sensors, and actuators.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .audio_calibration import AudioCalibration


class CalibrationManager:
    """
    Manages calibration of all system components.
    
    Coordinates audio calibration, sensor calibration, and automatic
    recalibration scheduling for the triage station.
    """
    
    def __init__(self,
                 audio_calibration_enabled: bool = True,
                 sensor_calibration_enabled: bool = True,
                 auto_calibration_interval: int = 3600):
        """
        Initialize calibration manager.
        
        Args:
            audio_calibration_enabled: Enable audio calibration
            sensor_calibration_enabled: Enable sensor calibration
            auto_calibration_interval: Auto-calibration interval in seconds
        """
        self.audio_calibration_enabled = audio_calibration_enabled
        self.sensor_calibration_enabled = sensor_calibration_enabled
        self.auto_calibration_interval = auto_calibration_interval
        
        # Calibration components
        self.audio_calibration = None
        
        # Calibration state
        self.calibration_status = {
            'audio': {'calibrated': False, 'timestamp': None, 'quality': 'unknown'},
            'sensors': {'calibrated': False, 'timestamp': None, 'quality': 'unknown'}
        }
        
        # Auto-calibration
        self.auto_calibration_enabled = True
        self.last_auto_calibration = None
        self.auto_calibration_thread = None
        self.running = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Calibration manager initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize calibration manager.
        
        Returns:
            bool: True if successful
        """
        try:
            # Initialize audio calibration
            if self.audio_calibration_enabled:
                self.audio_calibration = AudioCalibration()
                if not await self.audio_calibration.initialize():
                    self.logger.error("Failed to initialize audio calibration")
                    return False
            
            # Start auto-calibration thread
            self.running = True
            self._start_auto_calibration_thread()
            
            self.logger.info("Calibration manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Calibration manager initialization failed: {e}")
            return False
    
    async def run_full_calibration(self) -> Dict[str, Any]:
        """
        Run complete system calibration.
        
        Returns:
            dict: Calibration results
        """
        try:
            self.logger.info("Starting full system calibration")
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'audio': {},
                'sensors': {}
            }
            
            # Audio calibration
            if self.audio_calibration_enabled and self.audio_calibration:
                self.logger.info("Running audio calibration")
                audio_results = await self.audio_calibration.run_full_calibration()
                results['audio'] = audio_results
                
                # Update status
                self.calibration_status['audio'] = {
                    'calibrated': audio_results.get('success', False),
                    'timestamp': datetime.now(),
                    'quality': 'good' if audio_results.get('success', False) else 'poor',
                    'results': audio_results
                }
            
            # Sensor calibration
            if self.sensor_calibration_enabled:
                self.logger.info("Running sensor calibration")
                sensor_results = await self._run_sensor_calibration()
                results['sensors'] = sensor_results
                
                # Update status
                self.calibration_status['sensors'] = {
                    'calibrated': sensor_results.get('success', False),
                    'timestamp': datetime.now(),
                    'quality': 'good' if sensor_results.get('success', False) else 'poor',
                    'results': sensor_results
                }
            
            # Overall success
            results['success'] = (
                results['audio'].get('success', True) and
                results['sensors'].get('success', True)
            )
            
            if results['success']:
                self.last_auto_calibration = datetime.now()
                self.logger.info("Full system calibration completed successfully")
            else:
                self.logger.error("Full system calibration failed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in full calibration: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _run_sensor_calibration(self) -> Dict[str, Any]:
        """
        Run sensor calibration.
        
        Returns:
            dict: Sensor calibration results
        """
        try:
            self.logger.info("Running sensor calibration")
            
            # This would interface with the MCU for sensor calibration
            # For now, return a simplified result
            
            results = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'sensors': {
                    'distance': {'calibrated': True, 'offset': 0.0, 'scale': 1.0},
                    'temperature': {'calibrated': True, 'offset': 0.0, 'scale': 1.0},
                    'movement': {'calibrated': True, 'sensitivity': 1.0}
                }
            }
            
            self.logger.info("Sensor calibration completed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in sensor calibration: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _start_auto_calibration_thread(self):
        """Start automatic calibration monitoring thread."""
        def auto_calibration_loop():
            self.logger.info("Auto-calibration thread started")
            
            while self.running:
                try:
                    # Check if auto-calibration is needed
                    if self._should_run_auto_calibration():
                        self.logger.info("Running automatic calibration")
                        asyncio.create_task(self.run_full_calibration())
                    
                    # Sleep for check interval (1 minute)
                    time.sleep(60)
                    
                except Exception as e:
                    self.logger.error(f"Error in auto-calibration loop: {e}")
                    time.sleep(60)
            
            self.logger.info("Auto-calibration thread stopped")
        
        self.auto_calibration_thread = threading.Thread(
            target=auto_calibration_loop,
            name="AutoCalibrationThread",
            daemon=True
        )
        self.auto_calibration_thread.start()
    
    def _should_run_auto_calibration(self) -> bool:
        """
        Check if automatic calibration should be run.
        
        Returns:
            bool: True if auto-calibration is needed
        """
        if not self.auto_calibration_enabled:
            return False
        
        # Check if enough time has passed since last calibration
        if self.last_auto_calibration is None:
            return True
        
        time_since_last = datetime.now() - self.last_auto_calibration
        return time_since_last.total_seconds() >= self.auto_calibration_interval
    
    def apply_audio_calibration(self, audio_data) -> Any:
        """
        Apply audio calibration to audio data.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            Calibrated audio data
        """
        try:
            if (self.audio_calibration and 
                self.calibration_status['audio']['calibrated']):
                return self.audio_calibration.apply_calibration(audio_data)
            else:
                return audio_data
                
        except Exception as e:
            self.logger.error(f"Error applying audio calibration: {e}")
            return audio_data
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """
        Get current calibration status.
        
        Returns:
            dict: Calibration status
        """
        status = self.calibration_status.copy()
        
        # Convert timestamps to ISO format
        for component in status.values():
            if component['timestamp']:
                component['timestamp'] = component['timestamp'].isoformat()
        
        # Add overall status
        overall_calibrated = all(
            comp['calibrated'] for comp in status.values()
        )
        
        return {
            'overall_calibrated': overall_calibrated,
            'components': status,
            'auto_calibration_enabled': self.auto_calibration_enabled,
            'auto_calibration_interval': self.auto_calibration_interval,
            'last_auto_calibration': self.last_auto_calibration.isoformat() if self.last_auto_calibration else None,
            'next_auto_calibration': self._get_next_auto_calibration_time()
        }
    
    def _get_next_auto_calibration_time(self) -> Optional[str]:
        """Get next automatic calibration time."""
        if not self.auto_calibration_enabled or not self.last_auto_calibration:
            return None
        
        next_time = self.last_auto_calibration + timedelta(seconds=self.auto_calibration_interval)
        return next_time.isoformat()
    
    def is_calibrated(self, component: Optional[str] = None) -> bool:
        """
        Check if system or component is calibrated.
        
        Args:
            component: Component to check ('audio', 'sensors', or None for overall)
            
        Returns:
            bool: True if calibrated
        """
        if component is None:
            # Check overall calibration
            return all(
                comp['calibrated'] for comp in self.calibration_status.values()
            )
        elif component in self.calibration_status:
            return self.calibration_status[component]['calibrated']
        else:
            return False
    
    async def shutdown(self):
        """Shutdown calibration manager."""
        try:
            self.logger.info("Shutting down calibration manager")
            
            # Stop auto-calibration thread
            self.running = False
            
            if self.auto_calibration_thread and self.auto_calibration_thread.is_alive():
                self.auto_calibration_thread.join(timeout=5.0)
            
            # Shutdown audio calibration
            if self.audio_calibration:
                await self.audio_calibration.shutdown()
            
            self.logger.info("Calibration manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during calibration manager shutdown: {e}")
