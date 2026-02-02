#!/usr/bin/env python3
"""
Triage Decision Engine
======================

Multi-modal sensor fusion and triage decision making system.
"""

import numpy as np
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class TriageDecisionEngine:
    """
    Multi-modal triage decision engine
    
    Combines audio analysis, ML predictions, and sensor data to make
    informed triage decisions with explainable reasoning.
    """
    
    def __init__(self,
                 thresholds: Dict[str, float] = None,
                 fusion_weights: Dict[str, float] = None,
                 risk_factors: Dict[str, Any] = None):
        """
        Initialize triage decision engine
        
        Args:
            thresholds: Risk thresholds for different metrics
            fusion_weights: Weights for sensor fusion
            risk_factors: Additional risk factor configurations
        """
        # Default thresholds
        self.thresholds = thresholds or {
            'ml_confidence': 0.7,
            'temperature_fever': 38.0,  # Celsius
            'heart_rate_high': 100,  # BPM
            'heart_rate_low': 50,
            'respiratory_rate_high': 25,  # Breaths per minute
            'respiratory_rate_low': 10
        }
        
        # Default fusion weights
        self.fusion_weights = fusion_weights or {
            'ml_prediction': 0.5,
            'audio_analysis': 0.3,
            'vital_signs': 0.2
        }
        
        # Risk factors
        self.risk_factors = risk_factors or {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize decision engine"""
        self.logger.info("Triage decision engine initialized")
        return True
    
    async def make_decision(self,
                           heart_result: Optional[Dict[str, Any]] = None,
                           lung_result: Optional[Dict[str, Any]] = None,
                           sensor_data: Dict[str, Any] = None,
                           examination_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make triage decision based on all available data
        
        Args:
            heart_result: Heart sound ML classification result
            lung_result: Lung sound ML classification result
            sensor_data: Current sensor readings
            examination_data: Examination metadata
            
        Returns:
            dict: Triage decision with reasoning
        """
        try:
            self.logger.info("Making triage decision...")
            
            # Initialize decision components
            risk_scores = {}
            risk_factors = []
            recommendations = []
            
            # Analyze ML predictions
            if heart_result and heart_result.get('success'):
                heart_risk = self._analyze_heart_prediction(heart_result)
                risk_scores['heart_ml'] = heart_risk['score']
                risk_factors.extend(heart_risk['factors'])
                recommendations.extend(heart_risk['recommendations'])
            
            if lung_result and lung_result.get('success'):
                lung_risk = self._analyze_lung_prediction(lung_result)
                risk_scores['lung_ml'] = lung_risk['score']
                risk_factors.extend(lung_risk['factors'])
                recommendations.extend(lung_risk['recommendations'])
            
            # Analyze vital signs
            if sensor_data:
                vital_risk = self._analyze_vital_signs(sensor_data)
                risk_scores['vital_signs'] = vital_risk['score']
                risk_factors.extend(vital_risk['factors'])
                recommendations.extend(vital_risk['recommendations'])
            
            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk(risk_scores)
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk_score)
            
            # Generate explanation
            explanation = self._generate_explanation(
                risk_level, risk_scores, risk_factors
            )
            
            # Create decision
            decision = {
                'timestamp': datetime.now().isoformat(),
                'risk_level': risk_level,
                'risk_score': overall_risk_score,
                'risk_scores_breakdown': risk_scores,
                'risk_factors': risk_factors,
                'recommendations': recommendations,
                'explanation': explanation,
                'requires_referral': risk_level in ['MEDIUM', 'HIGH'],
                'urgency': self._determine_urgency(risk_level, risk_factors),
                'confidence': self._calculate_decision_confidence(risk_scores)
            }
            
            self.logger.info(f"Triage decision: {risk_level} (score: {overall_risk_score:.2f})")
            return decision
            
        except Exception as e:
            self.logger.error(f"Error making triage decision: {e}")
            return {
                'error': str(e),
                'risk_level': 'UNKNOWN',
                'requires_referral': True
            }
    
    def _analyze_heart_prediction(self, heart_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze heart sound ML prediction"""
        risk_score = 0.0
        factors = []
        recommendations = []
        
        predicted_class = heart_result.get('predicted_class', 'Normal')
        confidence = heart_result.get('confidence', 0.0)
        
        if predicted_class != 'Normal':
            # Abnormal heart sound detected
            risk_score = 0.8 * confidence  # Higher risk for any abnormality
            factors.append(f"Abnormal heart sound detected")
            
            # General recommendations for any heart abnormality
            recommendations.append("Cardiac evaluation by physician recommended")
            recommendations.append("Consider ECG and echocardiography")
            recommendations.append("Monitor for symptoms: chest pain, palpitations, shortness of breath")
        else:
            # Normal heart sound
            risk_score = 0.1
            if confidence < self.thresholds['ml_confidence']:
                factors.append(f"Low confidence in normal classification ({confidence:.2f})")
                risk_score = 0.3
        
        return {
            'score': risk_score,
            'factors': factors,
            'recommendations': recommendations
        }
    
    def _analyze_lung_prediction(self, lung_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lung sound ML prediction"""
        risk_score = 0.0
        factors = []
        recommendations = []
        
        predicted_class = lung_result.get('predicted_class', 'Normal')
        confidence = lung_result.get('confidence', 0.0)
        
        if predicted_class != 'Normal':
            # Abnormal lung sound detected
            risk_score = 0.7 * confidence
            factors.append(f"Abnormal lung sound detected: {predicted_class}")
            
            if predicted_class == 'Wheeze':
                recommendations.append("Possible asthma or bronchospasm")
                recommendations.append("Consider bronchodilator therapy")
                recommendations.append("Pulmonary function testing if persistent")
            elif predicted_class == 'Crackle':
                recommendations.append("Possible pneumonia or pulmonary edema")
                recommendations.append("Chest X-ray recommended")
                recommendations.append("Monitor for fever and respiratory distress")
            elif predicted_class == 'Both':
                recommendations.append("Multiple abnormalities detected")
                recommendations.append("Urgent pulmonary evaluation recommended")
                risk_score = 0.9 * confidence
        else:
            # Normal lung sound
            risk_score = 0.1
            if confidence < self.thresholds['ml_confidence']:
                factors.append(f"Low confidence in normal classification ({confidence:.2f})")
                risk_score = 0.3
        
        return {
            'score': risk_score,
            'factors': factors,
            'recommendations': recommendations
        }
    
    def _analyze_vital_signs(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze vital signs from sensors"""
        risk_score = 0.0
        factors = []
        recommendations = []
        
        # Temperature analysis
        temp_data = sensor_data.get('temperature', {})
        if temp_data.get('valid'):
            temp_celsius = temp_data.get('celsius', 0)
            
            if temp_celsius >= self.thresholds['temperature_fever']:
                risk_score += 0.3
                factors.append(f"Fever detected: {temp_celsius:.1f}°C")
                recommendations.append("Fever management and infection workup")
            elif temp_celsius < 35.0:
                risk_score += 0.2
                factors.append(f"Hypothermia detected: {temp_celsius:.1f}°C")
                recommendations.append("Warming measures and evaluation")
        
        # Movement analysis (stability during examination)
        movement_data = sensor_data.get('movement', {})
        if movement_data.get('detected'):
            factors.append("Patient movement detected during examination")
            recommendations.append("Repeat examination when patient is stable")
        
        # Distance validation
        distance_data = sensor_data.get('distance', {})
        if not distance_data.get('in_range'):
            factors.append("Suboptimal stethoscope placement")
            recommendations.append("Ensure proper contact for accurate assessment")
        
        return {
            'score': risk_score,
            'factors': factors,
            'recommendations': recommendations
        }
    
    def _calculate_overall_risk(self, risk_scores: Dict[str, float]) -> float:
        """Calculate weighted overall risk score"""
        if not risk_scores:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for component, score in risk_scores.items():
            # Map component to weight
            if 'ml' in component:
                weight = self.fusion_weights['ml_prediction']
            elif 'vital' in component:
                weight = self.fusion_weights['vital_signs']
            else:
                weight = self.fusion_weights['audio_analysis']
            
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= 0.7:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _determine_urgency(self, risk_level: str, risk_factors: list) -> str:
        """Determine urgency of referral"""
        if risk_level == 'HIGH':
            return 'URGENT'
        elif risk_level == 'MEDIUM':
            # Check for specific urgent factors
            urgent_keywords = ['fever', 'both', 'multiple', 'urgent']
            for factor in risk_factors:
                if any(keyword in factor.lower() for keyword in urgent_keywords):
                    return 'URGENT'
            return 'ROUTINE'
        else:
            return 'NON-URGENT'
    
    def _calculate_decision_confidence(self, risk_scores: Dict[str, float]) -> float:
        """Calculate confidence in the decision"""
        if not risk_scores:
            return 0.0
        
        # Confidence based on consistency of risk scores
        scores = list(risk_scores.values())
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # High confidence if scores are consistent
        confidence = 1.0 - min(std_score / (mean_score + 0.1), 1.0)
        
        return float(confidence)
    
    def _generate_explanation(self,
                             risk_level: str,
                             risk_scores: Dict[str, float],
                             risk_factors: list) -> str:
        """Generate human-readable explanation"""
        explanation_parts = []
        
        # Risk level statement
        if risk_level == 'HIGH':
            explanation_parts.append("HIGH RISK: Significant abnormalities detected.")
        elif risk_level == 'MEDIUM':
            explanation_parts.append("MEDIUM RISK: Some abnormalities detected.")
        else:
            explanation_parts.append("LOW RISK: No significant abnormalities detected.")
        
        # Risk factors
        if risk_factors:
            explanation_parts.append("\nKey findings:")
            for factor in risk_factors[:5]:  # Limit to top 5
                explanation_parts.append(f"  • {factor}")
        
        # Risk score breakdown
        if risk_scores:
            explanation_parts.append("\nRisk assessment:")
            for component, score in risk_scores.items():
                explanation_parts.append(f"  • {component}: {score:.2f}")
        
        return "\n".join(explanation_parts)
