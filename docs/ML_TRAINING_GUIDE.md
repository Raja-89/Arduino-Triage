# 🤖 Machine Learning Training Guide

**Complete ML Pipeline for Heart & Lung Sound Classification**

## 🎯 Overview

This guide covers the complete machine learning pipeline for training, optimizing, and deploying TinyML models for heart and lung sound classification on the Arduino UNO Q.

## 📊 Dataset Requirements

### Heart Sound Datasets

**Primary Dataset: PhysioNet/CinC Challenge 2016**
- **Source**: https://physionet.org/content/challenge-2016/
- **Size**: 3,240 heart sound recordings
- **Classes**: Normal, Murmur, Extra Heart Sound, Artifact
- **Duration**: 5-120 seconds per recording
- **Sample Rate**: 2000 Hz (will be resampled to 8000 Hz)
- **Format**: WAV files

**Secondary Dataset: Pascal Challenge 2011**
- **Source**: http://www.peterjbentley.com/heartchallenge/
- **Size**: 176 recordings
- **Classes**: Normal, Murmur, Extrasystole
- **Format**: WAV files

### Lung Sound Datasets

**Primary Dataset: ICBHI 2017 Respiratory Sound Database**
- **Source**: https://bhichallenge.med.auth.gr/
- **Size**: 920 recordings from 126 patients
- **Classes**: Normal, Crackle, Wheeze, Both (Crackle+Wheeze)
- **Duration**: 10-90 seconds
- **Sample Rate**: 4000-44100 Hz (will be resampled)
- **Format**: WAV files

**Secondary Dataset: SPRSound**
- **Source**: Research dataset
- **Additional respiratory sounds for augmentation**

## 🔧 Environment Setup

### Install Dependencies

```bash
# Create virtual environment
python3 -m venv ml_env
source ml_env/bin/activate  # On Windows: ml_env\Scripts\activate

# Install core ML libraries
pip install tensorflow==2.13.0
pip install numpy==1.24.3
pip install scipy==1.10.1
pip install scikit-learn==1.3.0
pip install pandas==2.0.3

# Install audio processing
pip install librosa==0.10.1
pip install soundfile==0.12.1
pip install audiomentations==0.31.0

# Install visualization
pip install matplotlib==3.7.2
pip install seaborn==0.12.2

# Install utilities
pip install tqdm==4.66.1
pip install pyyaml==6.0.1
pip install h5py==3.9.0
```

## 📁 Project Structure for ML

```
ml/
├── datasets/
│   ├── heart/
│   │   ├── raw/              # Original downloaded data
│   │   ├── processed/        # Preprocessed audio
│   │   └── features/         # Extracted features
│   └── lung/
│       ├── raw/
│       ├── processed/
│       └── features/
├── models/
│   ├── heart/
│   │   ├── checkpoints/      # Training checkpoints
│   │   ├── saved_models/     # Full TensorFlow models
│   │   └── tflite/           # Converted TFLite models
│   └── lung/
│       ├── checkpoints/
│       ├── saved_models/
│       └── tflite/
├── scripts/
│   ├── download_datasets.py
│   ├── preprocess_audio.py
│   ├── extract_features.py
│   ├── train_heart_model.py
│   ├── train_lung_model.py
│   ├── evaluate_model.py
│   ├── convert_to_tflite.py
│   └── benchmark_model.py
├── notebooks/
│   ├── data_exploration.ipynb
│   ├── model_experiments.ipynb
│   └── results_analysis.ipynb
├── config/
│   ├── heart_training.yaml
│   └── lung_training.yaml
└── utils/
    ├── audio_utils.py
    ├── data_augmentation.py
    ├── model_utils.py
    └── evaluation_utils.py
```

## 🎵 Audio Preprocessing Pipeline

### Step 1: Download and Organize Datasets

Create `ml/scripts/download_datasets.py`:

```python
import os
import requests
import zipfile
from tqdm import tqdm

def download_physionet_dataset():
    """Download PhysioNet heart sound dataset"""
    url = "https://physionet.org/static/published-projects/challenge-2016/1.0.0/training-a.zip"
    output_dir = "ml/datasets/heart/raw"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Downloading PhysioNet dataset...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    zip_path = os.path.join(output_dir, "physionet.zip")
    
    with open(zip_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
    
    print("Extracting dataset...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    
    os.remove(zip_path)
    print("PhysioNet dataset downloaded and extracted")

def download_icbhi_dataset():
    """Download ICBHI respiratory sound dataset"""
    # Note: ICBHI dataset requires registration
    print("ICBHI dataset requires manual download from:")
    print("https://bhichallenge.med.auth.gr/")
    print("Please download and extract to ml/datasets/lung/raw/")

if __name__ == "__main__":
    download_physionet_dataset()
    download_icbhi_dataset()
```

### Step 2: Audio Preprocessing

Create `ml/scripts/preprocess_audio.py`:

```python
import os
import librosa
import soundfile as sf
import numpy as np
from tqdm import tqdm
from scipy import signal

class AudioPreprocessor:
    def __init__(self, target_sr=8000, target_duration=8.0):
        self.target_sr = target_sr
        self.target_duration = target_duration
        self.target_samples = int(target_sr * target_duration)
    
    def preprocess_heart_sound(self, audio_path, output_path):
        """Preprocess heart sound recording"""
        # Load audio
        audio, sr = librosa.load(audio_path, sr=None)
        
        # Resample to target sample rate
        if sr != self.target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
        
        # Apply bandpass filter (20-400 Hz for heart sounds)
        sos = signal.butter(4, [20, 400], btype='band', fs=self.target_sr, output='sos')
        audio = signal.sosfilt(sos, audio)
        
        # Normalize amplitude
        audio = audio / (np.max(np.abs(audio)) + 1e-8)
        
        # Segment or pad to target duration
        audio = self._segment_audio(audio)
        
        # Save preprocessed audio
        sf.write(output_path, audio, self.target_sr)
        
        return audio
    
    def preprocess_lung_sound(self, audio_path, output_path):
        """Preprocess lung sound recording"""
        # Load audio
        audio, sr = librosa.load(audio_path, sr=None)
        
        # Resample
        if sr != self.target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
        
        # Apply bandpass filter (100-2000 Hz for lung sounds)
        sos = signal.butter(4, [100, 2000], btype='band', fs=self.target_sr, output='sos')
        audio = signal.sosfilt(sos, audio)
        
        # Normalize
        audio = audio / (np.max(np.abs(audio)) + 1e-8)
        
        # Segment or pad
        audio = self._segment_audio(audio)
        
        # Save
        sf.write(output_path, audio, self.target_sr)
        
        return audio
    
    def _segment_audio(self, audio):
        """Segment or pad audio to target length"""
        if len(audio) > self.target_samples:
            # Take middle segment
            start = (len(audio) - self.target_samples) // 2
            audio = audio[start:start + self.target_samples]
        elif len(audio) < self.target_samples:
            # Pad with zeros
            pad_length = self.target_samples - len(audio)
            audio = np.pad(audio, (0, pad_length), mode='constant')
        
        return audio

def preprocess_dataset(input_dir, output_dir, sound_type='heart'):
    """Preprocess entire dataset"""
    preprocessor = AudioPreprocessor()
    
    os.makedirs(output_dir, exist_ok=True)
    
    audio_files = [f for f in os.listdir(input_dir) if f.endswith('.wav')]
    
    for audio_file in tqdm(audio_files, desc=f"Preprocessing {sound_type} sounds"):
        input_path = os.path.join(input_dir, audio_file)
        output_path = os.path.join(output_dir, audio_file)
        
        try:
            if sound_type == 'heart':
                preprocessor.preprocess_heart_sound(input_path, output_path)
            else:
                preprocessor.preprocess_lung_sound(input_path, output_path)
        except Exception as e:
            print(f"Error processing {audio_file}: {e}")

if __name__ == "__main__":
    # Preprocess heart sounds
    preprocess_dataset(
        'ml/datasets/heart/raw',
        'ml/datasets/heart/processed',
        sound_type='heart'
    )
    
    # Preprocess lung sounds
    preprocess_dataset(
        'ml/datasets/lung/raw',
        'ml/datasets/lung/processed',
        sound_type='lung'
    )
```

## 🎨 Data Augmentation

Create `ml/utils/data_augmentation.py`:

```python
import numpy as np
import librosa
from audiomentations import (
    Compose, AddGaussianNoise, TimeStretch, PitchShift,
    Shift, Gain, TimeMask, FrequencyMask
)

class AudioAugmenter:
    def __init__(self, sample_rate=8000):
        self.sample_rate = sample_rate
        
        # Define augmentation pipeline
        self.augment = Compose([
            AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.015, p=0.5),
            TimeStretch(min_rate=0.8, max_rate=1.25, p=0.5),
            PitchShift(min_semitones=-4, max_semitones=4, p=0.5),
            Shift(min_fraction=-0.5, max_fraction=0.5, p=0.5),
            Gain(min_gain_in_db=-12, max_gain_in_db=12, p=0.3),
        ])
    
    def augment_audio(self, audio):
        """Apply random augmentations to audio"""
        return self.augment(samples=audio, sample_rate=self.sample_rate)
    
    def create_augmented_dataset(self, audio_list, labels, num_augmentations=3):
        """Create augmented dataset"""
        augmented_audio = []
        augmented_labels = []
        
        for audio, label in zip(audio_list, labels):
            # Add original
            augmented_audio.append(audio)
            augmented_labels.append(label)
            
            # Add augmented versions
            for _ in range(num_augmentations):
                aug_audio = self.augment_audio(audio)
                augmented_audio.append(aug_audio)
                augmented_labels.append(label)
        
        return np.array(augmented_audio), np.array(augmented_labels)
```

## 🔬 Feature Extraction

Create `ml/scripts/extract_features.py`:

```python
import numpy as np
import librosa
import os
from tqdm import tqdm
import pickle

def extract_mel_spectrogram(audio, sr=8000, n_mels=64, n_fft=1024, hop_length=512):
    """Extract mel-spectrogram features"""
    mel_spec = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_mels=n_mels,
        n_fft=n_fft,
        hop_length=hop_length,
        fmax=sr//2
    )
    
    # Convert to log scale
    log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
    
    # Normalize to [0, 1]
    log_mel_spec = (log_mel_spec - log_mel_spec.min()) / (log_mel_spec.max() - log_mel_spec.min() + 1e-8)
    
    return log_mel_spec

def extract_features_from_dataset(audio_dir, output_file, sound_type='heart'):
    """Extract features from all audio files"""
    features = []
    labels = []
    filenames = []
    
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    
    for audio_file in tqdm(audio_files, desc=f"Extracting {sound_type} features"):
        audio_path = os.path.join(audio_dir, audio_file)
        
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=8000)
            
            # Extract mel-spectrogram
            mel_spec = extract_mel_spectrogram(audio, sr)
            
            # Extract label from filename (adjust based on your naming convention)
            label = extract_label_from_filename(audio_file, sound_type)
            
            features.append(mel_spec)
            labels.append(label)
            filenames.append(audio_file)
            
        except Exception as e:
            print(f"Error processing {audio_file}: {e}")
    
    # Save features
    data = {
        'features': np.array(features),
        'labels': np.array(labels),
        'filenames': filenames
    }
    
    with open(output_file, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"Extracted {len(features)} features, saved to {output_file}")
    return data

def extract_label_from_filename(filename, sound_type):
    """Extract label from filename"""
    # Implement based on your dataset naming convention
    # Example for PhysioNet: filename contains class info
    if sound_type == 'heart':
        if 'normal' in filename.lower():
            return 0
        elif 'murmur' in filename.lower():
            return 1
        elif 'extra' in filename.lower():
            return 2
        else:
            return 0  # Default to normal
    else:  # lung
        if 'normal' in filename.lower():
            return 0
        elif 'wheeze' in filename.lower():
            return 1
        elif 'crackle' in filename.lower():
            return 2
        elif 'both' in filename.lower():
            return 3
        else:
            return 0

if __name__ == "__main__":
    # Extract heart sound features
    extract_features_from_dataset(
        'ml/datasets/heart/processed',
        'ml/datasets/heart/features/features.pkl',
        sound_type='heart'
    )
    
    # Extract lung sound features
    extract_features_from_dataset(
        'ml/datasets/lung/processed',
        'ml/datasets/lung/features/features.pkl',
        sound_type='lung'
    )
```

## 🧠 Model Architecture

### Heart Sound Classification Model

```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

def create_heart_sound_model(input_shape=(64, 128, 1), num_classes=3):
    """
    Create CNN model for heart sound classification
    
    Architecture optimized for TinyML deployment:
    - Small number of parameters (<100K)
    - Efficient operations (Conv2D, MaxPooling, GlobalAveragePooling)
    - Suitable for quantization
    """
    model = keras.Sequential([
        # Input layer
        layers.Input(shape=input_shape),
        
        # First convolutional block
        layers.Conv2D(16, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.2),
        
        # Second convolutional block
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.2),
        
        # Third convolutional block
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.GlobalAveragePooling2D(),
        
        # Dense layers
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model
```

### Lung Sound Classification Model

```python
def create_lung_sound_model(input_shape=(64, 128, 1), num_classes=4):
    """
    Create CNN model for lung sound classification
    
    Similar architecture to heart model but with 4 output classes
    """
    model = keras.Sequential([
        layers.Input(shape=input_shape),
        
        layers.Conv2D(16, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.2),
        
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.2),
        
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.GlobalAveragePooling2D(),
        
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model
```

## 🎓 Training Pipeline

Create `ml/scripts/train_heart_model.py`:

```python
import tensorflow as tf
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt

# Load features
with open('ml/datasets/heart/features/features.pkl', 'rb') as f:
    data = pickle.load(f)

X = data['features']
y = data['labels']

# Reshape for CNN input (add channel dimension)
X = X[..., np.newaxis]

# Split dataset
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)

print(f"Training set: {X_train.shape}")
print(f"Validation set: {X_val.shape}")
print(f"Test set: {X_test.shape}")

# Compute class weights for imbalanced dataset
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weight_dict = dict(enumerate(class_weights))

# Create model
model = create_heart_sound_model(input_shape=X_train.shape[1:], num_classes=len(np.unique(y)))

# Compile model
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
)

# Callbacks
callbacks = [
    keras.callbacks.ModelCheckpoint(
        'ml/models/heart/checkpoints/best_model.h5',
        save_best_only=True,
        monitor='val_accuracy',
        mode='max'
    ),
    keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-6
    ),
    keras.callbacks.TensorBoard(log_dir='ml/models/heart/logs')
]

# Train model
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=32,
    class_weight=class_weight_dict,
    callbacks=callbacks,
    verbose=1
)

# Evaluate on test set
test_loss, test_acc, test_precision, test_recall = model.evaluate(X_test, y_test)
print(f"\nTest Accuracy: {test_acc:.4f}")
print(f"Test Precision: {test_precision:.4f}")
print(f"Test Recall: {test_recall:.4f}")

# Save final model
model.save('ml/models/heart/saved_models/heart_model.h5')

# Plot training history
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Val Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.title('Model Accuracy')

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.title('Model Loss')

plt.tight_layout()
plt.savefig('ml/models/heart/training_history.png')
plt.show()
```

## 📦 TensorFlow Lite Conversion

Create `ml/scripts/convert_to_tflite.py`:

```python
import tensorflow as tf
import numpy as np

def convert_to_tflite(model_path, output_path, quantize=True):
    """
    Convert TensorFlow model to TensorFlow Lite format
    
    Args:
        model_path: Path to saved TensorFlow model
        output_path: Path to save TFLite model
        quantize: Whether to apply INT8 quantization
    """
    # Load model
    model = tf.keras.models.load_model(model_path)
    
    # Create converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    if quantize:
        # Enable INT8 quantization
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Representative dataset for quantization
        def representative_dataset():
            # Load some sample data
            with open('ml/datasets/heart/features/features.pkl', 'rb') as f:
                data = pickle.load(f)
            X = data['features'][:100]  # Use 100 samples
            X = X[..., np.newaxis]
            for sample in X:
                yield [sample[np.newaxis, ...].astype(np.float32)]
        
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
    
    # Convert model
    tflite_model = converter.convert()
    
    # Save TFLite model
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    # Print model size
    model_size = len(tflite_model) / 1024  # KB
    print(f"TFLite model size: {model_size:.2f} KB")
    
    return tflite_model

# Convert heart model
convert_to_tflite(
    'ml/models/heart/saved_models/heart_model.h5',
    'ml/models/heart/tflite/heart_model.tflite',
    quantize=True
)

# Convert lung model
convert_to_tflite(
    'ml/models/lung/saved_models/lung_model.h5',
    'ml/models/lung/tflite/lung_model.tflite',
    quantize=True
)
```

## ⚡ Model Benchmarking

Create `ml/scripts/benchmark_model.py`:

```python
import tensorflow as tf
import numpy as np
import time

def benchmark_tflite_model(model_path, test_data, num_runs=100):
    """Benchmark TFLite model performance"""
    
    # Load TFLite model
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    
    # Get input and output details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Warm-up run
    interpreter.set_tensor(input_details[0]['index'], test_data[0:1])
    interpreter.invoke()
    
    # Benchmark
    inference_times = []
    
    for i in range(num_runs):
        start_time = time.time()
        interpreter.set_tensor(input_details[0]['index'], test_data[i:i+1])
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        end_time = time.time()
        
        inference_times.append((end_time - start_time) * 1000)  # Convert to ms
    
    # Calculate statistics
    avg_time = np.mean(inference_times)
    std_time = np.std(inference_times)
    min_time = np.min(inference_times)
    max_time = np.max(inference_times)
    
    print(f"Average inference time: {avg_time:.2f} ms")
    print(f"Std deviation: {std_time:.2f} ms")
    print(f"Min time: {min_time:.2f} ms")
    print(f"Max time: {max_time:.2f} ms")
    
    return avg_time

# Benchmark heart model
print("Benchmarking heart sound model...")
benchmark_tflite_model('ml/models/heart/tflite/heart_model.tflite', X_test)

# Benchmark lung model
print("\nBenchmarking lung sound model...")
benchmark_tflite_model('ml/models/lung/tflite/lung_model.tflite', X_test_lung)
```

## 🎯 Target Performance Metrics

### Heart Sound Model
- **Accuracy**: >85%
- **Sensitivity**: >90% (for abnormal detection)
- **Specificity**: >85%
- **Inference Time**: <100ms
- **Model Size**: <2MB

### Lung Sound Model
- **Accuracy**: >80%
- **Sensitivity**: >85% (for abnormal detection)
- **Specificity**: >80%
- **Inference Time**: <100ms
- **Model Size**: <2MB

## 🚀 Deployment to Arduino UNO Q

1. Copy TFLite models to device:
```bash
scp ml/models/heart/tflite/heart_model.tflite root@192.168.7.2:/opt/triage-station/models/heart/
scp ml/models/lung/tflite/lung_model.tflite root@192.168.7.2:/opt/triage-station/models/lung/
```

2. Verify models on device:
```bash
ssh root@192.168.7.2
ls -lh /opt/triage-station/models/
```

3. Test inference:
```bash
python3 /opt/triage-station/linux/ml/test_inference.py
```

## 📊 Model Evaluation and Validation

Create comprehensive evaluation scripts to validate model performance on test data, generate confusion matrices, ROC curves, and detailed classification reports.

## 🔄 Continuous Improvement

1. **Collect real-world data** from device usage
2. **Retrain models** with new data periodically
3. **A/B test** new models before deployment
4. **Monitor performance** metrics in production
5. **Update models** via USB or secure network transfer

This completes the ML training pipeline. Next, I'll create the inference engine and deployment code.
