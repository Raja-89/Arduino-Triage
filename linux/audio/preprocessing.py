#!/usr/bin/env python3
"""
Smart Rural Triage Station - Audio Preprocessing
===============================================

This module handles audio signal preprocessing including filtering,
noise reduction, normalization, and quality enhancement.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import numpy as np
import scipy.signal
import scipy.fft
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PreprocessingConfig:
    """Configuration for audio preprocessing."""
    
    # Filtering
    highpass_freq: float = 20.0      # High-pass filter frequency (Hz)
    lowpass_freq: float = 2000.0     # Low-pass filter frequency (Hz)
    notch_freq: float = 50.0         # Notch filter frequency (Hz) for power line noise
    notch_q: float = 30.0            # Notch filter Q factor
    
    # Noise reduction
    noise_reduction_enabled: bool = True
    noise_floor_percentile: float = 10.0  # Percentile for noise floor estimation
    noise_reduction_factor: float = 0.5   # Noise reduction strength (0-1)
    
    # Normalization
    normalize_enabled: bool = True
    target_rms: float = 0.1          # Target RMS level after normalization
    
    # Quality enhancement
    dynamic_range_compression: bool = True
    compression_ratio: float = 3.0    # Compression ratio
    compression_threshold: float = 0.3  # Compression threshold
    
    # Artifact removal
    remove_dc_offset: bool = True
    remove_clicks: bool = True
    click_threshold: float = 3.0      # Click detection threshold (std devs)


class AudioPreprocessor:
    """
    Audio signal preprocessing for medical sound analysis.
    
    Provides comprehensive audio preprocessing including filtering,
    noise reduction, normalization, and artifact removal optimized
    for heart and lung sound analysis.
    """
    
    def __init__(self, sample_rate: int = 8000, config: Optional[PreprocessingConfig] = None):
        """
        Initialize audio preprocessor.
        
        Args:
            sample_rate: Audio sample rate in Hz
            config: Preprocessing configuration
        """
        self.sample_rate = sample_rate
        self.config = config or PreprocessingConfig()
        
        # Filter coefficients (computed once for efficiency)
        self._filter_coefficients = {}
        self._compute_filter_coefficients()
        
        # Noise profile for adaptive noise reduction
        self._noise_profile = None
        
        # Statistics
        self.stats = {
            'samples_processed': 0,
            'dc_offset_removed': 0,
            'clicks_removed': 0,
            'noise_reduction_applied': 0,
            'normalization_applied': 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Audio preprocessor initialized - Sample rate: {sample_rate}Hz")
    
    def _compute_filter_coefficients(self):
        """Compute filter coefficients for efficient processing."""
        try:
            nyquist = self.sample_rate / 2.0
            
            # High-pass filter (remove very low frequencies)
            if self.config.highpass_freq > 0:
                hp_freq = min(self.config.highpass_freq, nyquist * 0.95)
                self._filter_coefficients['highpass'] = scipy.signal.butter(
                    4, hp_freq / nyquist, btype='high'
                )
            
            # Low-pass filter (remove high-frequency noise)
            if self.config.lowpass_freq < nyquist:
                lp_freq = min(self.config.lowpass_freq, nyquist * 0.95)
                self._filter_coefficients['lowpass'] = scipy.signal.butter(
                    4, lp_freq / nyquist, btype='low'
                )
            
            # Notch filter (remove power line noise)
            if self.config.notch_freq > 0:
                notch_freq = min(self.config.notch_freq, nyquist * 0.95)
                self._filter_coefficients['notch'] = scipy.signal.iirnotch(
                    notch_freq / nyquist, self.config.notch_q
                )
            
            self.logger.debug("Filter coefficients computed")
            
        except Exception as e:
            self.logger.error(f"Error computing filter coefficients: {e}")
    
    def preprocess(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply complete preprocessing pipeline to audio data.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            tuple: (processed_audio, processing_info)
        """
        try:
            if len(audio_data) == 0:
                return audio_data, {}
            
            # Convert to float for processing
            processed_audio = audio_data.astype(np.float32)
            processing_info = {}
            
            # Step 1: Remove DC offset
            if self.config.remove_dc_offset:
                processed_audio, dc_info = self._remove_dc_offset(processed_audio)
                processing_info['dc_removal'] = dc_info
            
            # Step 2: Remove clicks and artifacts
            if self.config.remove_clicks:
                processed_audio, click_info = self._remove_clicks(processed_audio)
                processing_info['click_removal'] = click_info
            
            # Step 3: Apply filtering
            processed_audio, filter_info = self._apply_filters(processed_audio)
            processing_info['filtering'] = filter_info
            
            # Step 4: Noise reduction
            if self.config.noise_reduction_enabled:
                processed_audio, noise_info = self._reduce_noise(processed_audio)
                processing_info['noise_reduction'] = noise_info
            
            # Step 5: Dynamic range compression
            if self.config.dynamic_range_compression:
                processed_audio, compression_info = self._apply_compression(processed_audio)
                processing_info['compression'] = compression_info
            
            # Step 6: Normalization
            if self.config.normalize_enabled:
                processed_audio, norm_info = self._normalize_audio(processed_audio)
                processing_info['normalization'] = norm_info
            
            # Update statistics
            self.stats['samples_processed'] += len(audio_data)
            
            # Convert back to int16 if needed
            if audio_data.dtype == np.int16:
                processed_audio = np.clip(processed_audio * 32767, -32768, 32767).astype(np.int16)
            
            self.logger.debug(f"Preprocessed {len(audio_data)} samples")
            return processed_audio, processing_info
            
        except Exception as e:
            self.logger.error(f"Error in preprocessing: {e}")
            return audio_data, {'error': str(e)}
    
    def _remove_dc_offset(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Remove DC offset from audio signal.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            tuple: (processed_audio, info)
        """
        try:
            dc_offset = np.mean(audio_data)
            processed_audio = audio_data - dc_offset
            
            self.stats['dc_offset_removed'] += 1
            
            return processed_audio, {
                'dc_offset': float(dc_offset),
                'applied': True
            }
            
        except Exception as e:
            self.logger.error(f"Error removing DC offset: {e}")
            return audio_data, {'applied': False, 'error': str(e)}
    
    def _remove_clicks(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Remove clicks and impulse noise from audio signal.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            tuple: (processed_audio, info)
        """
        try:
            # Detect clicks using derivative and threshold
            diff_signal = np.diff(audio_data)
            threshold = self.config.click_threshold * np.std(diff_signal)
            
            # Find click locations
            click_indices = np.where(np.abs(diff_signal) > threshold)[0]
            
            processed_audio = audio_data.copy()
            clicks_removed = 0
            
            # Remove clicks by interpolation
            for idx in click_indices:
                # Define interpolation window
                start_idx = max(0, idx - 2)
                end_idx = min(len(processed_audio), idx + 3)
                
                if end_idx - start_idx > 2:
                    # Linear interpolation
                    x = np.array([start_idx, end_idx - 1])
                    y = np.array([processed_audio[start_idx], processed_audio[end_idx - 1]])
                    
                    interp_indices = np.arange(start_idx + 1, end_idx - 1)
                    if len(interp_indices) > 0:
                        processed_audio[interp_indices] = np.interp(interp_indices, x, y)
                        clicks_removed += 1
            
            self.stats['clicks_removed'] += clicks_removed
            
            return processed_audio, {
                'clicks_detected': len(click_indices),
                'clicks_removed': clicks_removed,
                'applied': True
            }
            
        except Exception as e:
            self.logger.error(f"Error removing clicks: {e}")
            return audio_data, {'applied': False, 'error': str(e)}
    
    def _apply_filters(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply frequency domain filtering.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            tuple: (processed_audio, info)
        """
        try:
            processed_audio = audio_data.copy()
            filters_applied = []
            
            # High-pass filter
            if 'highpass' in self._filter_coefficients:
                b, a = self._filter_coefficients['highpass']
                processed_audio = scipy.signal.filtfilt(b, a, processed_audio)
                filters_applied.append('highpass')
            
            # Low-pass filter
            if 'lowpass' in self._filter_coefficients:
                b, a = self._filter_coefficients['lowpass']
                processed_audio = scipy.signal.filtfilt(b, a, processed_audio)
                filters_applied.append('lowpass')
            
            # Notch filter
            if 'notch' in self._filter_coefficients:
                b, a = self._filter_coefficients['notch']
                processed_audio = scipy.signal.filtfilt(b, a, processed_audio)
                filters_applied.append('notch')
            
            return processed_audio, {
                'filters_applied': filters_applied,
                'applied': len(filters_applied) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
            return audio_data, {'applied': False, 'error': str(e)}
    
    def _reduce_noise(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply spectral noise reduction.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            tuple: (processed_audio, info)
        """
        try:
            # Estimate noise profile if not available
            if self._noise_profile is None:
                self._estimate_noise_profile(audio_data)
            
            # Apply spectral subtraction
            processed_audio = self._spectral_subtraction(audio_data)
            
            self.stats['noise_reduction_applied'] += 1
            
            return processed_audio, {
                'method': 'spectral_subtraction',
                'reduction_factor': self.config.noise_reduction_factor,
                'applied': True
            }
            
        except Exception as e:
            self.logger.error(f"Error in noise reduction: {e}")
            return audio_data, {'applied': False, 'error': str(e)}
    
    def _estimate_noise_profile(self, audio_data: np.ndarray):
        """
        Estimate noise profile from quiet segments.
        
        Args:
            audio_data: Input audio data
        """
        try:
            # Find quiet segments (bottom percentile)
            rms_window_size = int(0.1 * self.sample_rate)  # 100ms windows
            rms_values = []
            
            for i in range(0, len(audio_data) - rms_window_size, rms_window_size // 2):
                window = audio_data[i:i + rms_window_size]
                rms = np.sqrt(np.mean(window ** 2))
                rms_values.append(rms)
            
            if rms_values:
                noise_threshold = np.percentile(rms_values, self.config.noise_floor_percentile)
                
                # Extract noise segments
                noise_segments = []
                for i, rms in enumerate(rms_values):
                    if rms <= noise_threshold:
                        start_idx = i * (rms_window_size // 2)
                        end_idx = start_idx + rms_window_size
                        noise_segments.append(audio_data[start_idx:end_idx])
                
                if noise_segments:
                    noise_signal = np.concatenate(noise_segments)
                    
                    # Compute noise spectrum
                    noise_fft = scipy.fft.fft(noise_signal)
                    self._noise_profile = np.abs(noise_fft)
                    
                    self.logger.debug(f"Noise profile estimated from {len(noise_segments)} segments")
            
        except Exception as e:
            self.logger.error(f"Error estimating noise profile: {e}")
    
    def _spectral_subtraction(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply spectral subtraction for noise reduction.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            np.ndarray: Noise-reduced audio
        """
        try:
            if self._noise_profile is None:
                return audio_data
            
            # Compute signal spectrum
            signal_fft = scipy.fft.fft(audio_data)
            signal_magnitude = np.abs(signal_fft)
            signal_phase = np.angle(signal_fft)
            
            # Resize noise profile to match signal length
            if len(self._noise_profile) != len(signal_magnitude):
                noise_profile = np.interp(
                    np.linspace(0, 1, len(signal_magnitude)),
                    np.linspace(0, 1, len(self._noise_profile)),
                    self._noise_profile
                )
            else:
                noise_profile = self._noise_profile
            
            # Apply spectral subtraction
            alpha = self.config.noise_reduction_factor
            enhanced_magnitude = signal_magnitude - alpha * noise_profile
            
            # Prevent over-subtraction
            enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * signal_magnitude)
            
            # Reconstruct signal
            enhanced_fft = enhanced_magnitude * np.exp(1j * signal_phase)
            enhanced_audio = np.real(scipy.fft.ifft(enhanced_fft))
            
            return enhanced_audio.astype(audio_data.dtype)
            
        except Exception as e:
            self.logger.error(f"Error in spectral subtraction: {e}")
            return audio_data
    
    def _apply_compression(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply dynamic range compression.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            tuple: (processed_audio, info)
        """
        try:
            # Calculate envelope
            envelope = np.abs(audio_data)
            
            # Apply smoothing to envelope
            window_size = int(0.01 * self.sample_rate)  # 10ms window
            if window_size > 1:
                kernel = np.ones(window_size) / window_size
                envelope = np.convolve(envelope, kernel, mode='same')
            
            # Apply compression
            threshold = self.config.compression_threshold
            ratio = self.config.compression_ratio
            
            # Compute gain reduction
            gain = np.ones_like(envelope)
            above_threshold = envelope > threshold
            
            if np.any(above_threshold):
                excess = envelope[above_threshold] - threshold
                compressed_excess = excess / ratio
                gain[above_threshold] = (threshold + compressed_excess) / envelope[above_threshold]
            
            # Apply gain smoothing to avoid artifacts
            if window_size > 1:
                gain = np.convolve(gain, kernel, mode='same')
            
            # Apply compression
            processed_audio = audio_data * gain
            
            compression_amount = np.mean(1.0 - gain[above_threshold]) if np.any(above_threshold) else 0.0
            
            return processed_audio, {
                'threshold': threshold,
                'ratio': ratio,
                'compression_amount': float(compression_amount),
                'applied': True
            }
            
        except Exception as e:
            self.logger.error(f"Error applying compression: {e}")
            return audio_data, {'applied': False, 'error': str(e)}
    
    def _normalize_audio(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Normalize audio to target RMS level.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            tuple: (processed_audio, info)
        """
        try:
            # Calculate current RMS
            current_rms = np.sqrt(np.mean(audio_data ** 2))
            
            if current_rms > 0:
                # Calculate gain factor
                gain_factor = self.config.target_rms / current_rms
                
                # Apply normalization
                processed_audio = audio_data * gain_factor
                
                self.stats['normalization_applied'] += 1
                
                return processed_audio, {
                    'original_rms': float(current_rms),
                    'target_rms': self.config.target_rms,
                    'gain_factor': float(gain_factor),
                    'applied': True
                }
            else:
                return audio_data, {
                    'applied': False,
                    'reason': 'zero_rms'
                }
            
        except Exception as e:
            self.logger.error(f"Error normalizing audio: {e}")
            return audio_data, {'applied': False, 'error': str(e)}
    
    def update_noise_profile(self, noise_audio: np.ndarray):
        """
        Update noise profile with new noise sample.
        
        Args:
            noise_audio: Pure noise audio sample
        """
        try:
            if len(noise_audio) > 0:
                noise_fft = scipy.fft.fft(noise_audio)
                new_noise_profile = np.abs(noise_fft)
                
                if self._noise_profile is None:
                    self._noise_profile = new_noise_profile
                else:
                    # Exponential moving average
                    alpha = 0.1
                    if len(new_noise_profile) == len(self._noise_profile):
                        self._noise_profile = (1 - alpha) * self._noise_profile + alpha * new_noise_profile
                    else:
                        self._noise_profile = new_noise_profile
                
                self.logger.info("Noise profile updated")
            
        except Exception as e:
            self.logger.error(f"Error updating noise profile: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get preprocessing statistics.
        
        Returns:
            dict: Processing statistics
        """
        return {
            'sample_rate': self.sample_rate,
            'config': {
                'highpass_freq': self.config.highpass_freq,
                'lowpass_freq': self.config.lowpass_freq,
                'notch_freq': self.config.notch_freq,
                'noise_reduction_enabled': self.config.noise_reduction_enabled,
                'normalize_enabled': self.config.normalize_enabled,
                'dynamic_range_compression': self.config.dynamic_range_compression
            },
            'stats': self.stats.copy(),
            'noise_profile_available': self._noise_profile is not None
        }
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            'samples_processed': 0,
            'dc_offset_removed': 0,
            'clicks_removed': 0,
            'noise_reduction_applied': 0,
            'normalization_applied': 0
        }
        self.logger.info("Statistics reset")


# Example usage and testing
if __name__ == "__main__":
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    def test_audio_preprocessor():
        """Test audio preprocessor functionality."""
        # Create test signal
        sample_rate = 8000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create test signal with noise and artifacts
        signal = (
            0.5 * np.sin(2 * np.pi * 100 * t) +  # 100 Hz heart sound component
            0.3 * np.sin(2 * np.pi * 300 * t) +  # 300 Hz lung sound component
            0.1 * np.random.randn(len(t)) +      # White noise
            0.05 * np.sin(2 * np.pi * 50 * t)    # 50 Hz power line noise
        )
        
        # Add DC offset
        signal += 0.1
        
        # Add some clicks
        click_indices = [1000, 5000, 10000]
        for idx in click_indices:
            if idx < len(signal):
                signal[idx] += 2.0
        
        # Convert to int16
        test_audio = (signal * 32767).astype(np.int16)
        
        print(f"Original signal - Length: {len(test_audio)}, RMS: {np.sqrt(np.mean(test_audio.astype(np.float32) ** 2)):.0f}")
        
        # Create preprocessor
        config = PreprocessingConfig(
            highpass_freq=20.0,
            lowpass_freq=2000.0,
            notch_freq=50.0,
            noise_reduction_enabled=True,
            normalize_enabled=True,
            remove_clicks=True
        )
        
        preprocessor = AudioPreprocessor(sample_rate=sample_rate, config=config)
        
        # Process audio
        processed_audio, processing_info = preprocessor.preprocess(test_audio)
        
        print(f"Processed signal - Length: {len(processed_audio)}, RMS: {np.sqrt(np.mean(processed_audio.astype(np.float32) ** 2)):.0f}")
        print(f"Processing info: {processing_info}")
        
        # Get statistics
        stats = preprocessor.get_statistics()
        print(f"Preprocessor statistics: {stats}")
        
        # Test noise profile update
        noise_sample = (0.1 * np.random.randn(sample_rate)).astype(np.float32)
        preprocessor.update_noise_profile(noise_sample)
        
        print("Audio preprocessor test completed")
    
    # Run test
    test_audio_preprocessor()