#!/usr/bin/env python3
"""
ML Inference Engine
==================

TensorFlow Lite inference engine for heart and lung sound classification.
"""

import numpy as np
import tensorflow as tf
import logging
import time
from pathlib import Path
import json

class InferenceEngine:
    """
    TensorFlow Lite inference engine for medical sound classification
    """
    
    def __init__(self, 
                 heart_model_path: str,
                 lung_model_path: str,
                 confidence_threshold: float = 0.7):
        """
        Initialize inference engine
        
        Args:
            heart_model_path: Path to heart sound TFLite model
            lung_model_path: Path to lung sound TFLite model
            confidence_threshold: Minimum confidence for predictions
        """
        self.heart_model_path = heart_model_path
        self.lung_model_path = lung_model_path
        self.confidence_threshold = confidence_threshold
        
        # Interpreters
        self.heart_interpreter = None
        self.lung_interpreter = None
        
        # Model metadata
        self.heart_classes = ['Normal', 'Abnormal']
        self.lung_classes = ['Normal', 'Wheeze', 'Crackle', 'Both']
        
        # Performance tracking
        self.inference_times = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """
        Initialize TFLite interpreters
        
        Returns:
            bool: True if successful
        """
        try:
            # Load heart sound model
            if Path(self.heart_model_path).exists():
                self.heart_interpreter = tf.lite.Interpreter(model_path=self.heart_model_path)
                self.heart_interpreter.allocate_tensors()
                self.logger.info(f"Heart sound model loaded: {self.heart_model_path}")
            else:
                self.logger.warning(f"Heart model not found: {self.heart_model_path}")
            
            # Load lung sound model
            if Path(self.lung_model_path).exists():
                self.lung_interpreter = tf.lite.Interpreter(model_path=self.lung_model_path)
                self.lung_interpreter.allocate_tensors()
                self.logger.info(f"Lung sound model loaded: {self.lung_model_path}")
            else:
                self.logger.warning(f"Lung model not found: {self.lung_model_path}")
            
            # Warm-up inference
            if self.heart_interpreter:
                await self._warmup_model(self.heart_interpreter)
            if self.lung_interpreter:
                await self._warmup_model(self.lung_interpreter)
            
            self.logger.info("Inference engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize inference engine: {e}")
            return False
    
    async def _warmup_model(self, interpreter):
        """Perform warm-up inference"""
        input_details = interpreter.get_input_details()
        input_shape = input_details[0]['shape']
        
        # Create dummy input
        dummy_input = np.zeros(input_shape, dtype=np.float32)
        
        # Run inference
        interpreter.set_tensor(input_details[0]['index'], dummy_input)
        interpreter.invoke()
        
        self.logger.debug("Model warm-up completed")
    
    async def classify_heart_sound(self, audio_features: np.ndarray) -> dict:
        """
        Classify heart sound
        
        Args:
            audio_features: Mel-spectrogram features
            
        Returns:
            dict: Classification results
        """
        if self.heart_interpreter is None:
            return {
                'success': False,
                'error': 'Heart sound model not loaded'
            }
        
        try:
            start_time = time.time()
            
            # Prepare input
            input_details = self.heart_interpreter.get_input_details()
            output_details = self.heart_interpreter.get_output_details()
            
            # Reshape features if needed
            input_shape = input_details[0]['shape']
            if audio_features.shape != tuple(input_shape[1:]):
                audio_features = self._reshape_features(audio_features, input_shape[1:])
            
            # Add batch dimension
            input_data = audio_features[np.newaxis, ...].astype(np.float32)
            
            # Run inference
            self.heart_interpreter.set_tensor(input_details[0]['index'], input_data)
            self.heart_interpreter.invoke()
            
            # Get output
            output_data = self.heart_interpreter.get_tensor(output_details[0]['index'])
            probabilities = output_data[0]
            
            # Get prediction
            predicted_class = int(np.argmax(probabilities))
            confidence = float(probabilities[predicted_class])
            
            inference_time = (time.time() - start_time) * 1000  # ms
            self.inference_times.append(inference_time)
            
            # Create result
            result = {
                'success': True,
                'predicted_class': self.heart_classes[predicted_class],
                'predicted_class_id': predicted_class,
                'confidence': confidence,
                'probabilities': {
                    class_name: float(prob)
                    for class_name, prob in zip(self.heart_classes, probabilities)
                },
                'is_abnormal': predicted_class != 0,  # 0 is Normal
                'meets_threshold': confidence >= self.confidence_threshold,
                'inference_time_ms': inference_time
            }
            
            self.logger.info(f"Heart sound classification: {result['predicted_class']} ({confidence:.3f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Heart sound classification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def classify_lung_sound(self, audio_features: np.ndarray) -> dict:
        """
        Classify lung sound
        
        Args:
            audio_features: Mel-spectrogram features
            
        Returns:
            dict: Classification results
        """
        if self.lung_interpreter is None:
            return {
                'success': False,
                'error': 'Lung sound model not loaded'
            }
        
        try:
            start_time = time.time()
            
            # Prepare input
            input_details = self.lung_interpreter.get_input_details()
            output_details = self.lung_interpreter.get_output_details()
            
            # Reshape features if needed
            input_shape = input_details[0]['shape']
            if audio_features.shape != tuple(input_shape[1:]):
                audio_features = self._reshape_features(audio_features, input_shape[1:])
            
            # Add batch dimension
            input_data = audio_features[np.newaxis, ...].astype(np.float32)
            
            # Run inference
            self.lung_interpreter.set_tensor(input_details[0]['index'], input_data)
            self.lung_interpreter.invoke()
            
            # Get output
            output_data = self.lung_interpreter.get_tensor(output_details[0]['index'])
            probabilities = output_data[0]
            
            # Get prediction
            predicted_class = int(np.argmax(probabilities))
            confidence = float(probabilities[predicted_class])
            
            inference_time = (time.time() - start_time) * 1000  # ms
            self.inference_times.append(inference_time)
            
            # Create result
            result = {
                'success': True,
                'predicted_class': self.lung_classes[predicted_class],
                'predicted_class_id': predicted_class,
                'confidence': confidence,
                'probabilities': {
                    class_name: float(prob)
                    for class_name, prob in zip(self.lung_classes, probabilities)
                },
                'is_abnormal': predicted_class != 0,  # 0 is Normal
                'meets_threshold': confidence >= self.confidence_threshold,
                'inference_time_ms': inference_time
            }
            
            self.logger.info(f"Lung sound classification: {result['predicted_class']} ({confidence:.3f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Lung sound classification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _reshape_features(self, features: np.ndarray, target_shape: tuple) -> np.ndarray:
        """Reshape features to match model input"""
        # Simple resize using interpolation
        from scipy.ndimage import zoom
        
        zoom_factors = [target_shape[i] / features.shape[i] for i in range(len(target_shape) - 1)]
        zoom_factors.append(1)  # Don't zoom channel dimension
        
        reshaped = zoom(features, zoom_factors, order=1)
        return reshaped
    
    def get_average_inference_time(self) -> float:
        """Get average inference time"""
        if not self.inference_times:
            return 0.0
        return np.mean(self.inference_times)
    
    def get_model_info(self) -> dict:
        """Get model information"""
        info = {
            'heart_model': {
                'path': self.heart_model_path,
                'loaded': self.heart_interpreter is not None,
                'classes': self.heart_classes
            },
            'lung_model': {
                'path': self.lung_model_path,
                'loaded': self.lung_interpreter is not None,
                'classes': self.lung_classes
            },
            'confidence_threshold': self.confidence_threshold,
            'average_inference_time_ms': self.get_average_inference_time()
        }
        
        return info
