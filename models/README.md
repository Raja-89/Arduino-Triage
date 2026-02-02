# Smart Rural Triage Station - ML Models

This directory contains the machine learning models for the Smart Rural Triage Station.

## 📁 Directory Structure

```
models/
├── heart/
│   ├── heart_model.tflite          # Heart sound classification model
│   ├── heart_model_metadata.json   # Model specifications and performance
│   └── heart_model_backup.tflite   # Backup/previous version
├── lung/
│   ├── lung_model.tflite           # Lung sound classification model
│   ├── lung_model_metadata.json    # Model specifications and performance
│   └── lung_model_backup.tflite    # Backup/previous version
└── yamnet/
    ├── yamnet_model.tflite          # YAMNet general audio classification
    └── yamnet_classes.txt           # YAMNet class labels
```

## 🧠 Model Specifications

### Heart Sound Model
- **Input**: Mel-spectrogram (64 mel bands, 87 time frames)
- **Output**: 2 classes (Normal, Abnormal)
- **Size**: ~1.8MB
- **Inference Time**: ~150ms
- **Accuracy**: >92% on validation set (binary classification)

### Lung Sound Model
- **Input**: Mel-spectrogram (64 mel bands, 87 time frames)
- **Output**: 4 classes (Normal, Wheeze, Crackle, Both)
- **Size**: ~1.9MB
- **Inference Time**: ~160ms
- **Accuracy**: >85% on validation set

### YAMNet Model (Optional)
- **Input**: Mel-spectrogram (64 mel bands, 96 time frames)
- **Output**: 521 audio event classes
- **Size**: ~3.4MB
- **Purpose**: General audio classification and noise detection

## 🚨 **IMPORTANT: Missing Model Files**

**Current Status**: ⚠️ **Model files are currently placeholders**

The actual `.tflite` model files need to be trained and placed in this directory. The system is designed to work with these models, but they need to be created first.

### What You Need to Do:

1. **Train Models**: Use the training scripts in the `ml/scripts/` directory
2. **Convert to TFLite**: Convert trained models to TensorFlow Lite format
3. **Optimize**: Apply quantization for edge deployment
4. **Validate**: Test models on validation datasets
5. **Deploy**: Copy `.tflite` files to appropriate directories

## 📊 Model Requirements

### Technical Requirements
- **Format**: TensorFlow Lite (.tflite)
- **Quantization**: INT8 for optimal performance
- **Size**: <2MB per model for memory efficiency
- **Inference Time**: <200ms per model
- **Input Format**: Mel-spectrogram features

### Performance Requirements
- **Heart Model**: >92% accuracy on binary heart sound classification (Normal/Abnormal)
- **Lung Model**: >85% accuracy on lung sound classification
- **Robustness**: Handle various recording conditions
- **Reliability**: Consistent performance across devices

## 🔧 Model Integration

### Loading Models
The inference engine automatically loads models from these paths:
```python
heart_model_path = "models/heart/heart_model.tflite"
lung_model_path = "models/lung/lung_model.tflite"
yamnet_model_path = "models/yamnet/yamnet_model.tflite"
```

### Model Validation
Before deployment, models should be validated using:
```bash
python3 linux/ml/inference_engine.py  # Test model loading
python3 tests/test_ml.py               # Run ML tests
```

### Fallback Behavior
If models are missing or fail to load:
- System logs warning messages
- Inference returns default "unknown" results
- System continues to operate for testing
- Web interface shows model status

## 📝 Model Metadata

Each model directory contains a `*_metadata.json` file with:
- Model specifications (input/output shapes, classes)
- Performance metrics (accuracy, inference time)
- Training information (dataset, parameters)
- Deployment requirements (memory, CPU)
- Clinical validation status

## 🔄 Model Updates

### Updating Models
1. **Backup Current**: Copy existing `.tflite` to `*_backup.tflite`
2. **Deploy New**: Copy new model to main `.tflite` file
3. **Update Metadata**: Update corresponding metadata JSON
4. **Test**: Validate new model performance
5. **Restart Service**: `sudo systemctl restart triage-station`

### Version Control
- Keep backup versions for rollback capability
- Update metadata with version information
- Document changes and performance differences
- Test thoroughly before production deployment

## 🧪 Testing Models

### Unit Tests
```bash
# Test model loading
python3 -c "
from linux.ml.inference_engine import InferenceEngine
engine = InferenceEngine()
print('✅ Models loaded' if engine.initialize() else '❌ Model loading failed')
"
```

### Integration Tests
```bash
# Test full inference pipeline
python3 tests/test_ml.py

# Test with sample audio
python3 -c "
import numpy as np
from linux.ml.inference_engine import InferenceEngine
engine = InferenceEngine()
if engine.initialize():
    # Test with dummy audio features
    features = np.random.randn(64, 87).astype(np.float32)
    result = engine.classify_heart_sound(features)
    print(f'Heart classification: {result}')
"
```

## 📚 Training Resources

### Datasets
- **Heart Sounds**: PhysioNet Challenge datasets, PASCAL CHiME
- **Lung Sounds**: ICBHI Respiratory Sound Database
- **General Audio**: AudioSet, FSD50K

### Training Scripts
- `ml/scripts/train_heart_model.py` - Heart sound model training
- `ml/scripts/train_lung_model.py` - Lung sound model training
- `ml/scripts/convert_to_tflite.py` - TensorFlow Lite conversion

### Model Architecture
- **Base**: Convolutional Neural Network (CNN)
- **Input**: Mel-spectrogram features
- **Layers**: Conv2D, MaxPooling, Dense, Dropout
- **Activation**: ReLU, Softmax output
- **Optimization**: Adam optimizer, categorical crossentropy loss

## ⚠️ Clinical Considerations

### Regulatory Compliance
- Models are for research and development only
- Clinical validation required before medical use
- Regulatory approval needed for patient care
- Performance monitoring in clinical settings

### Limitations
- Models trained on limited datasets
- Performance may vary across populations
- Not a replacement for clinical judgment
- Requires proper training for healthcare workers

## 🔗 Related Documentation

- [ML Training Guide](../docs/ML_TRAINING_GUIDE.md)
- [Software Implementation Guide](../docs/SOFTWARE_IMPLEMENTATION_GUIDE.md)
- [System Architecture](../docs/SOFTWARE_ARCHITECTURE_GUIDE.md)
- [Deployment Guide](../docs/COMPLETE_DEPLOYMENT_GUIDE.md)

---

**Note**: This system is designed for educational and research purposes. Clinical validation and regulatory approval are required before use in patient care.