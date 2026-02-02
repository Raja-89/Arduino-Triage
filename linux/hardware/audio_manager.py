#!/usr/bin/env python3
"""
Smart Rural Triage Station - Audio Manager
==========================================

This module handles audio device management, including microphone
initialization, audio stream management, and device configuration.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import pyaudio
import numpy as np
import logging
import threading
import time
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import wave


class AudioDevice:
    """Represents an audio device."""
    
    def __init__(self, device_info: Dict[str, Any]):
        """
        Initialize audio device.
        
        Args:
            device_info: PyAudio device info dictionary
        """
        self.index = device_info['index']
        self.name = device_info['name']
        self.max_input_channels = device_info['maxInputChannels']
        self.max_output_channels = device_info['maxOutputChannels']
        self.default_sample_rate = device_info['defaultSampleRate']
        self.host_api = device_info['hostApi']
        
    def __str__(self):
        return f"AudioDevice(index={self.index}, name='{self.name}', channels={self.max_input_channels})"
    
    def is_input_device(self) -> bool:
        """Check if device supports input."""
        return self.max_input_channels > 0
    
    def is_output_device(self) -> bool:
        """Check if device supports output."""
        return self.max_output_channels > 0


class AudioManager:
    """
    Audio device manager for microphone and speaker operations.
    
    Handles audio device discovery, initialization, stream management,
    and audio processing for the triage station.
    """
    
    def __init__(self,
                 sample_rate: int = 8000,
                 channels: int = 1,
                 device_id: Optional[int] = None,
                 chunk_size: int = 1024):
        """
        Initialize audio manager.
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            device_id: Specific device ID (None for default)
            chunk_size: Audio buffer chunk size
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_id = device_id
        self.chunk_size = chunk_size
        
        # PyAudio instance
        self.pyaudio = None
        self.stream = None
        
        # Device management
        self.available_devices = []
        self.selected_device = None
        self.active = False
        
        # Audio processing
        self.recording = False
        self.playback = False
        self.audio_callback = None
        
        # Statistics
        self.stats = {
            'samples_recorded': 0,
            'samples_played': 0,
            'buffer_overruns': 0,
            'buffer_underruns': 0,
            'last_activity_time': None,
            'average_level': 0.0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Audio manager initialized - Sample rate: {sample_rate}Hz, Channels: {channels}")
    
    async def initialize(self) -> bool:
        """
        Initialize audio system.
        
        Returns:
            bool: True if successful
        """
        try:
            # Initialize PyAudio
            self.pyaudio = pyaudio.PyAudio()
            
            # Discover available devices
            self._discover_devices()
            
            # Select audio device
            if not self._select_device():
                self.logger.error("No suitable audio device found")
                return False
            
            # Test device compatibility
            if not self._test_device_compatibility():
                self.logger.error("Selected device is not compatible")
                return False
            
            self.active = True
            
            self.logger.info(f"Audio system initialized - Using device: {self.selected_device}")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio initialization failed: {e}")
            return False
    
    def _discover_devices(self):
        """Discover available audio devices."""
        try:
            self.available_devices = []
            
            device_count = self.pyaudio.get_device_count()
            
            for i in range(device_count):
                try:
                    device_info = self.pyaudio.get_device_info_by_index(i)
                    device = AudioDevice(device_info)
                    
                    # Only include input devices
                    if device.is_input_device():
                        self.available_devices.append(device)
                        self.logger.debug(f"Found audio device: {device}")
                        
                except Exception as e:
                    self.logger.warning(f"Error getting device info for index {i}: {e}")
            
            self.logger.info(f"Discovered {len(self.available_devices)} audio input devices")
            
        except Exception as e:
            self.logger.error(f"Error discovering audio devices: {e}")
    
    def _select_device(self) -> bool:
        """
        Select appropriate audio device.
        
        Returns:
            bool: True if device selected successfully
        """
        try:
            if not self.available_devices:
                return False
            
            # If specific device ID provided, use it
            if self.device_id is not None:
                for device in self.available_devices:
                    if device.index == self.device_id:
                        self.selected_device = device
                        self.logger.info(f"Using specified device: {device}")
                        return True
                
                self.logger.warning(f"Specified device ID {self.device_id} not found")
            
            # Try to find USB microphone or high-quality device
            preferred_keywords = ['usb', 'microphone', 'mic', 'audio', 'headset']
            
            for device in self.available_devices:
                device_name_lower = device.name.lower()
                
                if any(keyword in device_name_lower for keyword in preferred_keywords):
                    # Check if device supports our sample rate
                    if self._is_sample_rate_supported(device, self.sample_rate):
                        self.selected_device = device
                        self.logger.info(f"Selected preferred device: {device}")
                        return True
            
            # Fall back to default input device
            try:
                default_device_info = self.pyaudio.get_default_input_device_info()
                default_device = AudioDevice(default_device_info)
                
                if self._is_sample_rate_supported(default_device, self.sample_rate):
                    self.selected_device = default_device
                    self.logger.info(f"Using default input device: {default_device}")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Error getting default input device: {e}")
            
            # Use first available device as last resort
            if self.available_devices:
                self.selected_device = self.available_devices[0]
                self.logger.info(f"Using first available device: {self.selected_device}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error selecting audio device: {e}")
            return False
    
    def _is_sample_rate_supported(self, device: AudioDevice, sample_rate: int) -> bool:
        """
        Check if device supports the specified sample rate.
        
        Args:
            device: Audio device to test
            sample_rate: Sample rate to test
            
        Returns:
            bool: True if supported
        """
        try:
            # Test if the device supports the sample rate
            self.pyaudio.is_format_supported(
                rate=sample_rate,
                input_device=device.index,
                input_channels=self.channels,
                input_format=pyaudio.paInt16
            )
            return True
            
        except ValueError:
            return False
        except Exception as e:
            self.logger.warning(f"Error testing sample rate for device {device.index}: {e}")
            return False
    
    def _test_device_compatibility(self) -> bool:
        """
        Test device compatibility with our requirements.
        
        Returns:
            bool: True if compatible
        """
        try:
            if not self.selected_device:
                return False
            
            # Test opening a stream
            test_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.selected_device.index,
                frames_per_buffer=self.chunk_size
            )
            
            # Test reading a small amount of data
            test_data = test_stream.read(self.chunk_size, exception_on_overflow=False)
            
            # Close test stream
            test_stream.stop_stream()
            test_stream.close()
            
            # Verify we got data
            if len(test_data) > 0:
                self.logger.info("Device compatibility test passed")
                return True
            else:
                self.logger.error("Device compatibility test failed - no data received")
                return False
                
        except Exception as e:
            self.logger.error(f"Device compatibility test failed: {e}")
            return False
    
    async def start_recording(self, callback: Optional[Callable] = None) -> bool:
        """
        Start audio recording.
        
        Args:
            callback: Optional callback for audio data processing
            
        Returns:
            bool: True if started successfully
        """
        try:
            if not self.active:
                self.logger.error("Audio manager not initialized")
                return False
            
            if self.recording:
                self.logger.warning("Recording already active")
                return True
            
            self.audio_callback = callback
            
            # Open audio stream
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.selected_device.index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_stream_callback if callback else None
            )
            
            self.stream.start_stream()
            self.recording = True
            
            self.logger.info("Audio recording started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start audio recording: {e}")
            return False
    
    async def stop_recording(self):
        """Stop audio recording."""
        try:
            if not self.recording:
                return
            
            self.recording = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            self.audio_callback = None
            
            self.logger.info("Audio recording stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping audio recording: {e}")
    
    def _audio_stream_callback(self, in_data, frame_count, time_info, status):
        """
        Audio stream callback for real-time processing.
        
        Args:
            in_data: Input audio data
            frame_count: Number of frames
            time_info: Timing information
            status: Stream status
            
        Returns:
            tuple: (None, pyaudio.paContinue)
        """
        try:
            # Update statistics
            self.stats['samples_recorded'] += frame_count
            self.stats['last_activity_time'] = datetime.now()
            
            # Check for buffer overruns
            if status & pyaudio.paInputOverflow:
                self.stats['buffer_overruns'] += 1
                self.logger.warning("Audio input buffer overrun")
            
            # Convert to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Calculate audio level
            if len(audio_data) > 0:
                level = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                self.stats['average_level'] = level
            
            # Call user callback if provided
            if self.audio_callback:
                try:
                    self.audio_callback(audio_data, frame_count, time_info)
                except Exception as e:
                    self.logger.error(f"Error in audio callback: {e}")
            
            return (None, pyaudio.paContinue)
            
        except Exception as e:
            self.logger.error(f"Error in audio stream callback: {e}")
            return (None, pyaudio.paAbort)
    
    def record_audio(self, duration: float) -> Optional[np.ndarray]:
        """
        Record audio for specified duration.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            np.ndarray: Recorded audio data or None if failed
        """
        try:
            if not self.active:
                self.logger.error("Audio manager not initialized")
                return None
            
            # Calculate number of frames to record
            frames_to_record = int(self.sample_rate * duration)
            
            # Open stream for recording
            stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.selected_device.index,
                frames_per_buffer=self.chunk_size
            )
            
            self.logger.info(f"Recording audio for {duration} seconds...")
            
            # Record audio data
            audio_frames = []
            frames_recorded = 0
            
            while frames_recorded < frames_to_record:
                frames_to_read = min(self.chunk_size, frames_to_record - frames_recorded)
                
                try:
                    data = stream.read(frames_to_read, exception_on_overflow=False)
                    audio_frames.append(data)
                    frames_recorded += frames_to_read
                    
                except Exception as e:
                    self.logger.warning(f"Audio read error: {e}")
                    break
            
            # Close stream
            stream.stop_stream()
            stream.close()
            
            # Convert to numpy array
            if audio_frames:
                audio_data = b''.join(audio_frames)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                self.logger.info(f"Recorded {len(audio_array)} samples")
                return audio_array
            else:
                self.logger.error("No audio data recorded")
                return None
                
        except Exception as e:
            self.logger.error(f"Error recording audio: {e}")
            return None
    
    def save_audio(self, audio_data: np.ndarray, filename: str) -> bool:
        """
        Save audio data to WAV file.
        
        Args:
            audio_data: Audio data to save
            filename: Output filename
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Open WAV file for writing
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
                wav_file.setframerate(self.sample_rate)
                
                # Convert to bytes and write
                audio_bytes = audio_data.astype(np.int16).tobytes()
                wav_file.writeframes(audio_bytes)
            
            self.logger.info(f"Audio saved to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving audio to {filename}: {e}")
            return False
    
    def get_audio_level(self) -> float:
        """
        Get current audio input level.
        
        Returns:
            float: Audio level (RMS)
        """
        return self.stats.get('average_level', 0.0)
    
    def get_available_devices(self) -> List[AudioDevice]:
        """
        Get list of available audio devices.
        
        Returns:
            list: Available audio devices
        """
        return self.available_devices.copy()
    
    def set_device(self, device_id: int) -> bool:
        """
        Set audio device by ID.
        
        Args:
            device_id: Device ID to use
            
        Returns:
            bool: True if set successfully
        """
        try:
            # Find device by ID
            for device in self.available_devices:
                if device.index == device_id:
                    # Stop current recording if active
                    if self.recording:
                        asyncio.create_task(self.stop_recording())
                    
                    self.selected_device = device
                    self.device_id = device_id
                    
                    self.logger.info(f"Audio device changed to: {device}")
                    return True
            
            self.logger.error(f"Device ID {device_id} not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting audio device: {e}")
            return False
    
    def is_active(self) -> bool:
        """
        Check if audio manager is active.
        
        Returns:
            bool: True if active
        """
        return self.active and self.pyaudio is not None
    
    def is_healthy(self) -> bool:
        """
        Check audio system health.
        
        Returns:
            bool: True if healthy
        """
        if not self.is_active():
            return False
        
        # Check if we have a selected device
        if not self.selected_device:
            return False
        
        # Check for excessive buffer overruns
        if self.stats['buffer_overruns'] > 10:
            return False
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audio system statistics.
        
        Returns:
            dict: Audio statistics
        """
        stats = self.stats.copy()
        stats.update({
            'active': self.active,
            'recording': self.recording,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'chunk_size': self.chunk_size,
            'selected_device': str(self.selected_device) if self.selected_device else None,
            'available_devices_count': len(self.available_devices),
            'healthy': self.is_healthy()
        })
        
        return stats
    
    async def shutdown(self):
        """Shutdown audio system."""
        try:
            self.logger.info("Shutting down audio system")
            
            # Stop recording
            await self.stop_recording()
            
            # Terminate PyAudio
            if self.pyaudio:
                self.pyaudio.terminate()
                self.pyaudio = None
            
            self.active = False
            
            self.logger.info("Audio system shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during audio shutdown: {e}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_audio_manager():
        """Test audio manager functionality."""
        # Create audio manager
        audio_manager = AudioManager(sample_rate=8000, channels=1)
        
        # Audio callback for testing
        def audio_callback(audio_data, frame_count, time_info):
            level = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            print(f"Audio level: {level:.2f}")
        
        # Initialize audio
        if await audio_manager.initialize():
            print("Audio manager initialized successfully")
            
            # List available devices
            devices = audio_manager.get_available_devices()
            print(f"Available devices: {len(devices)}")
            for device in devices:
                print(f"  {device}")
            
            # Test recording
            print("Testing 5-second recording...")
            audio_data = audio_manager.record_audio(5.0)
            
            if audio_data is not None:
                print(f"Recorded {len(audio_data)} samples")
                
                # Save audio
                if audio_manager.save_audio(audio_data, "test_recording.wav"):
                    print("Audio saved successfully")
                
                # Print statistics
                stats = audio_manager.get_statistics()
                print(f"Audio statistics: {stats}")
            else:
                print("Recording failed")
        else:
            print("Failed to initialize audio manager")
        
        # Shutdown
        await audio_manager.shutdown()
    
    # Run test
    asyncio.run(test_audio_manager())