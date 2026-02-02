#!/usr/bin/env python3
"""
Smart Rural Triage Station - Audio Calibration
==============================================

This module handles audio system calibration including microphone
sensitivity, noise floor measurement, and frequency response calibration.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import numpy as np
import scipy.signal
import logging
import asyncio
import time
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from dataclasses import dataclass
from ..hardware.audio_manager import AudioManager
from ..audio.preprocessing import AudioPreprocessor
from ..audio.features import AudioFeatureExtractor


@dataclass
class CalibrationConfig:
    """Configuration for audio calibration."""
    
    # Calibration tones
    calibration_frequencies: List[float] = None  # Hz
    tone_duration: float = 2.0                   # seconds
    tone_amplitude: float = 0.5                  # 0-1
    
    # Noise floor measurement
    noise_measurement_duration: float = 5.0      # seconds
    noise_samples: int = 10                      # number of measurements
    
    # Sensitivity calibration
    reference_level_db: float = -20.0           # dBFS reference level
    sensitivity_tolerance: float = 3.0          # dB tolerance
    
    # Frequency response
    freq_response_points: int = 20               # measurement points
    freq_response_tolerance: float = 6.0        # dB tolerance
    
    def __post_init__(self):
        if self.calibration_frequencies is None:
            # Default calibration frequencies for medical audio
            self.calibration_frequencies = [
                100, 200, 400, 800, 1000, 1600, 2000
            ]


class AudioCalibration:
    """
    Audio system calibration for medical sound analysis.
    
    Provides comprehensive audio calibration including microphone sensitivity,
    noise floor measurement, frequency response calibration, and quality assessment.
    """
    
    def __init__(self, 
                 sample_rate: int = 8000,
                 config: Optional[CalibrationConfig] = None):
        """
        Initialize audio calibration.
        
        Args:
            sample_rate: Audio sample rate
            config: Calibration configuration
        """
        self.sample_rate = sample_rate
        self.config = config or CalibrationConfig()
        
        # Audio components
        self.audio_manager = AudioManager(sample_rate=sample_rate)
        self.preprocessor = AudioPreprocessor(sample_rate=sample_rate)
        self.feature_extractor = AudioFeatureExtractor(sample_rate=sample_rate)
        
        # Calibration results
        self.calibration_results = {}
        self.is_calibrated = False
        self.calibration_timestamp = None
        
        # Reference measurements
        self.noise_floor = None
        self.sensitivity_factor = 1.0
        self.frequency_response = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Audio calibration system initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize calibration system.
        
        Returns:
            bool: True if successful
        """
        try:
            # Initialize audio manager
            if not await self.audio_manager.initialize():
                self.logger.error("Failed to initialize audio manager")
                return False
            
            self.logger.info("Audio calibration system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio calibration initialization failed: {e}")
            return False
    
    async def run_full_calibration(self) -> Dict[str, Any]:
        """
        Run complete audio calibration sequence.
        
        Returns:
            dict: Calibration results
        """
        try:
            self.logger.info("Starting full audio calibration")
            
            calibration_results = {
                'timestamp': datetime.now().isoformat(),
                'sample_rate': self.sample_rate,
                'success': False,
                'steps': {}
            }
            
            # Step 1: Measure noise floor
            self.logger.info("Step 1: Measuring noise floor")
            noise_result = await self._measure_noise_floor()
            calibration_results['steps']['noise_floor'] = noise_result
            
            if not noise_result.get('success', False):
                self.logger.error("Noise floor measurement failed")
                return calibration_results
            
            # Step 2: Calibrate microphone sensitivity
            self.logger.info("Step 2: Calibrating microphone sensitivity")
            sensitivity_result = await self._calibrate_sensitivity()
            calibration_results['steps']['sensitivity'] = sensitivity_result
            
            if not sensitivity_result.get('success', False):
                self.logger.warning("Sensitivity calibration failed, using default")
            
            # Step 3: Measure frequency response
            self.logger.info("Step 3: Measuring frequency response")
            freq_response_result = await self._measure_frequency_response()
            calibration_results['steps']['frequency_response'] = freq_response_result
            
            if not freq_response_result.get('success', False):
                self.logger.warning("Frequency response measurement failed")
            
            # Step 4: Validate calibration
            self.logger.info("Step 4: Validating calibration")
            validation_result = await self._validate_calibration()
            calibration_results['steps']['validation'] = validation_result
            
            # Determine overall success
            calibration_results['success'] = (
                noise_result.get('success', False) and
                validation_result.get('success', False)
            )
            
            if calibration_results['success']:
                self.is_calibrated = True
                self.calibration_timestamp = datetime.now()
                self.calibration_results = calibration_results
                self.logger.info("Audio calibration completed successfully")
            else:
                self.logger.error("Audio calibration failed")
            
            return calibration_results
            
        except Exception as e:
            self.logger.error(f"Error in full calibration: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _measure_noise_floor(self) -> Dict[str, Any]:
        """
        Measure ambient noise floor.
        
        Returns:
            dict: Noise floor measurement results
        """
        try:
            self.logger.info("Measuring ambient noise floor...")
            
            noise_measurements = []
            
            for i in range(self.config.noise_samples):
                self.logger.debug(f"Noise measurement {i+1}/{self.config.noise_samples}")
                
                # Record ambient noise
                noise_audio = self.audio_manager.record_audio(
                    self.config.noise_measurement_duration
                )
                
                if noise_audio is None:
                    continue
                
                # Preprocess audio
                processed_audio, _ = self.preprocessor.preprocess(noise_audio)
                
                # Calculate noise level
                noise_level = np.sqrt(np.mean(processed_audio.astype(np.float32) ** 2))
                noise_measurements.append(noise_level)
                
                # Wait between measurements
                await asyncio.sleep(0.5)
            
            if not noise_measurements:
                return {
                    'success': False,
                    'error': 'No noise measurements obtained'
                }
            
            # Calculate statistics
            noise_floor = np.mean(noise_measurements)
            noise_std = np.std(noise_measurements)
            noise_max = np.max(noise_measurements)
            noise_min = np.min(noise_measurements)
            
            # Convert to dB
            noise_floor_db = 20 * np.log10(noise_floor + 1e-10)
            
            # Store noise floor
            self.noise_floor = noise_floor
            
            result = {
                'success': True,
                'noise_floor_linear': float(noise_floor),
                'noise_floor_db': float(noise_floor_db),
                'noise_std': float(noise_std),
                'noise_max': float(noise_max),
                'noise_min': float(noise_min),
                'measurements_count': len(noise_measurements),
                'quality': 'good' if noise_floor_db < -40 else 'fair' if noise_floor_db < -30 else 'poor'
            }
            
            self.logger.info(f"Noise floor: {noise_floor_db:.1f} dB ({result['quality']})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error measuring noise floor: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _calibrate_sensitivity(self) -> Dict[str, Any]:
        """
        Calibrate microphone sensitivity using reference tone.
        
        Returns:
            dict: Sensitivity calibration results
        """
        try:
            self.logger.info("Calibrating microphone sensitivity...")
            
            # This would typically require a calibrated reference tone
            # For now, we'll use a simplified approach
            
            # Generate reference tone (would be external in real system)
            reference_freq = 1000.0  # 1 kHz reference
            tone_duration = self.config.tone_duration
            
            self.logger.info(f"Please play a {reference_freq} Hz tone at known level")
            self.logger.info("Recording reference tone...")
            
            # Record reference tone
            reference_audio = self.audio_manager.record_audio(tone_duration)
            
            if reference_audio is None:
                return {
                    'success': False,
                    'error': 'Failed to record reference tone'
                }
            
            # Preprocess audio
            processed_audio, _ = self.preprocessor.preprocess(reference_audio)
            
            # Extract features
            features = self.feature_extractor.extract_features(processed_audio)
            
            # Analyze reference tone
            if 'spectrogram' in features:
                spectrogram = features['spectrogram']
                freqs = np.linspace(0, self.sample_rate / 2, spectrogram.shape[0])
                
                # Find peak at reference frequency
                ref_freq_idx = np.argmin(np.abs(freqs - reference_freq))
                ref_energy = np.mean(spectrogram[ref_freq_idx, :])
                
                # Calculate sensitivity factor
                # This would use known reference level in real system
                measured_level_db = 20 * np.log10(ref_energy + 1e-10)
                sensitivity_error = measured_level_db - self.config.reference_level_db
                
                # Update sensitivity factor
                self.sensitivity_factor = 10 ** (-sensitivity_error / 20)
                
                result = {
                    'success': True,
                    'reference_frequency': reference_freq,
                    'measured_level_db': float(measured_level_db),
                    'reference_level_db': self.config.reference_level_db,
                    'sensitivity_error_db': float(sensitivity_error),
                    'sensitivity_factor': float(self.sensitivity_factor),
                    'within_tolerance': abs(sensitivity_error) <= self.config.sensitivity_tolerance
                }
                
                self.logger.info(f"Sensitivity error: {sensitivity_error:.1f} dB")
                return result
            
            return {
                'success': False,
                'error': 'Failed to analyze reference tone'
            }
            
        except Exception as e:
            self.logger.error(f"Error calibrating sensitivity: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _measure_frequency_response(self) -> Dict[str, Any]:
        """
        Measure frequency response using calibration tones.
        
        Returns:
            dict: Frequency response measurement results
        """
        try:
            self.logger.info("Measuring frequency response...")
            
            frequency_responses = {}
            
            for freq in self.config.calibration_frequencies:
                self.logger.debug(f"Measuring response at {freq} Hz")
                
                # This would require external tone generation in real system
                self.logger.info(f"Please play {freq} Hz calibration tone")
                
                # Record calibration tone
                tone_audio = self.audio_manager.record_audio(self.config.tone_duration)
                
                if tone_audio is None:
                    continue
                
                # Preprocess audio
                processed_audio, _ = self.preprocessor.preprocess(tone_audio)
                
                # Extract features
                features = self.feature_extractor.extract_features(processed_audio)
                
                if 'spectrogram' in features:
                    spectrogram = features['spectrogram']
                    freqs = np.linspace(0, self.sample_rate / 2, spectrogram.shape[0])
                    
                    # Find energy at calibration frequency
                    freq_idx = np.argmin(np.abs(freqs - freq))
                    freq_energy = np.mean(spectrogram[freq_idx, :])
                    freq_level_db = 20 * np.log10(freq_energy + 1e-10)
                    
                    frequency_responses[freq] = {
                        'frequency': freq,
                        'level_db': float(freq_level_db),
                        'energy': float(freq_energy)
                    }
                
                await asyncio.sleep(0.5)
            
            if not frequency_responses:
                return {
                    'success': False,
                    'error': 'No frequency response measurements obtained'
                }
            
            # Calculate frequency response statistics
            levels = [resp['level_db'] for resp in frequency_responses.values()]
            mean_level = np.mean(levels)
            level_variation = np.max(levels) - np.min(levels)
            
            # Store frequency response
            self.frequency_response = frequency_responses
            
            result = {
                'success': True,
                'frequency_responses': frequency_responses,
                'mean_level_db': float(mean_level),
                'level_variation_db': float(level_variation),
                'within_tolerance': level_variation <= self.config.freq_response_tolerance,
                'frequencies_tested': len(frequency_responses)
            }
            
            self.logger.info(f"Frequency response variation: {level_variation:.1f} dB")
            return result
            
        except Exception as e:
            self.logger.error(f"Error measuring frequency response: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _validate_calibration(self) -> Dict[str, Any]:
        """
        Validate calibration by testing with known signals.
        
        Returns:
            dict: Validation results
        """
        try:
            self.logger.info("Validating calibration...")
            
            # Test with silence
            silence_test = await self._test_silence_detection()
            
            # Test with tone
            tone_test = await self._test_tone_detection()
            
            # Overall validation
            validation_success = (
                silence_test.get('success', False) and
                tone_test.get('success', False)
            )
            
            result = {
                'success': validation_success,
                'silence_test': silence_test,
                'tone_test': tone_test,
                'overall_quality': 'good' if validation_success else 'poor'
            }
            
            self.logger.info(f"Calibration validation: {'PASSED' if validation_success else 'FAILED'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating calibration: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _test_silence_detection(self) -> Dict[str, Any]:
        """Test silence detection capability."""
        try:
            self.logger.debug("Testing silence detection...")
            
            # Record silence
            silence_audio = self.audio_manager.record_audio(2.0)
            
            if silence_audio is None:
                return {'success': False, 'error': 'Failed to record silence'}
            
            # Preprocess
            processed_audio, _ = self.preprocessor.preprocess(silence_audio)
            
            # Calculate level
            silence_level = np.sqrt(np.mean(processed_audio.astype(np.float32) ** 2))
            silence_level_db = 20 * np.log10(silence_level + 1e-10)
            
            # Check if silence is detected properly
            silence_detected = silence_level_db < -30  # -30 dB threshold
            
            return {
                'success': silence_detected,
                'silence_level_db': float(silence_level_db),
                'threshold_db': -30.0,
                'detected': silence_detected
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_tone_detection(self) -> Dict[str, Any]:
        """Test tone detection capability."""
        try:
            self.logger.debug("Testing tone detection...")
            
            # This would require external tone in real system
            self.logger.info("Please play 1000 Hz test tone")
            
            # Record tone
            tone_audio = self.audio_manager.record_audio(2.0)
            
            if tone_audio is None:
                return {'success': False, 'error': 'Failed to record tone'}
            
            # Preprocess
            processed_audio, _ = self.preprocessor.preprocess(tone_audio)
            
            # Extract features
            features = self.feature_extractor.extract_features(processed_audio)
            
            if 'spectrogram' in features:
                spectrogram = features['spectrogram']
                freqs = np.linspace(0, self.sample_rate / 2, spectrogram.shape[0])
                
                # Find peak frequency
                freq_energies = np.mean(spectrogram, axis=1)
                peak_idx = np.argmax(freq_energies)
                peak_freq = freqs[peak_idx]
                
                # Check if 1000 Hz tone is detected
                tone_detected = abs(peak_freq - 1000.0) < 50.0  # 50 Hz tolerance
                
                return {
                    'success': tone_detected,
                    'expected_frequency': 1000.0,
                    'detected_frequency': float(peak_freq),
                    'frequency_error': float(abs(peak_freq - 1000.0)),
                    'detected': tone_detected
                }
            
            return {'success': False, 'error': 'Failed to analyze tone'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def apply_calibration(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply calibration corrections to audio data.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            np.ndarray: Calibrated audio data
        """
        try:
            if not self.is_calibrated:
                self.logger.warning("Calibration not performed, returning original data")
                return audio_data
            
            # Apply sensitivity correction
            calibrated_audio = audio_data.astype(np.float32) * self.sensitivity_factor
            
            # Apply noise floor subtraction if needed
            if self.noise_floor is not None:
                # Simple noise gate
                noise_gate_threshold = self.noise_floor * 2.0
                mask = np.abs(calibrated_audio) > noise_gate_threshold
                calibrated_audio = calibrated_audio * mask
            
            # Convert back to original dtype
            if audio_data.dtype == np.int16:
                calibrated_audio = np.clip(calibrated_audio, -32768, 32767).astype(np.int16)
            
            return calibrated_audio
            
        except Exception as e:
            self.logger.error(f"Error applying calibration: {e}")
            return audio_data
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """
        Get current calibration status.
        
        Returns:
            dict: Calibration status
        """
        return {
            'is_calibrated': self.is_calibrated,
            'calibration_timestamp': self.calibration_timestamp.isoformat() if self.calibration_timestamp else None,
            'noise_floor': self.noise_floor,
            'sensitivity_factor': self.sensitivity_factor,
            'frequency_response_points': len(self.frequency_response),
            'calibration_results': self.calibration_results
        }
    
    def reset_calibration(self):
        """Reset calibration to default state."""
        self.is_calibrated = False
        self.calibration_timestamp = None
        self.calibration_results = {}
        self.noise_floor = None
        self.sensitivity_factor = 1.0
        self.frequency_response = {}
        
        self.logger.info("Calibration reset to default state")
    
    async def shutdown(self):
        """Shutdown calibration system."""
        try:
            self.logger.info("Shutting down audio calibration system")
            
            # Shutdown audio manager
            if self.audio_manager:
                await self.audio_manager.shutdown()
            
            self.logger.info("Audio calibration system shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during calibration shutdown: {e}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_audio_calibration():
        """Test audio calibration functionality."""
        # Create calibration system
        config = CalibrationConfig(
            noise_measurement_duration=2.0,
            noise_samples=3,
            tone_duration=1.0
        )
        
        calibration = AudioCalibration(sample_rate=8000, config=config)
        
        # Initialize
        if await calibration.initialize():
            print("Audio calibration system initialized successfully")
            
            # Run calibration
            print("Running calibration (this will require user interaction)...")
            results = await calibration.run_full_calibration()
            
            print(f"Calibration results: {results}")
            
            # Get status
            status = calibration.get_calibration_status()
            print(f"Calibration status: {status}")
            
            # Test calibration application
            if calibration.is_calibrated:
                test_audio = np.random.randn(8000).astype(np.int16)
                calibrated_audio = calibration.apply_calibration(test_audio)
                print(f"Applied calibration to test audio: {len(calibrated_audio)} samples")
            
        else:
            print("Failed to initialize audio calibration system")
        
        # Shutdown
        await calibration.shutdown()
    
    # Run test
    asyncio.run(test_audio_calibration())