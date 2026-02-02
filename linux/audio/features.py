#!/usr/bin/env python3
"""
Smart Rural Triage Station - Audio Feature Extraction
====================================================

This module handles audio feature extraction including mel-spectrograms,
MFCCs, and other features optimized for medical sound analysis.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import numpy as np
import scipy.signal
import scipy.fft
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FeatureConfig:
    """Configuration for feature extraction."""
    
    # Spectrogram parameters
    n_fft: int = 512                 # FFT window size
    hop_length: int = 256            # Hop length for STFT
    window: str = 'hann'             # Window function
    
    # Mel-spectrogram parameters
    n_mels: int = 64                 # Number of mel bands
    fmin: float = 20.0               # Minimum frequency
    fmax: Optional[float] = None     # Maximum frequency (None = Nyquist)
    
    # MFCC parameters
    n_mfcc: int = 13                 # Number of MFCC coefficients
    dct_type: int = 2                # DCT type
    norm: str = 'ortho'              # DCT normalization
    
    # Spectral features
    spectral_centroid: bool = True
    spectral_bandwidth: bool = True
    spectral_rolloff: bool = True
    zero_crossing_rate: bool = True
    
    # Time-domain features
    rms_energy: bool = True
    peak_amplitude: bool = True
    crest_factor: bool = True
    
    # Medical-specific features
    heart_rate_features: bool = True
    respiratory_features: bool = True


class MelFilterBank:
    """Mel-scale filter bank for mel-spectrogram computation."""
    
    def __init__(self, sample_rate: int, n_fft: int, n_mels: int, 
                 fmin: float = 0.0, fmax: Optional[float] = None):
        """
        Initialize mel filter bank.
        
        Args:
            sample_rate: Audio sample rate
            n_fft: FFT size
            n_mels: Number of mel bands
            fmin: Minimum frequency
            fmax: Maximum frequency
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.n_mels = n_mels
        self.fmin = fmin
        self.fmax = fmax or sample_rate / 2.0
        
        # Create mel filter bank
        self.mel_filters = self._create_mel_filters()
    
    def _hz_to_mel(self, hz: float) -> float:
        """Convert Hz to mel scale."""
        return 2595.0 * np.log10(1.0 + hz / 700.0)
    
    def _mel_to_hz(self, mel: float) -> float:
        """Convert mel scale to Hz."""
        return 700.0 * (10.0**(mel / 2595.0) - 1.0)
    
    def _create_mel_filters(self) -> np.ndarray:
        """Create mel-scale filter bank."""
        # Convert frequency range to mel scale
        mel_min = self._hz_to_mel(self.fmin)
        mel_max = self._hz_to_mel(self.fmax)
        
        # Create equally spaced mel points
        mel_points = np.linspace(mel_min, mel_max, self.n_mels + 2)
        hz_points = [self._mel_to_hz(mel) for mel in mel_points]
        
        # Convert to FFT bin indices
        bin_points = np.floor((self.n_fft + 1) * np.array(hz_points) / self.sample_rate).astype(int)
        
        # Create filter bank
        filters = np.zeros((self.n_mels, self.n_fft // 2 + 1))
        
        for i in range(self.n_mels):
            left = bin_points[i]
            center = bin_points[i + 1]
            right = bin_points[i + 2]
            
            # Left slope
            for j in range(left, center):
                if center != left:
                    filters[i, j] = (j - left) / (center - left)
            
            # Right slope
            for j in range(center, right):
                if right != center:
                    filters[i, j] = (right - j) / (right - center)
        
        return filters
    
    def apply(self, spectrogram: np.ndarray) -> np.ndarray:
        """
        Apply mel filter bank to spectrogram.
        
        Args:
            spectrogram: Input spectrogram
            
        Returns:
            np.ndarray: Mel-spectrogram
        """
        return np.dot(self.mel_filters, spectrogram)


class AudioFeatureExtractor:
    """
    Audio feature extraction for medical sound analysis.
    
    Extracts comprehensive features including spectrograms, MFCCs,
    and medical-specific features optimized for heart and lung sound analysis.
    """
    
    def __init__(self, sample_rate: int = 8000, config: Optional[FeatureConfig] = None):
        """
        Initialize feature extractor.
        
        Args:
            sample_rate: Audio sample rate
            config: Feature extraction configuration
        """
        self.sample_rate = sample_rate
        self.config = config or FeatureConfig()
        
        # Initialize mel filter bank
        fmax = self.config.fmax or (sample_rate / 2.0)
        self.mel_filter_bank = MelFilterBank(
            sample_rate=sample_rate,
            n_fft=self.config.n_fft,
            n_mels=self.config.n_mels,
            fmin=self.config.fmin,
            fmax=fmax
        )
        
        # DCT matrix for MFCC computation
        self.dct_matrix = self._create_dct_matrix()
        
        # Statistics
        self.stats = {
            'features_extracted': 0,
            'spectrograms_computed': 0,
            'mfccs_computed': 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Feature extractor initialized - Sample rate: {sample_rate}Hz")
    
    def _create_dct_matrix(self) -> np.ndarray:
        """Create DCT matrix for MFCC computation."""
        n = self.config.n_mels
        k = self.config.n_mfcc
        
        dct_matrix = np.zeros((k, n))
        
        for i in range(k):
            for j in range(n):
                if i == 0:
                    dct_matrix[i, j] = 1.0 / np.sqrt(n)
                else:
                    dct_matrix[i, j] = np.sqrt(2.0 / n) * np.cos(np.pi * i * (j + 0.5) / n)
        
        return dct_matrix
    
    def extract_features(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Extract comprehensive feature set from audio data.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            dict: Extracted features
        """
        try:
            if len(audio_data) == 0:
                return {}
            
            # Convert to float for processing
            audio_float = audio_data.astype(np.float32)
            if audio_data.dtype == np.int16:
                audio_float = audio_float / 32768.0
            
            features = {}
            
            # Compute spectrogram
            spectrogram = self._compute_spectrogram(audio_float)
            features['spectrogram'] = spectrogram
            
            # Compute mel-spectrogram
            mel_spectrogram = self._compute_mel_spectrogram(spectrogram)
            features['mel_spectrogram'] = mel_spectrogram
            
            # Compute MFCCs
            if self.config.n_mfcc > 0:
                mfccs = self._compute_mfccs(mel_spectrogram)
                features['mfccs'] = mfccs
            
            # Compute spectral features
            if any([self.config.spectral_centroid, self.config.spectral_bandwidth, 
                   self.config.spectral_rolloff]):
                spectral_features = self._compute_spectral_features(spectrogram)
                features.update(spectral_features)
            
            # Compute time-domain features
            if any([self.config.rms_energy, self.config.peak_amplitude, 
                   self.config.crest_factor, self.config.zero_crossing_rate]):
                time_features = self._compute_time_domain_features(audio_float)
                features.update(time_features)
            
            # Compute medical-specific features
            if self.config.heart_rate_features or self.config.respiratory_features:
                medical_features = self._compute_medical_features(audio_float, spectrogram)
                features.update(medical_features)
            
            # Update statistics
            self.stats['features_extracted'] += 1
            
            self.logger.debug(f"Extracted features from {len(audio_data)} samples")
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return {'error': str(e)}
    
    def _compute_spectrogram(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Compute power spectrogram.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            np.ndarray: Power spectrogram
        """
        try:
            # Compute STFT
            f, t, stft = scipy.signal.stft(
                audio_data,
                fs=self.sample_rate,
                window=self.config.window,
                nperseg=self.config.n_fft,
                noverlap=self.config.n_fft - self.config.hop_length,
                return_onesided=True
            )
            
            # Compute power spectrogram
            spectrogram = np.abs(stft) ** 2
            
            self.stats['spectrograms_computed'] += 1
            
            return spectrogram
            
        except Exception as e:
            self.logger.error(f"Error computing spectrogram: {e}")
            return np.array([])
    
    def _compute_mel_spectrogram(self, spectrogram: np.ndarray) -> np.ndarray:
        """
        Compute mel-spectrogram from power spectrogram.
        
        Args:
            spectrogram: Input power spectrogram
            
        Returns:
            np.ndarray: Mel-spectrogram
        """
        try:
            if spectrogram.size == 0:
                return np.array([])
            
            # Apply mel filter bank
            mel_spectrogram = self.mel_filter_bank.apply(spectrogram)
            
            # Convert to log scale (add small epsilon to avoid log(0))
            mel_spectrogram = np.log(mel_spectrogram + 1e-10)
            
            return mel_spectrogram
            
        except Exception as e:
            self.logger.error(f"Error computing mel-spectrogram: {e}")
            return np.array([])
    
    def _compute_mfccs(self, mel_spectrogram: np.ndarray) -> np.ndarray:
        """
        Compute MFCCs from mel-spectrogram.
        
        Args:
            mel_spectrogram: Input mel-spectrogram
            
        Returns:
            np.ndarray: MFCC coefficients
        """
        try:
            if mel_spectrogram.size == 0:
                return np.array([])
            
            # Apply DCT to mel-spectrogram
            mfccs = np.dot(self.dct_matrix, mel_spectrogram)
            
            self.stats['mfccs_computed'] += 1
            
            return mfccs
            
        except Exception as e:
            self.logger.error(f"Error computing MFCCs: {e}")
            return np.array([])
    
    def _compute_spectral_features(self, spectrogram: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Compute spectral features from spectrogram.
        
        Args:
            spectrogram: Input spectrogram
            
        Returns:
            dict: Spectral features
        """
        features = {}
        
        try:
            if spectrogram.size == 0:
                return features
            
            # Frequency bins
            freqs = np.linspace(0, self.sample_rate / 2, spectrogram.shape[0])
            
            # Spectral centroid
            if self.config.spectral_centroid:
                centroids = []
                for frame in spectrogram.T:
                    if np.sum(frame) > 0:
                        centroid = np.sum(freqs * frame) / np.sum(frame)
                    else:
                        centroid = 0.0
                    centroids.append(centroid)
                features['spectral_centroid'] = np.array(centroids)
            
            # Spectral bandwidth
            if self.config.spectral_bandwidth:
                bandwidths = []
                centroids = features.get('spectral_centroid', [0] * spectrogram.shape[1])
                
                for i, frame in enumerate(spectrogram.T):
                    if np.sum(frame) > 0 and i < len(centroids):
                        bandwidth = np.sqrt(np.sum(((freqs - centroids[i]) ** 2) * frame) / np.sum(frame))
                    else:
                        bandwidth = 0.0
                    bandwidths.append(bandwidth)
                features['spectral_bandwidth'] = np.array(bandwidths)
            
            # Spectral rolloff
            if self.config.spectral_rolloff:
                rolloffs = []
                rolloff_threshold = 0.85  # 85% of energy
                
                for frame in spectrogram.T:
                    if np.sum(frame) > 0:
                        cumsum = np.cumsum(frame)
                        total_energy = cumsum[-1]
                        rolloff_idx = np.where(cumsum >= rolloff_threshold * total_energy)[0]
                        if len(rolloff_idx) > 0:
                            rolloff = freqs[rolloff_idx[0]]
                        else:
                            rolloff = freqs[-1]
                    else:
                        rolloff = 0.0
                    rolloffs.append(rolloff)
                features['spectral_rolloff'] = np.array(rolloffs)
            
        except Exception as e:
            self.logger.error(f"Error computing spectral features: {e}")
        
        return features
    
    def _compute_time_domain_features(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Compute time-domain features.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            dict: Time-domain features
        """
        features = {}
        
        try:
            if len(audio_data) == 0:
                return features
            
            # RMS energy
            if self.config.rms_energy:
                # Frame-wise RMS
                frame_length = self.config.hop_length
                rms_frames = []
                
                for i in range(0, len(audio_data) - frame_length, frame_length):
                    frame = audio_data[i:i + frame_length]
                    rms = np.sqrt(np.mean(frame ** 2))
                    rms_frames.append(rms)
                
                features['rms_energy'] = np.array(rms_frames)
                features['rms_energy_mean'] = np.mean(rms_frames) if rms_frames else 0.0
                features['rms_energy_std'] = np.std(rms_frames) if rms_frames else 0.0
            
            # Peak amplitude
            if self.config.peak_amplitude:
                features['peak_amplitude'] = np.max(np.abs(audio_data))
            
            # Crest factor
            if self.config.crest_factor:
                rms = np.sqrt(np.mean(audio_data ** 2))
                peak = np.max(np.abs(audio_data))
                features['crest_factor'] = peak / rms if rms > 0 else 0.0
            
            # Zero crossing rate
            if self.config.zero_crossing_rate:
                # Frame-wise ZCR
                frame_length = self.config.hop_length
                zcr_frames = []
                
                for i in range(0, len(audio_data) - frame_length, frame_length):
                    frame = audio_data[i:i + frame_length]
                    zcr = np.sum(np.diff(np.sign(frame)) != 0) / (2.0 * len(frame))
                    zcr_frames.append(zcr)
                
                features['zero_crossing_rate'] = np.array(zcr_frames)
                features['zcr_mean'] = np.mean(zcr_frames) if zcr_frames else 0.0
                features['zcr_std'] = np.std(zcr_frames) if zcr_frames else 0.0
            
        except Exception as e:
            self.logger.error(f"Error computing time-domain features: {e}")
        
        return features
    
    def _compute_medical_features(self, audio_data: np.ndarray, spectrogram: np.ndarray) -> Dict[str, Any]:
        """
        Compute medical-specific features.
        
        Args:
            audio_data: Input audio data
            spectrogram: Power spectrogram
            
        Returns:
            dict: Medical features
        """
        features = {}
        
        try:
            # Heart rate features
            if self.config.heart_rate_features:
                heart_features = self._extract_heart_features(audio_data, spectrogram)
                features.update(heart_features)
            
            # Respiratory features
            if self.config.respiratory_features:
                respiratory_features = self._extract_respiratory_features(audio_data, spectrogram)
                features.update(respiratory_features)
            
        except Exception as e:
            self.logger.error(f"Error computing medical features: {e}")
        
        return features
    
    def _extract_heart_features(self, audio_data: np.ndarray, spectrogram: np.ndarray) -> Dict[str, Any]:
        """Extract heart sound specific features."""
        features = {}
        
        try:
            # Heart sound frequency bands
            s1_band = (20, 200)    # S1 heart sound frequency range
            s2_band = (50, 300)    # S2 heart sound frequency range
            murmur_band = (100, 500)  # Heart murmur frequency range
            
            # Extract energy in heart sound bands
            freqs = np.linspace(0, self.sample_rate / 2, spectrogram.shape[0])
            
            # S1 energy
            s1_indices = np.where((freqs >= s1_band[0]) & (freqs <= s1_band[1]))[0]
            if len(s1_indices) > 0:
                s1_energy = np.mean(spectrogram[s1_indices, :], axis=0)
                features['s1_energy'] = s1_energy
                features['s1_energy_mean'] = np.mean(s1_energy)
                features['s1_energy_std'] = np.std(s1_energy)
            
            # S2 energy
            s2_indices = np.where((freqs >= s2_band[0]) & (freqs <= s2_band[1]))[0]
            if len(s2_indices) > 0:
                s2_energy = np.mean(spectrogram[s2_indices, :], axis=0)
                features['s2_energy'] = s2_energy
                features['s2_energy_mean'] = np.mean(s2_energy)
                features['s2_energy_std'] = np.std(s2_energy)
            
            # Murmur energy
            murmur_indices = np.where((freqs >= murmur_band[0]) & (freqs <= murmur_band[1]))[0]
            if len(murmur_indices) > 0:
                murmur_energy = np.mean(spectrogram[murmur_indices, :], axis=0)
                features['murmur_energy'] = murmur_energy
                features['murmur_energy_mean'] = np.mean(murmur_energy)
                features['murmur_energy_std'] = np.std(murmur_energy)
            
            # Heart rate estimation (simplified)
            if len(audio_data) > self.sample_rate:  # At least 1 second of data
                autocorr = np.correlate(audio_data, audio_data, mode='full')
                autocorr = autocorr[len(autocorr)//2:]
                
                # Look for peaks in autocorrelation (heart beats)
                min_hr_samples = int(self.sample_rate * 60 / 200)  # 200 BPM max
                max_hr_samples = int(self.sample_rate * 60 / 40)   # 40 BPM min
                
                search_range = autocorr[min_hr_samples:max_hr_samples]
                if len(search_range) > 0:
                    peak_idx = np.argmax(search_range) + min_hr_samples
                    estimated_hr = 60 * self.sample_rate / peak_idx
                    features['estimated_heart_rate'] = estimated_hr
            
        except Exception as e:
            self.logger.error(f"Error extracting heart features: {e}")
        
        return features
    
    def _extract_respiratory_features(self, audio_data: np.ndarray, spectrogram: np.ndarray) -> Dict[str, Any]:
        """Extract respiratory sound specific features."""
        features = {}
        
        try:
            # Respiratory sound frequency bands
            normal_breath_band = (100, 1000)    # Normal breathing
            wheeze_band = (100, 800)            # Wheeze frequency range
            crackle_band = (200, 2000)          # Crackle frequency range
            
            # Extract energy in respiratory bands
            freqs = np.linspace(0, self.sample_rate / 2, spectrogram.shape[0])
            
            # Normal breathing energy
            breath_indices = np.where((freqs >= normal_breath_band[0]) & (freqs <= normal_breath_band[1]))[0]
            if len(breath_indices) > 0:
                breath_energy = np.mean(spectrogram[breath_indices, :], axis=0)
                features['breath_energy'] = breath_energy
                features['breath_energy_mean'] = np.mean(breath_energy)
                features['breath_energy_std'] = np.std(breath_energy)
            
            # Wheeze energy
            wheeze_indices = np.where((freqs >= wheeze_band[0]) & (freqs <= wheeze_band[1]))[0]
            if len(wheeze_indices) > 0:
                wheeze_energy = np.mean(spectrogram[wheeze_indices, :], axis=0)
                features['wheeze_energy'] = wheeze_energy
                features['wheeze_energy_mean'] = np.mean(wheeze_energy)
                features['wheeze_energy_std'] = np.std(wheeze_energy)
            
            # Crackle energy
            crackle_indices = np.where((freqs >= crackle_band[0]) & (freqs <= crackle_band[1]))[0]
            if len(crackle_indices) > 0:
                crackle_energy = np.mean(spectrogram[crackle_indices, :], axis=0)
                features['crackle_energy'] = crackle_energy
                features['crackle_energy_mean'] = np.mean(crackle_energy)
                features['crackle_energy_std'] = np.std(crackle_energy)
            
            # Respiratory rate estimation (simplified)
            if len(audio_data) > 2 * self.sample_rate:  # At least 2 seconds of data
                # Use envelope for respiratory pattern detection
                envelope = np.abs(scipy.signal.hilbert(audio_data))
                
                # Low-pass filter to get breathing pattern
                sos = scipy.signal.butter(4, 2.0, btype='low', fs=self.sample_rate, output='sos')
                breathing_pattern = scipy.signal.sosfilt(sos, envelope)
                
                # Find peaks (breaths)
                peaks, _ = scipy.signal.find_peaks(breathing_pattern, 
                                                 height=np.max(breathing_pattern) * 0.3,
                                                 distance=self.sample_rate)  # Min 1 second between breaths
                
                if len(peaks) > 1:
                    # Calculate respiratory rate
                    breath_intervals = np.diff(peaks) / self.sample_rate
                    avg_interval = np.mean(breath_intervals)
                    respiratory_rate = 60 / avg_interval  # Breaths per minute
                    features['estimated_respiratory_rate'] = respiratory_rate
            
        except Exception as e:
            self.logger.error(f"Error extracting respiratory features: {e}")
        
        return features
    
    def get_feature_vector(self, features: Dict[str, Any], feature_type: str = 'mfcc') -> np.ndarray:
        """
        Get feature vector for ML model input.
        
        Args:
            features: Extracted features dictionary
            feature_type: Type of features to extract ('mfcc', 'mel', 'combined')
            
        Returns:
            np.ndarray: Feature vector
        """
        try:
            if feature_type == 'mfcc' and 'mfccs' in features:
                # Use MFCC coefficients
                mfccs = features['mfccs']
                if mfccs.size > 0:
                    # Compute statistics across time
                    mfcc_mean = np.mean(mfccs, axis=1)
                    mfcc_std = np.std(mfccs, axis=1)
                    return np.concatenate([mfcc_mean, mfcc_std])
            
            elif feature_type == 'mel' and 'mel_spectrogram' in features:
                # Use mel-spectrogram
                mel_spec = features['mel_spectrogram']
                if mel_spec.size > 0:
                    # Compute statistics across time
                    mel_mean = np.mean(mel_spec, axis=1)
                    mel_std = np.std(mel_spec, axis=1)
                    return np.concatenate([mel_mean, mel_std])
            
            elif feature_type == 'combined':
                # Combine multiple feature types
                feature_vector = []
                
                # Add MFCC features
                if 'mfccs' in features and features['mfccs'].size > 0:
                    mfccs = features['mfccs']
                    mfcc_mean = np.mean(mfccs, axis=1)
                    mfcc_std = np.std(mfccs, axis=1)
                    feature_vector.extend(mfcc_mean)
                    feature_vector.extend(mfcc_std)
                
                # Add spectral features
                for key in ['spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff']:
                    if key in features:
                        values = features[key]
                        if len(values) > 0:
                            feature_vector.extend([np.mean(values), np.std(values)])
                
                # Add time-domain features
                for key in ['rms_energy_mean', 'rms_energy_std', 'zcr_mean', 'zcr_std', 
                           'peak_amplitude', 'crest_factor']:
                    if key in features:
                        feature_vector.append(features[key])
                
                # Add medical features
                for key in ['s1_energy_mean', 's2_energy_mean', 'murmur_energy_mean',
                           'breath_energy_mean', 'wheeze_energy_mean', 'crackle_energy_mean']:
                    if key in features:
                        feature_vector.append(features[key])
                
                return np.array(feature_vector)
            
            return np.array([])
            
        except Exception as e:
            self.logger.error(f"Error creating feature vector: {e}")
            return np.array([])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get feature extraction statistics.
        
        Returns:
            dict: Statistics
        """
        return {
            'sample_rate': self.sample_rate,
            'config': {
                'n_fft': self.config.n_fft,
                'hop_length': self.config.hop_length,
                'n_mels': self.config.n_mels,
                'n_mfcc': self.config.n_mfcc,
                'fmin': self.config.fmin,
                'fmax': self.config.fmax
            },
            'stats': self.stats.copy()
        }


# Example usage and testing
if __name__ == "__main__":
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    def test_feature_extractor():
        """Test feature extractor functionality."""
        # Create test signal
        sample_rate = 8000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create test signal with heart and lung sound components
        signal = (
            0.5 * np.sin(2 * np.pi * 100 * t) +  # Heart sound component
            0.3 * np.sin(2 * np.pi * 300 * t) +  # Lung sound component
            0.2 * np.sin(2 * np.pi * 800 * t) +  # High frequency component
            0.1 * np.random.randn(len(t))        # Noise
        )
        
        # Convert to int16
        test_audio = (signal * 32767).astype(np.int16)
        
        print(f"Test signal - Length: {len(test_audio)}, Sample rate: {sample_rate}Hz")
        
        # Create feature extractor
        config = FeatureConfig(
            n_fft=512,
            hop_length=256,
            n_mels=64,
            n_mfcc=13,
            heart_rate_features=True,
            respiratory_features=True
        )
        
        extractor = AudioFeatureExtractor(sample_rate=sample_rate, config=config)
        
        # Extract features
        features = extractor.extract_features(test_audio)
        
        print(f"Extracted features: {list(features.keys())}")
        
        # Print feature shapes
        for key, value in features.items():
            if isinstance(value, np.ndarray):
                print(f"  {key}: {value.shape}")
            else:
                print(f"  {key}: {value}")
        
        # Get feature vectors
        mfcc_vector = extractor.get_feature_vector(features, 'mfcc')
        mel_vector = extractor.get_feature_vector(features, 'mel')
        combined_vector = extractor.get_feature_vector(features, 'combined')
        
        print(f"Feature vectors:")
        print(f"  MFCC: {mfcc_vector.shape}")
        print(f"  Mel: {mel_vector.shape}")
        print(f"  Combined: {combined_vector.shape}")
        
        # Get statistics
        stats = extractor.get_statistics()
        print(f"Feature extractor statistics: {stats}")
        
        print("Feature extraction test completed")
    
    # Run test
    test_feature_extractor()