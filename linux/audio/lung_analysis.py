#!/usr/bin/env python3
"""
Lung Sound Analysis Module
==========================

Specialized analysis for lung sounds including wheeze detection,
crackle detection, and respiratory rate estimation.
"""

import numpy as np
from scipy import signal
import librosa

class LungSoundAnalyzer:
    def __init__(self, sample_rate=8000):
        self.sample_rate = sample_rate
    
    def analyze_lung_sound(self, audio_data):
        """
        Comprehensive lung sound analysis
        
        Args:
            audio_data: Audio signal
            
        Returns:
            dict: Analysis results
        """
        results = {}
        
        # Detect wheezes
        results['wheeze_detection'] = self.detect_wheeze(audio_data)
        
        # Detect crackles
        results['crackle_detection'] = self.detect_crackles(audio_data)
        
        # Estimate respiratory rate
        results['respiratory_rate'] = self.estimate_respiratory_rate(audio_data)
        
        # Calculate quality metrics
        results['quality_metrics'] = self.calculate_quality_metrics(audio_data)
        
        return results
    
    def detect_wheeze(self, audio_data):
        """
        Detect wheeze patterns in lung sounds
        
        Wheezes are continuous, musical sounds typically >100ms duration
        """
        # Compute spectrogram
        f, t, Sxx = signal.spectrogram(
            audio_data,
            fs=self.sample_rate,
            window='hann',
            nperseg=1024,
            noverlap=512
        )
        
        # Focus on wheeze frequency range (100-1000 Hz)
        wheeze_freq_mask = (f >= 100) & (f <= 1000)
        wheeze_spec = Sxx[wheeze_freq_mask, :]
        
        # Calculate spectral persistence (wheezes are sustained)
        persistence = np.mean(wheeze_spec > np.percentile(wheeze_spec, 75), axis=1)
        
        # Find dominant frequency
        max_persistence_idx = np.argmax(persistence)
        dominant_freq = f[wheeze_freq_mask][max_persistence_idx]
        
        # Wheeze score
        wheeze_score = np.max(persistence)
        
        # Detect monophonic vs polyphonic wheeze
        # Monophonic: single frequency, Polyphonic: multiple frequencies
        num_peaks = len(signal.find_peaks(persistence, height=0.5)[0])
        wheeze_type = 'polyphonic' if num_peaks > 1 else 'monophonic'
        
        return {
            'wheeze_detected': bool(wheeze_score > 0.4),
            'wheeze_score': float(wheeze_score),
            'dominant_frequency': float(dominant_freq),
            'wheeze_type': wheeze_type,
            'num_wheeze_components': int(num_peaks)
        }
    
    def detect_crackles(self, audio_data):
        """
        Detect crackle patterns in lung sounds
        
        Crackles are short, explosive sounds (<20ms duration)
        """
        # Compute short-time energy
        window_size = int(0.01 * self.sample_rate)  # 10ms windows
        hop_size = window_size // 2
        
        energy = []
        for i in range(0, len(audio_data) - window_size, hop_size):
            window = audio_data[i:i + window_size]
            energy.append(np.sum(window ** 2))
        
        energy = np.array(energy)
        
        # Find sudden energy spikes (crackles)
        energy_diff = np.diff(energy)
        threshold = np.mean(energy_diff) + 3 * np.std(energy_diff)
        
        crackle_events = energy_diff > threshold
        crackle_count = np.sum(crackle_events)
        
        # Calculate crackle rate (per second)
        duration = len(audio_data) / self.sample_rate
        crackle_rate = crackle_count / duration
        
        # Classify as fine or coarse crackles based on duration
        # Fine crackles: <5ms, Coarse crackles: 5-15ms
        crackle_type = 'fine' if window_size < 0.005 * self.sample_rate else 'coarse'
        
        return {
            'crackles_detected': bool(crackle_count > 0),
            'crackle_count': int(crackle_count),
            'crackle_rate': float(crackle_rate),
            'crackle_type': crackle_type
        }
    
    def estimate_respiratory_rate(self, audio_data):
        """Estimate respiratory rate from lung sounds"""
        # Apply bandpass filter for breath sounds
        sos = signal.butter(4, [100, 500], btype='band', fs=self.sample_rate, output='sos')
        filtered = signal.sosfilt(sos, audio_data)
        
        # Compute envelope
        analytic_signal = signal.hilbert(filtered)
        envelope = np.abs(analytic_signal)
        
        # Smooth envelope
        window_size = int(0.1 * self.sample_rate)
        envelope_smooth = signal.savgol_filter(envelope, window_size, 3)
        
        # Find peaks (breaths)
        min_distance = int(60 / 30 * self.sample_rate)  # Max 30 breaths/min
        peaks, _ = signal.find_peaks(
            envelope_smooth,
            height=np.max(envelope_smooth) * 0.2,
            distance=min_distance
        )
        
        if len(peaks) < 2:
            return None
        
        # Calculate intervals
        intervals = np.diff(peaks) / self.sample_rate
        valid_intervals = intervals[(intervals >= 60/30) & (intervals <= 60/8)]
        
        if len(valid_intervals) == 0:
            return None
        
        # Calculate breaths per minute
        avg_interval = np.mean(valid_intervals)
        breaths_per_min = 60 / avg_interval
        
        return {
            'breaths_per_minute': float(breaths_per_min),
            'confidence': float(len(valid_intervals) / len(intervals)),
            'num_breaths': len(peaks)
        }
    
    def calculate_quality_metrics(self, audio_data):
        """Calculate audio quality metrics"""
        # Signal-to-noise ratio
        signal_power = np.mean(audio_data ** 2)
        noise_estimate = np.percentile(np.abs(audio_data), 10) ** 2
        snr = 10 * np.log10(signal_power / (noise_estimate + 1e-8))
        
        # Spectral flatness (measure of noise vs tonal content)
        spec = np.abs(np.fft.fft(audio_data))
        geometric_mean = np.exp(np.mean(np.log(spec + 1e-8)))
        arithmetic_mean = np.mean(spec)
        spectral_flatness = geometric_mean / (arithmetic_mean + 1e-8)
        
        return {
            'snr_db': float(snr),
            'spectral_flatness': float(spectral_flatness),
            'rms_level': float(np.sqrt(np.mean(audio_data ** 2)))
        }
