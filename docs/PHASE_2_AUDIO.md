# 🎵 PHASE 2: Audio Pipeline & Preprocessing

**Objective**: Establish robust audio capture, preprocessing, and feature extraction pipeline for heart and lung sound analysis.

## 🎯 Phase 2 Goals

By the end of this phase, you must have:
- ✅ Contact microphone integrated and calibrated
- ✅ Real-time audio capture working on Linux side
- ✅ Signal processing pipeline implemented (filtering, noise reduction)
- ✅ Feature extraction working (spectrograms, MFCCs)
- ✅ Heart rate estimation from audio
- ✅ Device calibration system functional
- ✅ Audio visualization for debugging and demo

**⚠️ Prerequisites**: Phase 1 must be 100% complete before starting this phase.

## 🎤 Audio Hardware Setup

### Required Components
- **MAX9814 Electret Microphone Module** (with AGC and amplifier)
- **3.5mm Audio Jack** (for stethoscope connection)
- **Audio Cable** (3.5mm to connect stethoscope)
- **Optional**: USB Audio Interface for better quality

### Microphone Module Specifications
- **Frequency Response**: 20Hz - 20kHz
- **Supply Voltage**: 2.7V - 5.5V
- **Gain**: Adjustable (40dB, 50dB, 60dB)
- **Output**: Analog audio signal
- **AGC**: Automatic Gain Control built-in

## 🔌 Audio Hardware Integration

### Option 1: Direct Analog Connection
```
MAX9814 Module → Arduino UNO Q Analog Input
VCC → 3.3V
GND → GND
OUT → A1 (or available analog pin)
GAIN → 3.3V (for maximum gain)
```

### Option 2: USB Audio Interface (Recommended)
```
MAX9814 Module → 3.5mm Jack → USB Audio Interface → UNO Q USB Port
```

**Advantages of USB Audio**:
- Higher sample rates (up to 48kHz)
- Better noise isolation
- Standard Linux audio drivers
- Easier software integration

## 🔧 Linux Audio System Setup

### Step 2.1: Audio System Configuration

#### Install Required Packages
```bash
# SSH into Arduino UNO Q
ssh root@192.168.7.2

# Update package list
apt update

# Install audio tools and libraries
apt install -y alsa-utils pulseaudio python3-pyaudio python3-sounddevice
apt install -y python3-scipy python3-numpy python3-matplotlib
apt install -y python3-librosa  # For advanced audio processing
```

#### Test Audio Input
```bash
# List audio devices
arecord -l

# Test recording (5 seconds)
arecord -D hw:1,0 -f cd -t wav -d 5 test_recording.wav

# Play back recording
aplay test_recording.wav

# Check recording properties
file test_recording.wav
```

### Step 2.2: Python Audio Capture System

Create file: `linux/audio/capture.py`
```python
import sounddevice as sd
import numpy as np
import threading
import queue
import time
from scipy import signal
import json

class AudioCapture:
    def __init__(self, sample_rate=8000, channels=1, device=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.callback_thread = None
        
        # Audio buffer for continuous processing
        self.buffer_size = int(sample_rate * 2)  # 2 seconds buffer
        self.audio_buffer = np.zeros(self.buffer_size)
        
    def list_devices(self):
        """List available audio input devices"""
        devices = sd.query_devices()
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        
        return input_devices
    
    def audio_callback(self, indata, frames, time, status):
        """Callback function for audio stream"""
        if status:
            print(f"Audio callback status: {status}")
        
        # Add new audio data to queue
        audio_data = indata[:, 0] if self.channels == 1 else indata
        self.audio_queue.put(audio_data.copy())
        
        # Update rolling buffer
        self.audio_buffer = np.roll(self.audio_buffer, -len(audio_data))
        self.audio_buffer[-len(audio_data):] = audio_data
    
    def start_stream(self):
        """Start continuous audio capture"""
        try:
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                blocksize=1024
            )
            self.stream.start()
            self.is_recording = True
            print(f"Audio stream started: {self.sample_rate}Hz, {self.channels} channel(s)")
            return True
            
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            return False
    
    def stop_stream(self):
        """Stop audio capture"""
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
            self.is_recording = False
            print("Audio stream stopped")
    
    def capture_segment(self, duration=8.0):
        """Capture a specific duration of audio"""
        if not self.is_recording:
            print("Audio stream not running")
            return None
        
        samples_needed = int(duration * self.sample_rate)
        audio_segment = np.zeros(samples_needed)
        samples_collected = 0
        
        start_time = time.time()
        
        while samples_collected < samples_needed:
            try:
                # Get audio data from queue (timeout after 1 second)
                chunk = self.audio_queue.get(timeout=1.0)
                
                # Add chunk to segment
                chunk_size = min(len(chunk), samples_needed - samples_collected)
                audio_segment[samples_collected:samples_collected + chunk_size] = chunk[:chunk_size]
                samples_collected += chunk_size
                
            except queue.Empty:
                print("Audio capture timeout")
                break
        
        capture_time = time.time() - start_time
        print(f"Captured {samples_collected} samples in {capture_time:.2f}s")
        
        return audio_segment[:samples_collected]
    
    def get_current_buffer(self):
        """Get current audio buffer for real-time analysis"""
        return self.audio_buffer.copy()

# Test the audio capture system
if __name__ == "__main__":
    capture = AudioCapture()
    
    # List available devices
    devices = capture.list_devices()
    print("Available audio input devices:")
    for device in devices:
        print(f"  {device['id']}: {device['name']}")
    
    # Start capture
    if capture.start_stream():
        print("Recording for 10 seconds...")
        time.sleep(2)  # Let stream stabilize
        
        # Capture a segment
        audio_data = capture.capture_segment(duration=5.0)
        
        if audio_data is not None:
            print(f"Captured audio: {len(audio_data)} samples")
            print(f"Audio level: {np.max(np.abs(audio_data)):.3f}")
            
            # Save for testing
            import scipy.io.wavfile as wav
            wav.write('test_capture.wav', capture.sample_rate, 
                     (audio_data * 32767).astype(np.int16))
            print("Saved as test_capture.wav")
        
        capture.stop_stream()
```

## 🔄 Signal Processing Pipeline

### Step 2.3: Audio Preprocessing

Create file: `linux/audio/preprocessing.py`
```python
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
import librosa

class AudioPreprocessor:
    def __init__(self, sample_rate=8000):
        self.sample_rate = sample_rate
        
        # Design filters
        self.heart_filter = self._design_heart_filter()
        self.lung_filter = self._design_lung_filter()
        self.notch_filter = self._design_notch_filter()
    
    def _design_heart_filter(self):
        """Design bandpass filter for heart sounds (20-400 Hz)"""
        nyquist = self.sample_rate / 2
        low = 20 / nyquist
        high = 400 / nyquist
        
        # 4th order Butterworth bandpass filter
        sos = signal.butter(4, [low, high], btype='band', output='sos')
        return sos
    
    def _design_lung_filter(self):
        """Design bandpass filter for lung sounds (100-2000 Hz)"""
        nyquist = self.sample_rate / 2
        low = 100 / nyquist
        high = min(2000 / nyquist, 0.95)  # Ensure below Nyquist
        
        sos = signal.butter(4, [low, high], btype='band', output='sos')
        return sos
    
    def _design_notch_filter(self):
        """Design notch filter for 50Hz mains hum"""
        nyquist = self.sample_rate / 2
        freq = 50 / nyquist
        quality = 30  # Q factor
        
        if freq < 0.95:  # Only if frequency is valid
            b, a = signal.iirnotch(freq, quality)
            return (b, a)
        return None
    
    def preprocess_heart(self, audio_data):
        """Preprocess audio for heart sound analysis"""
        # Apply notch filter for mains hum
        if self.notch_filter:
            audio_data = signal.filtfilt(self.notch_filter[0], 
                                       self.notch_filter[1], audio_data)
        
        # Apply heart-specific bandpass filter
        filtered = signal.sosfilt(self.heart_filter, audio_data)
        
        # Normalize amplitude
        if np.max(np.abs(filtered)) > 0:
            filtered = filtered / np.max(np.abs(filtered))
        
        return filtered
    
    def preprocess_lung(self, audio_data):
        """Preprocess audio for lung sound analysis"""
        # Apply notch filter
        if self.notch_filter:
            audio_data = signal.filtfilt(self.notch_filter[0], 
                                       self.notch_filter[1], audio_data)
        
        # Apply lung-specific bandpass filter
        filtered = signal.sosfilt(self.lung_filter, audio_data)
        
        # Normalize amplitude
        if np.max(np.abs(filtered)) > 0:
            filtered = filtered / np.max(np.abs(filtered))
        
        return filtered
    
    def remove_noise(self, audio_data, noise_reduction=0.1):
        """Simple noise reduction using spectral subtraction"""
        # Compute FFT
        fft_data = fft(audio_data)
        freqs = fftfreq(len(audio_data), 1/self.sample_rate)
        
        # Estimate noise floor (bottom 10% of spectrum)
        magnitude = np.abs(fft_data)
        noise_floor = np.percentile(magnitude, 10)
        
        # Reduce noise
        magnitude_clean = np.maximum(magnitude - noise_reduction * noise_floor, 
                                   0.1 * magnitude)
        
        # Reconstruct signal
        phase = np.angle(fft_data)
        fft_clean = magnitude_clean * np.exp(1j * phase)
        
        return np.real(np.fft.ifft(fft_clean))
    
    def detect_silence(self, audio_data, threshold=0.01, min_duration=0.5):
        """Detect silent periods in audio"""
        # Calculate RMS energy in windows
        window_size = int(0.1 * self.sample_rate)  # 100ms windows
        hop_size = window_size // 2
        
        energy = []
        for i in range(0, len(audio_data) - window_size, hop_size):
            window = audio_data[i:i + window_size]
            rms = np.sqrt(np.mean(window**2))
            energy.append(rms)
        
        # Find silent regions
        silent_windows = np.array(energy) < threshold
        
        return silent_windows, energy

# Test preprocessing
if __name__ == "__main__":
    import scipy.io.wavfile as wav
    
    # Load test audio
    try:
        sample_rate, audio_data = wav.read('test_capture.wav')
        audio_data = audio_data.astype(np.float32) / 32767.0
        
        preprocessor = AudioPreprocessor(sample_rate)
        
        # Test heart preprocessing
        heart_filtered = preprocessor.preprocess_heart(audio_data)
        wav.write('heart_filtered.wav', sample_rate, 
                 (heart_filtered * 32767).astype(np.int16))
        
        # Test lung preprocessing
        lung_filtered = preprocessor.preprocess_lung(audio_data)
        wav.write('lung_filtered.wav', sample_rate, 
                 (lung_filtered * 32767).astype(np.int16))
        
        print("Preprocessing test completed")
        print(f"Original RMS: {np.sqrt(np.mean(audio_data**2)):.4f}")
        print(f"Heart filtered RMS: {np.sqrt(np.mean(heart_filtered**2)):.4f}")
        print(f"Lung filtered RMS: {np.sqrt(np.mean(lung_filtered**2)):.4f}")
        
    except FileNotFoundError:
        print("No test audio file found. Run capture.py first.")
```

## 📊 Feature Extraction

### Step 2.4: Feature Extraction Pipeline

Create file: `linux/audio/features.py`
```python
import numpy as np
import librosa
from scipy import signal
import matplotlib.pyplot as plt

class FeatureExtractor:
    def __init__(self, sample_rate=8000):
        self.sample_rate = sample_rate
    
    def extract_mel_spectrogram(self, audio_data, n_mels=64, n_fft=1024, 
                               hop_length=512, fmax=None):
        """Extract mel-spectrogram features"""
        if fmax is None:
            fmax = self.sample_rate // 2
        
        # Compute mel-spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=audio_data,
            sr=self.sample_rate,
            n_mels=n_mels,
            n_fft=n_fft,
            hop_length=hop_length,
            fmax=fmax
        )
        
        # Convert to log scale
        log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
        
        return log_mel_spec
    
    def extract_mfcc(self, audio_data, n_mfcc=13):
        """Extract MFCC features"""
        mfccs = librosa.feature.mfcc(
            y=audio_data,
            sr=self.sample_rate,
            n_mfcc=n_mfcc
        )
        
        return mfccs
    
    def extract_spectral_features(self, audio_data):
        """Extract various spectral features"""
        features = {}
        
        # Spectral centroid
        features['spectral_centroid'] = librosa.feature.spectral_centroid(
            y=audio_data, sr=self.sample_rate)[0]
        
        # Spectral rolloff
        features['spectral_rolloff'] = librosa.feature.spectral_rolloff(
            y=audio_data, sr=self.sample_rate)[0]
        
        # Zero crossing rate
        features['zcr'] = librosa.feature.zero_crossing_rate(audio_data)[0]
        
        # RMS energy
        features['rms'] = librosa.feature.rms(y=audio_data)[0]
        
        return features
    
    def estimate_heart_rate(self, audio_data, min_bpm=40, max_bpm=200):
        """Estimate heart rate from audio signal"""
        # Compute envelope using Hilbert transform
        analytic_signal = signal.hilbert(audio_data)
        envelope = np.abs(analytic_signal)
        
        # Smooth envelope
        window_size = int(0.05 * self.sample_rate)  # 50ms window
        envelope_smooth = signal.savgol_filter(envelope, window_size, 3)
        
        # Find peaks (potential heartbeats)
        min_distance = int(60 / max_bpm * self.sample_rate)  # Minimum distance between beats
        peaks, properties = signal.find_peaks(
            envelope_smooth,
            height=np.max(envelope_smooth) * 0.3,  # 30% of max height
            distance=min_distance
        )
        
        if len(peaks) < 2:
            return None, envelope_smooth, peaks
        
        # Calculate intervals between peaks
        intervals = np.diff(peaks) / self.sample_rate  # Convert to seconds
        
        # Filter out unrealistic intervals
        valid_intervals = intervals[
            (intervals >= 60/max_bpm) & (intervals <= 60/min_bpm)
        ]
        
        if len(valid_intervals) == 0:
            return None, envelope_smooth, peaks
        
        # Calculate BPM
        avg_interval = np.mean(valid_intervals)
        bpm = 60 / avg_interval
        
        return bpm, envelope_smooth, peaks
    
    def extract_heart_features(self, audio_data):
        """Extract features specific to heart sound analysis"""
        features = {}
        
        # Basic spectral features
        features.update(self.extract_spectral_features(audio_data))
        
        # Mel-spectrogram (optimized for heart sounds)
        features['mel_spectrogram'] = self.extract_mel_spectrogram(
            audio_data, n_mels=64, fmax=400
        )
        
        # Heart rate estimation
        bpm, envelope, peaks = self.estimate_heart_rate(audio_data)
        features['heart_rate'] = bpm
        features['envelope'] = envelope
        features['heart_peaks'] = peaks
        
        # Frequency domain analysis
        fft_data = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
        magnitude = np.abs(fft_data)
        
        # Find dominant frequencies
        positive_freqs = freqs[:len(freqs)//2]
        positive_magnitude = magnitude[:len(magnitude)//2]
        
        # Focus on heart sound frequency range (20-400 Hz)
        heart_freq_mask = (positive_freqs >= 20) & (positive_freqs <= 400)
        heart_freqs = positive_freqs[heart_freq_mask]
        heart_magnitude = positive_magnitude[heart_freq_mask]
        
        if len(heart_magnitude) > 0:
            dominant_freq_idx = np.argmax(heart_magnitude)
            features['dominant_frequency'] = heart_freqs[dominant_freq_idx]
            features['dominant_magnitude'] = heart_magnitude[dominant_freq_idx]
        
        return features
    
    def extract_lung_features(self, audio_data):
        """Extract features specific to lung sound analysis"""
        features = {}
        
        # Basic spectral features
        features.update(self.extract_spectral_features(audio_data))
        
        # Mel-spectrogram (optimized for lung sounds)
        features['mel_spectrogram'] = self.extract_mel_spectrogram(
            audio_data, n_mels=64, fmax=2000
        )
        
        # Wheeze detection (look for tonal components)
        features.update(self._detect_wheeze(audio_data))
        
        # Crackle detection (look for transient events)
        features.update(self._detect_crackles(audio_data))
        
        return features
    
    def _detect_wheeze(self, audio_data):
        """Detect wheeze patterns in lung sounds"""
        # Compute spectrogram
        f, t, Sxx = signal.spectrogram(
            audio_data, 
            fs=self.sample_rate,
            window='hann',
            nperseg=1024,
            noverlap=512
        )
        
        # Look for sustained tonal components (wheeze characteristics)
        # Wheeze typically appears as horizontal lines in spectrogram
        wheeze_features = {}
        
        # Focus on wheeze frequency range (100-1000 Hz)
        wheeze_freq_mask = (f >= 100) & (f <= 1000)
        wheeze_spec = Sxx[wheeze_freq_mask, :]
        
        # Calculate spectral persistence (how long frequencies persist)
        persistence = np.mean(wheeze_spec > np.percentile(wheeze_spec, 75), axis=1)
        
        wheeze_features['wheeze_score'] = np.max(persistence)
        wheeze_features['wheeze_frequency'] = f[wheeze_freq_mask][np.argmax(persistence)]
        
        return wheeze_features
    
    def _detect_crackles(self, audio_data):
        """Detect crackle patterns in lung sounds"""
        crackle_features = {}
        
        # Crackles are short, explosive sounds
        # Look for sudden energy increases
        
        # Compute short-time energy
        window_size = int(0.01 * self.sample_rate)  # 10ms windows
        hop_size = window_size // 2
        
        energy = []
        for i in range(0, len(audio_data) - window_size, hop_size):
            window = audio_data[i:i + window_size]
            energy.append(np.sum(window**2))
        
        energy = np.array(energy)
        
        # Find sudden energy spikes
        energy_diff = np.diff(energy)
        threshold = np.mean(energy_diff) + 3 * np.std(energy_diff)
        
        crackle_events = energy_diff > threshold
        crackle_features['crackle_count'] = np.sum(crackle_events)
        crackle_features['crackle_rate'] = np.sum(crackle_events) / (len(audio_data) / self.sample_rate)
        
        return crackle_features

# Test feature extraction
if __name__ == "__main__":
    import scipy.io.wavfile as wav
    
    try:
        # Load test audio
        sample_rate, audio_data = wav.read('test_capture.wav')
        audio_data = audio_data.astype(np.float32) / 32767.0
        
        extractor = FeatureExtractor(sample_rate)
        
        # Extract heart features
        heart_features = extractor.extract_heart_features(audio_data)
        print("Heart Features:")
        for key, value in heart_features.items():
            if isinstance(value, np.ndarray) and value.ndim > 1:
                print(f"  {key}: shape {value.shape}")
            elif isinstance(value, np.ndarray):
                print(f"  {key}: {len(value)} values")
            else:
                print(f"  {key}: {value}")
        
        # Extract lung features
        lung_features = extractor.extract_lung_features(audio_data)
        print("\nLung Features:")
        for key, value in lung_features.items():
            if isinstance(value, np.ndarray) and value.ndim > 1:
                print(f"  {key}: shape {value.shape}")
            elif isinstance(value, np.ndarray):
                print(f"  {key}: {len(value)} values")
            else:
                print(f"  {key}: {value}")
                
    except FileNotFoundError:
        print("No test audio file found. Run capture.py first.")
```

## 🎛️ Device Calibration System

### Step 2.5: Device Calibration

Create file: `linux/audio/calibration.py`
```python
import numpy as np
from scipy import signal
import json
import os

class DeviceCalibrator:
    def __init__(self, sample_rate=8000):
        self.sample_rate = sample_rate
        self.calibration_profile = None
        self.calibration_file = 'device_calibration.json'
    
    def calibrate_device(self, reference_audio, test_audio):
        """
        Calibrate device using reference and test recordings
        
        Args:
            reference_audio: Known reference signal
            test_audio: Signal recorded through the device
        """
        print("Starting device calibration...")
        
        # Ensure signals are same length
        min_length = min(len(reference_audio), len(test_audio))
        reference_audio = reference_audio[:min_length]
        test_audio = test_audio[:min_length]
        
        # Compute frequency response
        freq_response = self._compute_frequency_response(reference_audio, test_audio)
        
        # Compute gain correction
        gain_correction = self._compute_gain_correction(reference_audio, test_audio)
        
        # Compute noise characteristics
        noise_profile = self._compute_noise_profile(test_audio)
        
        # Create calibration profile
        self.calibration_profile = {
            'frequency_response': freq_response.tolist(),
            'gain_correction': float(gain_correction),
            'noise_profile': noise_profile,
            'sample_rate': self.sample_rate,
            'calibration_timestamp': str(np.datetime64('now'))
        }
        
        # Save calibration
        self.save_calibration()
        
        print("Device calibration completed")
        return self.calibration_profile
    
    def _compute_frequency_response(self, reference, test):
        """Compute device frequency response"""
        # Compute FFTs
        ref_fft = np.fft.fft(reference)
        test_fft = np.fft.fft(test)
        
        # Compute transfer function
        # H(f) = Test(f) / Reference(f)
        transfer_function = test_fft / (ref_fft + 1e-10)  # Avoid division by zero
        
        # Take magnitude and smooth
        magnitude_response = np.abs(transfer_function)
        
        # Smooth the response
        window_size = len(magnitude_response) // 50
        if window_size > 1:
            magnitude_response = signal.savgol_filter(
                magnitude_response, window_size, 3
            )
        
        return magnitude_response
    
    def _compute_gain_correction(self, reference, test):
        """Compute overall gain correction factor"""
        ref_rms = np.sqrt(np.mean(reference**2))
        test_rms = np.sqrt(np.mean(test**2))
        
        if test_rms > 0:
            gain_correction = ref_rms / test_rms
        else:
            gain_correction = 1.0
        
        return gain_correction
    
    def _compute_noise_profile(self, audio):
        """Compute noise characteristics"""
        # Find quiet segments (bottom 20% of energy)
        window_size = int(0.1 * self.sample_rate)  # 100ms windows
        hop_size = window_size // 2
        
        energies = []
        for i in range(0, len(audio) - window_size, hop_size):
            window = audio[i:i + window_size]
            energy = np.mean(window**2)
            energies.append(energy)
        
        energies = np.array(energies)
        noise_threshold = np.percentile(energies, 20)
        
        # Extract noise segments
        noise_segments = []
        for i, energy in enumerate(energies):
            if energy <= noise_threshold:
                start = i * hop_size
                end = start + window_size
                noise_segments.append(audio[start:end])
        
        if noise_segments:
            noise_audio = np.concatenate(noise_segments)
            noise_level = np.sqrt(np.mean(noise_audio**2))
            noise_spectrum = np.abs(np.fft.fft(noise_audio))
        else:
            noise_level = 0.0
            noise_spectrum = np.zeros(len(audio))
        
        return {
            'noise_level': float(noise_level),
            'noise_spectrum': noise_spectrum[:len(noise_spectrum)//2].tolist()
        }
    
    def apply_calibration(self, audio_data):
        """Apply calibration corrections to audio data"""
        if self.calibration_profile is None:
            return audio_data
        
        corrected_audio = audio_data.copy()
        
        # Apply gain correction
        corrected_audio *= self.calibration_profile['gain_correction']
        
        # Apply frequency response correction (inverse filtering)
        freq_response = np.array(self.calibration_profile['frequency_response'])
        
        if len(freq_response) == len(audio_data):
            # Compute inverse filter
            audio_fft = np.fft.fft(corrected_audio)
            
            # Avoid division by very small numbers
            safe_response = np.maximum(freq_response, 0.1 * np.max(freq_response))
            inverse_response = 1.0 / safe_response
            
            # Apply inverse filter
            corrected_fft = audio_fft * inverse_response
            corrected_audio = np.real(np.fft.ifft(corrected_fft))
        
        return corrected_audio
    
    def save_calibration(self):
        """Save calibration profile to file"""
        if self.calibration_profile:
            with open(self.calibration_file, 'w') as f:
                json.dump(self.calibration_profile, f, indent=2)
            print(f"Calibration saved to {self.calibration_file}")
    
    def load_calibration(self):
        """Load calibration profile from file"""
        if os.path.exists(self.calibration_file):
            with open(self.calibration_file, 'r') as f:
                self.calibration_profile = json.load(f)
            print(f"Calibration loaded from {self.calibration_file}")
            return True
        else:
            print("No calibration file found")
            return False
    
    def quick_calibration(self, audio_capture, duration=10.0):
        """
        Perform quick calibration using ambient noise and known test signal
        """
        print("Starting quick calibration...")
        print("Please ensure microphone is in quiet environment")
        
        # Record ambient noise
        print("Recording ambient noise...")
        noise_audio = audio_capture.capture_segment(duration=2.0)
        
        # Generate test tone
        print("Playing test tone (if available)...")
        test_freq = 440  # A4 note
        t = np.linspace(0, 2.0, int(2.0 * self.sample_rate))
        reference_tone = 0.5 * np.sin(2 * np.pi * test_freq * t)
        
        # For now, use recorded audio as test (in real implementation,
        # you would play the reference tone and record it)
        print("Recording test signal...")
        test_audio = audio_capture.capture_segment(duration=2.0)
        
        if test_audio is not None and len(test_audio) > 0:
            # Simple calibration based on noise level and gain
            noise_level = np.sqrt(np.mean(noise_audio**2)) if noise_audio is not None else 0.01
            signal_level = np.sqrt(np.mean(test_audio**2))
            
            self.calibration_profile = {
                'gain_correction': 1.0,  # Will be refined with actual reference
                'noise_level': float(noise_level),
                'signal_level': float(signal_level),
                'snr_estimate': float(signal_level / (noise_level + 1e-10)),
                'sample_rate': self.sample_rate,
                'calibration_timestamp': str(np.datetime64('now')),
                'calibration_type': 'quick'
            }
            
            self.save_calibration()
            print("Quick calibration completed")
            return True
        else:
            print("Calibration failed - no audio captured")
            return False

# Test calibration system
if __name__ == "__main__":
    from capture import AudioCapture
    
    calibrator = DeviceCalibrator()
    
    # Try to load existing calibration
    if not calibrator.load_calibration():
        # Perform new calibration
        print("No existing calibration found")
        print("Starting audio capture for calibration...")
        
        capture = AudioCapture()
        if capture.start_stream():
            success = calibrator.quick_calibration(capture)
            capture.stop_stream()
            
            if success:
                print("Calibration profile created:")
                print(json.dumps(calibrator.calibration_profile, indent=2))
        else:
            print("Failed to start audio capture")
    else:
        print("Existing calibration loaded:")
        print(json.dumps(calibrator.calibration_profile, indent=2))
```

## 📊 Audio Visualization

### Step 2.6: Real-time Audio Visualization

Create file: `linux/audio/visualization.py`
```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
import base64

class AudioVisualizer:
    def __init__(self, sample_rate=8000, buffer_size=8000):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        # Setup matplotlib for non-interactive backend
        plt.switch_backend('Agg')
        
    def plot_waveform(self, audio_data, title="Audio Waveform"):
        """Plot audio waveform"""
        fig, ax = plt.subplots(figsize=(12, 4))
        
        time_axis = np.linspace(0, len(audio_data) / self.sample_rate, len(audio_data))
        ax.plot(time_axis, audio_data)
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Amplitude')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def plot_spectrogram(self, audio_data, title="Spectrogram", fmax=None):
        """Plot spectrogram"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if fmax is None:
            fmax = self.sample_rate // 2
        
        # Compute spectrogram
        f, t, Sxx = signal.spectrogram(
            audio_data,
            fs=self.sample_rate,
            window='hann',
            nperseg=1024,
            noverlap=512
        )
        
        # Plot
        im = ax.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), shading='gouraud')
        ax.set_ylabel('Frequency (Hz)')
        ax.set_xlabel('Time (seconds)')
        ax.set_title(title)
        ax.set_ylim(0, fmax)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Power (dB)')
        
        return fig
    
    def plot_mel_spectrogram(self, mel_spec, title="Mel Spectrogram"):
        """Plot mel spectrogram"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        im = ax.imshow(mel_spec, aspect='auto', origin='lower', 
                      extent=[0, mel_spec.shape[1], 0, mel_spec.shape[0]])
        ax.set_ylabel('Mel Bins')
        ax.set_xlabel('Time Frames')
        ax.set_title(title)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Power (dB)')
        
        return fig
    
    def plot_heart_analysis(self, audio_data, envelope, peaks, bpm=None):
        """Plot heart sound analysis"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        time_axis = np.linspace(0, len(audio_data) / self.sample_rate, len(audio_data))
        
        # Plot original audio
        ax1.plot(time_axis, audio_data, alpha=0.7, label='Audio')
        ax1.plot(time_axis, envelope, 'r-', linewidth=2, label='Envelope')
        
        # Mark detected peaks
        if len(peaks) > 0:
            peak_times = peaks / self.sample_rate
            ax1.plot(peak_times, envelope[peaks], 'ro', markersize=8, label='Heart Beats')
        
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Amplitude')
        ax1.set_title(f'Heart Sound Analysis (BPM: {bpm:.1f})' if bpm else 'Heart Sound Analysis')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot frequency spectrum
        fft_data = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
        magnitude = np.abs(fft_data)
        
        # Plot only positive frequencies up to 400 Hz (heart range)
        positive_freqs = freqs[:len(freqs)//2]
        positive_magnitude = magnitude[:len(magnitude)//2]
        heart_mask = positive_freqs <= 400
        
        ax2.plot(positive_freqs[heart_mask], positive_magnitude[heart_mask])
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Magnitude')
        ax2.set_title('Frequency Spectrum (Heart Range)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_lung_analysis(self, audio_data, wheeze_score=None, crackle_count=None):
        """Plot lung sound analysis"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Plot spectrogram
        f, t, Sxx = signal.spectrogram(
            audio_data,
            fs=self.sample_rate,
            window='hann',
            nperseg=1024,
            noverlap=512
        )
        
        im = ax1.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), shading='gouraud')
        ax1.set_ylabel('Frequency (Hz)')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_title('Lung Sound Spectrogram')
        ax1.set_ylim(0, 2000)  # Focus on lung sound range
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax1)
        cbar.set_label('Power (dB)')
        
        # Plot frequency spectrum
        fft_data = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
        magnitude = np.abs(fft_data)
        
        positive_freqs = freqs[:len(freqs)//2]
        positive_magnitude = magnitude[:len(magnitude)//2]
        lung_mask = positive_freqs <= 2000
        
        ax2.plot(positive_freqs[lung_mask], positive_magnitude[lung_mask])
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Magnitude')
        
        title = 'Frequency Spectrum (Lung Range)'
        if wheeze_score is not None:
            title += f' - Wheeze Score: {wheeze_score:.3f}'
        if crackle_count is not None:
            title += f' - Crackles: {crackle_count}'
        
        ax2.set_title(title)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string for web display"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)  # Free memory
        
        return image_base64
    
    def create_dashboard_plots(self, audio_data, features, mode='heart'):
        """Create comprehensive dashboard plots"""
        plots = {}
        
        # Waveform plot
        fig_waveform = self.plot_waveform(audio_data, f"{mode.title()} Sound Waveform")
        plots['waveform'] = self.fig_to_base64(fig_waveform)
        
        # Spectrogram
        fmax = 400 if mode == 'heart' else 2000
        fig_spec = self.plot_spectrogram(audio_data, f"{mode.title()} Sound Spectrogram", fmax)
        plots['spectrogram'] = self.fig_to_base64(fig_spec)
        
        # Mode-specific analysis
        if mode == 'heart' and 'envelope' in features:
            fig_heart = self.plot_heart_analysis(
                audio_data, 
                features['envelope'], 
                features.get('heart_peaks', []),
                features.get('heart_rate')
            )
            plots['analysis'] = self.fig_to_base64(fig_heart)
        
        elif mode == 'lung':
            fig_lung = self.plot_lung_analysis(
                audio_data,
                features.get('wheeze_score'),
                features.get('crackle_count')
            )
            plots['analysis'] = self.fig_to_base64(fig_lung)
        
        # Mel spectrogram if available
        if 'mel_spectrogram' in features:
            fig_mel = self.plot_mel_spectrogram(
                features['mel_spectrogram'], 
                f"{mode.title()} Mel Spectrogram"
            )
            plots['mel_spectrogram'] = self.fig_to_base64(fig_mel)
        
        return plots

# Test visualization
if __name__ == "__main__":
    import scipy.io.wavfile as wav
    from scipy import signal
    from features import FeatureExtractor
    
    try:
        # Load test audio
        sample_rate, audio_data = wav.read('test_capture.wav')
        audio_data = audio_data.astype(np.float32) / 32767.0
        
        # Extract features
        extractor = FeatureExtractor(sample_rate)
        features = extractor.extract_heart_features(audio_data)
        
        # Create visualizations
        visualizer = AudioVisualizer(sample_rate)
        plots = visualizer.create_dashboard_plots(audio_data, features, mode='heart')
        
        print("Generated plots:")
        for plot_name in plots.keys():
            print(f"  - {plot_name}")
        
        # Save one plot as example
        fig = visualizer.plot_waveform(audio_data)
        fig.savefig('example_waveform.png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        print("Example plot saved as example_waveform.png")
        
    except FileNotFoundError:
        print("No test audio file found. Run capture.py first.")
```

## 📋 Phase 2 Completion Checklist

### Audio Hardware
- [ ] Contact microphone connected and working
- [ ] Audio input device detected by Linux
- [ ] Clear audio capture with acceptable signal-to-noise ratio
- [ ] Audio levels properly calibrated

### Software Pipeline
- [ ] Real-time audio capture working
- [ ] Preprocessing filters implemented and tested
- [ ] Feature extraction producing valid outputs
- [ ] Heart rate estimation functional
- [ ] Device calibration system working

### Integration
- [ ] Audio pipeline integrated with main system
- [ ] Real-time processing achieving target latency (<200ms)
- [ ] Visualization system generating plots
- [ ] Error handling and recovery implemented

### Performance
- [ ] Audio quality sufficient for analysis
- [ ] Processing speed meets real-time requirements
- [ ] Memory usage within acceptable limits
- [ ] System stability during continuous operation

## 📁 Phase 2 Deliverables

1. **linux/audio/capture.py** - Audio capture system
2. **linux/audio/preprocessing.py** - Signal processing pipeline
3. **linux/audio/features.py** - Feature extraction
4. **linux/audio/calibration.py** - Device calibration
5. **linux/audio/visualization.py** - Audio visualization
6. **docs/phase2_results.md** - Performance validation report

## 🚀 Next Steps

Once Phase 2 is complete:
1. Validate audio quality and feature extraction
2. Test with various audio sources and conditions
3. Document calibration procedures
4. Proceed to **PHASE 3: ML Training & Model Deployment**

The audio pipeline is the foundation for accurate AI analysis - ensure it's robust before moving forward!

## 🎧 Audio Troubleshooting & Quality Check

### 50Hz/60Hz Mains Hum
- **Problem**: A constant low-frequency hum in your recordings.
- **Cause**: Electrical interference from power lines/walls.
- **Solution**:
  - **Notch Filter**: Ensure the `_design_notch_filter` in `preprocessing.py` is enabled and set to your region's frequency (50Hz usually).
  - **Shielding**: Use shielded audio cables.
  - **Grounding**: Ensure the microphone ground is solid. Touching the metal part of the USB connector can sometimes reduce hum (indicating a grounding issue).

### Low Volume / Poor Sensitivity
- **Problem**: Can barely hear heart sounds.
- **Solution**:
  - **Mic Placement**: The microphone must be in *direct contact* with the skin or chest piece. Air gaps kill sound transfer.
  - **Gain**: On the MAX9814, connect the GAIN pin to VCC (3.3V) for max amplification (60dB).
  - **Pressure**: Apply steady, firm pressure.

### Clipping / Distortion
- **Problem**: Audio sounds "crunchy" or flat-topped waveform.
- **Cause**: Input signal is too loud for the ADC.
- **Solution**:
  - Reduce gain on the microphone module (floating GAIN pin = 50dB, GND = 40dB).
  - Move the microphone slightly away from very loud sources (not applicable for heart sounds usually, but good to know).

### USB Audio Device Not Starting
- **Problem**: `arecord -l` shows no devices or "Device or resource busy".
- **Solution**:
  - **Re-plug**: Unplug and replug the USB card.
  - **Kill Process**: Another process might be using the audio. Run `fuser -v /dev/snd/*` to see what's using it.
  - **Drivers**: Ensure `snd-usb-audio` module is loaded (`lsmod | grep snd`).