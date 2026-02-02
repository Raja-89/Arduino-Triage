#!/usr/bin/env python3
"""
Heart Sound Analysis Module
===========================

Specialized analysis for heart sounds including S1/S2 detection,
murmur detection, and heart rate estimation.
"""

import numpy as np
from scipy import signal
import librosa

class HeartSoundAnalyzer:
    def __init__(self, sample_rate=8000):
        self.sample_rate = sample_rate
    
    def analyze_heart_sound(self, audio_data):
        """
        Comprehensive heart sound analysis
        
        Args:
            audio_data: Audio signal
            
        Returns:
            dict: Analysis results
        """
        results = {}
        
        # Estimate heart rate
        results['heart_rate'] = self.estimate_heart_rate(audio_data)
        
        # Detect S1 and S2 sounds
        results['s1_s2_detection'] = self.detect_s1_s2(audio_data)
        
        # Analyze for murmurs
        results['murmur_analysis'] = self.analyze_murmur(audio_data)
        
        # Calculate heart sound quality metrics
        results['quality_metrics'] = self.calculate_quality_metrics(audio_data)
        
        return results
    
    def estimate_heart_rate(self, audio_data):
        """Estimate heart rate from audio"""
        # Compute envelope
        analytic_signal = signal.hilbert(audio_data)
        envelope = np.abs(analytic_signal)
        
        # Smooth envelope
        window_size = int(0.05 * self.sample_rate)
        envelope_smooth = signal.savgol_filter(envelope, window_size, 3)
        
        # Find peaks
        min_distance = int(60 / 200 * self.sample_rate)  # Max 200 BPM
        peaks, _ = signal.find_peaks(
            envelope_smooth,
            height=np.max(envelope_smooth) * 0.3,
            distance=min_distance
        )
        
        if len(peaks) < 2:
            return None
        
        # Calculate intervals
        intervals = np.diff(peaks) / self.sample_rate
        valid_intervals = intervals[(intervals >= 60/200) & (intervals <= 60/40)]
        
        if len(valid_intervals) == 0:
            return None
        
        # Calculate BPM
        avg_interval = np.mean(valid_intervals)
        bpm = 60 / avg_interval
        
        return {
            'bpm': float(bpm),
            'confidence': float(len(valid_intervals) / len(intervals)),
            'num_beats': len(peaks)
        }
    
    def detect_s1_s2(self, audio_data):
        """Detect S1 and S2 heart sounds"""
        # S1 is typically lower frequency (20-60 Hz)
        # S2 is typically higher frequency (60-100 Hz)
        
        # Filter for S1
        sos_s1 = signal.butter(4, [20, 60], btype='band', fs=self.sample_rate, output='sos')
        s1_filtered = signal.sosfilt(sos_s1, audio_data)
        
        # Filter for S2
        sos_s2 = signal.butter(4, [60, 100], btype='band', fs=self.sample_rate, output='sos')
        s2_filtered = signal.sosfilt(sos_s2, audio_data)
        
        # Calculate energy ratio
        s1_energy = np.sum(s1_filtered ** 2)
        s2_energy = np.sum(s2_filtered ** 2)
        
        return {
            's1_energy': float(s1_energy),
            's2_energy': float(s2_energy),
            's1_s2_ratio': float(s1_energy / (s2_energy + 1e-8))
        }
    
    def analyze_murmur(self, audio_data):
        """Analyze for presence of heart murmurs"""
        # Murmurs are typically sustained sounds between S1 and S2
        # Look for sustained energy in systolic/diastolic periods
        
        # Compute spectrogram
        f, t, Sxx = signal.spectrogram(
            audio_data,
            fs=self.sample_rate,
            window='hann',
            nperseg=1024,
            noverlap=512
        )
        
        # Focus on murmur frequency range (100-400 Hz)
        murmur_freq_mask = (f >= 100) & (f <= 400)
        murmur_spec = Sxx[murmur_freq_mask, :]
        
        # Calculate temporal persistence
        persistence = np.mean(murmur_spec > np.percentile(murmur_spec, 75), axis=0)
        
        # Murmur score based on sustained energy
        murmur_score = np.mean(persistence)
        
        return {
            'murmur_score': float(murmur_score),
            'murmur_detected': bool(murmur_score > 0.3)
        }
    
    def calculate_quality_metrics(self, audio_data):
        """Calculate audio quality metrics"""
        # Signal-to-noise ratio estimate
        signal_power = np.mean(audio_data ** 2)
        noise_estimate = np.percentile(np.abs(audio_data), 10) ** 2
        snr = 10 * np.log10(signal_power / (noise_estimate + 1e-8))
        
        # Dynamic range
        dynamic_range = 20 * np.log10(np.max(np.abs(audio_data)) / (np.min(np.abs(audio_data[audio_data != 0])) + 1e-8))
        
        return {
            'snr_db': float(snr),
            'dynamic_range_db': float(dynamic_range),
            'rms_level': float(np.sqrt(np.mean(audio_data ** 2)))
        }
