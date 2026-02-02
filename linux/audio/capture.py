#!/usr/bin/env python3
"""
Smart Rural Triage Station - Audio Capture
==========================================

This module handles real-time audio capture with progress tracking,
quality monitoring, and callback-based processing.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import numpy as np
import logging
import asyncio
import threading
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import wave
from ..hardware.audio_manager import AudioManager


class AudioCapture:
    """
    Real-time audio capture with progress tracking and quality monitoring.
    
    Provides high-level audio capture functionality with progress callbacks,
    quality assessment, and automatic gain control.
    """
    
    def __init__(self,
                 sample_rate: int = 8000,
                 channels: int = 1,
                 buffer_size: int = 8192):
        """
        Initialize audio capture.
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            buffer_size: Audio buffer size
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_size = buffer_size
        
        # Audio manager
        self.audio_manager = AudioManager(
            sample_rate=sample_rate,
            channels=channels,
            chunk_size=buffer_size
        )
        
        # Capture state
        self.capturing = False
        self.capture_duration = 0.0
        self.capture_start_time = None
        self.captured_samples = 0
        self.target_samples = 0
        
        # Audio data storage
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Callbacks
        self.progress_callback = None
        self.completion_callback = None
        self.quality_callback = None
        
        # Quality monitoring
        self.quality_stats = {
            'peak_level': 0.0,
            'rms_level': 0.0,
            'snr_estimate': 0.0,
            'clipping_detected': False,
            'silence_detected': False,
            'quality_score': 0.0
        }
        
        # Automatic gain control
        self.agc_enabled = True
        self.target_level = 0.3  # Target RMS level (0-1)
        self.gain_factor = 1.0
        self.gain_adaptation_rate = 0.01
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Audio capture initialized - Sample rate: {sample_rate}Hz, Buffer: {buffer_size}")
    
    async def initialize(self) -> bool:
        """
        Initialize audio capture system.
        
        Returns:
            bool: True if successful
        """
        try:
            # Initialize audio manager
            if not await self.audio_manager.initialize():
                self.logger.error("Failed to initialize audio manager")
                return False
            
            self.logger.info("Audio capture system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio capture initialization failed: {e}")
            return False
    
    async def start_capture(self,
                           duration: float,
                           callback: Optional[Callable] = None,
                           progress_callback: Optional[Callable] = None,
                           quality_callback: Optional[Callable] = None) -> bool:
        """
        Start audio capture for specified duration.
        
        Args:
            duration: Capture duration in seconds
            callback: Completion callback (audio_data, progress)
            progress_callback: Progress callback (audio_data, progress)
            quality_callback: Quality monitoring callback (quality_stats)
            
        Returns:
            bool: True if started successfully
        """
        try:
            if self.capturing:
                self.logger.warning("Capture already in progress")
                return False
            
            # Setup capture parameters
            self.capture_duration = duration
            self.target_samples = int(self.sample_rate * duration)
            self.captured_samples = 0
            self.capture_start_time = time.time()
            
            # Setup callbacks
            self.completion_callback = callback
            self.progress_callback = progress_callback
            self.quality_callback = quality_callback
            
            # Clear audio buffer
            with self.buffer_lock:
                self.audio_buffer.clear()
            
            # Reset quality stats
            self._reset_quality_stats()
            
            # Start audio recording with callback
            if not await self.audio_manager.start_recording(callback=self._audio_data_callback):
                self.logger.error("Failed to start audio recording")
                return False
            
            self.capturing = True
            
            # Start monitoring thread
            self._start_monitoring_thread()
            
            self.logger.info(f"Audio capture started - Duration: {duration}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start audio capture: {e}")
            return False
    
    async def stop_capture(self) -> Optional[np.ndarray]:
        """
        Stop audio capture and return captured data.
        
        Returns:
            np.ndarray: Captured audio data or None if failed
        """
        try:
            if not self.capturing:
                return None
            
            self.capturing = False
            
            # Stop audio recording
            await self.audio_manager.stop_recording()
            
            # Get captured audio data
            with self.buffer_lock:
                if self.audio_buffer:
                    audio_data = np.concatenate(self.audio_buffer)
                else:
                    audio_data = np.array([], dtype=np.int16)
            
            # Call completion callback
            if self.completion_callback:
                try:
                    await self.completion_callback(audio_data, 1.0)
                except Exception as e:
                    self.logger.error(f"Error in completion callback: {e}")
            
            self.logger.info(f"Audio capture stopped - Captured {len(audio_data)} samples")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error stopping audio capture: {e}")
            return None
    
    def _audio_data_callback(self, audio_data: np.ndarray, frame_count: int, time_info: Dict):
        """
        Audio data callback for real-time processing.
        
        Args:
            audio_data: Audio data chunk
            frame_count: Number of frames
            time_info: Timing information
        """
        try:
            if not self.capturing:
                return
            
            # Apply automatic gain control
            if self.agc_enabled:
                audio_data = self._apply_agc(audio_data)
            
            # Store audio data
            with self.buffer_lock:
                self.audio_buffer.append(audio_data.copy())
            
            # Update capture progress
            self.captured_samples += len(audio_data)
            progress = min(self.captured_samples / self.target_samples, 1.0)
            
            # Update quality statistics
            self._update_quality_stats(audio_data)
            
            # Call progress callback
            if self.progress_callback:
                try:
                    asyncio.create_task(self.progress_callback(audio_data, progress))
                except Exception as e:
                    self.logger.error(f"Error in progress callback: {e}")
            
            # Call quality callback
            if self.quality_callback:
                try:
                    asyncio.create_task(self.quality_callback(self.quality_stats.copy()))
                except Exception as e:
                    self.logger.error(f"Error in quality callback: {e}")
            
            # Check if capture is complete
            if progress >= 1.0:
                asyncio.create_task(self.stop_capture())
            
        except Exception as e:
            self.logger.error(f"Error in audio data callback: {e}")
    
    def _apply_agc(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply automatic gain control to audio data.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            np.ndarray: Gain-adjusted audio data
        """
        try:
            # Calculate current RMS level
            if len(audio_data) > 0:
                current_level = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)) / 32768.0
                
                # Adapt gain factor
                if current_level > 0:
                    desired_gain = self.target_level / current_level
                    self.gain_factor += (desired_gain - self.gain_factor) * self.gain_adaptation_rate
                    
                    # Limit gain factor to reasonable range
                    self.gain_factor = np.clip(self.gain_factor, 0.1, 10.0)
                
                # Apply gain
                adjusted_data = audio_data.astype(np.float32) * self.gain_factor
                
                # Prevent clipping
                adjusted_data = np.clip(adjusted_data, -32768, 32767)
                
                return adjusted_data.astype(np.int16)
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error applying AGC: {e}")
            return audio_data
    
    def _update_quality_stats(self, audio_data: np.ndarray):
        """
        Update audio quality statistics.
        
        Args:
            audio_data: Audio data chunk
        """
        try:
            if len(audio_data) == 0:
                return
            
            # Convert to float for calculations
            float_data = audio_data.astype(np.float32) / 32768.0
            
            # Peak level
            peak_level = np.max(np.abs(float_data))
            self.quality_stats['peak_level'] = max(self.quality_stats['peak_level'], peak_level)
            
            # RMS level
            rms_level = np.sqrt(np.mean(float_data ** 2))
            self.quality_stats['rms_level'] = rms_level
            
            # Clipping detection
            if peak_level > 0.95:
                self.quality_stats['clipping_detected'] = True
            
            # Silence detection
            if rms_level < 0.01:
                self.quality_stats['silence_detected'] = True
            
            # Simple SNR estimate (based on signal dynamics)
            if len(float_data) > 1:
                signal_variance = np.var(float_data)
                if signal_variance > 0:
                    # Estimate noise floor from quiet segments
                    quiet_threshold = rms_level * 0.1
                    quiet_samples = float_data[np.abs(float_data) < quiet_threshold]
                    
                    if len(quiet_samples) > 10:
                        noise_variance = np.var(quiet_samples)
                        if noise_variance > 0:
                            snr = 10 * np.log10(signal_variance / noise_variance)
                            self.quality_stats['snr_estimate'] = snr
            
            # Overall quality score (0-1)
            quality_score = 1.0
            
            # Penalize clipping
            if self.quality_stats['clipping_detected']:
                quality_score *= 0.5
            
            # Penalize silence
            if self.quality_stats['silence_detected']:
                quality_score *= 0.3
            
            # Reward good signal level
            if 0.1 <= rms_level <= 0.8:
                quality_score *= 1.0
            else:
                quality_score *= 0.7
            
            # Reward good SNR
            if self.quality_stats['snr_estimate'] > 20:
                quality_score *= 1.0
            elif self.quality_stats['snr_estimate'] > 10:
                quality_score *= 0.8
            else:
                quality_score *= 0.6
            
            self.quality_stats['quality_score'] = quality_score
            
        except Exception as e:
            self.logger.error(f"Error updating quality stats: {e}")
    
    def _reset_quality_stats(self):
        """Reset quality statistics."""
        self.quality_stats = {
            'peak_level': 0.0,
            'rms_level': 0.0,
            'snr_estimate': 0.0,
            'clipping_detected': False,
            'silence_detected': False,
            'quality_score': 0.0
        }
    
    def _start_monitoring_thread(self):
        """Start monitoring thread for capture progress."""
        def monitoring_loop():
            while self.capturing:
                try:
                    # Check for timeout
                    if self.capture_start_time:
                        elapsed_time = time.time() - self.capture_start_time
                        if elapsed_time > self.capture_duration + 5.0:  # 5 second timeout buffer
                            self.logger.warning("Capture timeout - stopping")
                            asyncio.create_task(self.stop_capture())
                            break
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
        
        monitoring_thread = threading.Thread(
            target=monitoring_loop,
            name="AudioCaptureMonitor",
            daemon=True
        )
        monitoring_thread.start()
    
    def get_capture_progress(self) -> float:
        """
        Get current capture progress.
        
        Returns:
            float: Progress (0.0 to 1.0)
        """
        if self.target_samples > 0:
            return min(self.captured_samples / self.target_samples, 1.0)
        return 0.0
    
    def get_quality_stats(self) -> Dict[str, Any]:
        """
        Get current quality statistics.
        
        Returns:
            dict: Quality statistics
        """
        return self.quality_stats.copy()
    
    def set_agc_enabled(self, enabled: bool):
        """
        Enable or disable automatic gain control.
        
        Args:
            enabled: True to enable AGC
        """
        self.agc_enabled = enabled
        self.logger.info(f"AGC {'enabled' if enabled else 'disabled'}")
    
    def set_target_level(self, level: float):
        """
        Set target audio level for AGC.
        
        Args:
            level: Target RMS level (0.0 to 1.0)
        """
        self.target_level = np.clip(level, 0.01, 0.9)
        self.logger.info(f"AGC target level set to {self.target_level}")
    
    def save_captured_audio(self, filename: str, audio_data: Optional[np.ndarray] = None) -> bool:
        """
        Save captured audio to file.
        
        Args:
            filename: Output filename
            audio_data: Audio data to save (uses buffer if None)
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Get audio data
            if audio_data is None:
                with self.buffer_lock:
                    if self.audio_buffer:
                        audio_data = np.concatenate(self.audio_buffer)
                    else:
                        self.logger.error("No audio data to save")
                        return False
            
            # Save using audio manager
            return self.audio_manager.save_audio(audio_data, filename)
            
        except Exception as e:
            self.logger.error(f"Error saving captured audio: {e}")
            return False
    
    def is_capturing(self) -> bool:
        """
        Check if capture is in progress.
        
        Returns:
            bool: True if capturing
        """
        return self.capturing
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get capture statistics.
        
        Returns:
            dict: Capture statistics
        """
        stats = {
            'capturing': self.capturing,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'buffer_size': self.buffer_size,
            'capture_duration': self.capture_duration,
            'captured_samples': self.captured_samples,
            'target_samples': self.target_samples,
            'progress': self.get_capture_progress(),
            'agc_enabled': self.agc_enabled,
            'gain_factor': self.gain_factor,
            'quality_stats': self.quality_stats.copy()
        }
        
        # Add audio manager stats
        if self.audio_manager:
            stats['audio_manager'] = self.audio_manager.get_statistics()
        
        return stats
    
    async def shutdown(self):
        """Shutdown audio capture system."""
        try:
            self.logger.info("Shutting down audio capture system")
            
            # Stop capture if active
            if self.capturing:
                await self.stop_capture()
            
            # Shutdown audio manager
            if self.audio_manager:
                await self.audio_manager.shutdown()
            
            self.logger.info("Audio capture system shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during audio capture shutdown: {e}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_audio_capture():
        """Test audio capture functionality."""
        # Create audio capture
        audio_capture = AudioCapture(sample_rate=8000, channels=1)
        
        # Progress callback
        async def progress_callback(audio_data, progress):
            print(f"Capture progress: {progress:.1%} - Level: {np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)):.0f}")
        
        # Quality callback
        async def quality_callback(quality_stats):
            print(f"Quality score: {quality_stats['quality_score']:.2f}, RMS: {quality_stats['rms_level']:.3f}")
        
        # Completion callback
        async def completion_callback(audio_data, progress):
            print(f"Capture completed - {len(audio_data)} samples captured")
        
        # Initialize
        if await audio_capture.initialize():
            print("Audio capture initialized successfully")
            
            # Start capture
            print("Starting 8-second audio capture...")
            if await audio_capture.start_capture(
                duration=8.0,
                callback=completion_callback,
                progress_callback=progress_callback,
                quality_callback=quality_callback
            ):
                print("Capture started successfully")
                
                # Wait for completion
                while audio_capture.is_capturing():
                    await asyncio.sleep(0.5)
                
                # Save captured audio
                if audio_capture.save_captured_audio("test_capture.wav"):
                    print("Audio saved successfully")
                
                # Print statistics
                stats = audio_capture.get_statistics()
                print(f"Capture statistics: {stats}")
                
            else:
                print("Failed to start capture")
        else:
            print("Failed to initialize audio capture")
        
        # Shutdown
        await audio_capture.shutdown()
    
    # Run test
    asyncio.run(test_audio_capture())