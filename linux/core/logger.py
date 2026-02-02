#!/usr/bin/env python3
"""
Smart Rural Triage Station - Logging System
===========================================

This module provides centralized logging configuration and utilities
for the triage station system.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional
from pathlib import Path


def setup_logging(level: str = 'INFO', 
                 log_file: Optional[str] = None,
                 max_size: str = '10MB',
                 backup_count: int = 5,
                 format_string: Optional[str] = None) -> logging.Logger:
    """
    Setup centralized logging for the triage station.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        format_string: Custom format string (optional)
        
    Returns:
        logging.Logger: Configured root logger
    """
    
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Default format string
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[%(filename)s:%(lineno)d] - %(message)s'
        )
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # Parse max_size
            max_bytes = _parse_size(max_size)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            root_logger.info(f"Logging to file: {log_file}")
            
        except Exception as e:
            root_logger.error(f"Failed to setup file logging: {e}")
    
    # Setup specific loggers for different components
    _setup_component_loggers(numeric_level)
    
    root_logger.info(f"Logging system initialized - Level: {level}")
    return root_logger


def _parse_size(size_str: str) -> int:
    """
    Parse size string to bytes.
    
    Args:
        size_str: Size string (e.g., '10MB', '1GB')
        
    Returns:
        int: Size in bytes
    """
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # Assume bytes
        return int(size_str)


def _setup_component_loggers(level: int):
    """
    Setup specific loggers for different system components.
    
    Args:
        level: Logging level
    """
    
    # Component-specific loggers
    components = [
        'system_manager',
        'state_machine',
        'serial_manager',
        'audio_manager',
        'camera_manager',
        'inference_engine',
        'decision_engine',
        'calibration_manager',
        'web_app'
    ]
    
    for component in components:
        logger = logging.getLogger(component)
        logger.setLevel(level)
        # Inherit handlers from root logger
        logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific component.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Component logger
    """
    return logging.getLogger(name)


class TriageStationLogger:
    """
    Custom logger class for the triage station with additional features.
    """
    
    def __init__(self, name: str):
        """
        Initialize triage station logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.name = name
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """
        Log message with additional context.
        
        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional context
        """
        if kwargs:
            context_str = ' | '.join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} | {context_str}"
        
        self.logger.log(level, message)
    
    def log_examination_start(self, mode: str, patient_id: str = "anonymous"):
        """Log examination start."""
        self.info("Examination started", mode=mode, patient_id=patient_id)
    
    def log_examination_complete(self, mode: str, duration: float, result: str):
        """Log examination completion."""
        self.info("Examination completed", 
                 mode=mode, duration=duration, result=result)
    
    def log_ml_inference(self, model: str, inference_time: float, confidence: float):
        """Log ML inference."""
        self.info("ML inference completed",
                 model=model, inference_time=inference_time, confidence=confidence)
    
    def log_sensor_data(self, sensor: str, value: float, valid: bool):
        """Log sensor reading."""
        self.debug("Sensor reading",
                  sensor=sensor, value=value, valid=valid)
    
    def log_actuator_command(self, actuator: str, command: str, value: any):
        """Log actuator command."""
        self.debug("Actuator command",
                  actuator=actuator, command=command, value=value)
    
    def log_error_with_context(self, error: Exception, context: dict = None):
        """Log error with full context."""
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg += f" | Context: {context}"
        self.error(error_msg, exc_info=True)


def setup_performance_logging(log_file: str = '/opt/triage-station/logs/performance.log'):
    """
    Setup performance logging for system monitoring.
    
    Args:
        log_file: Performance log file path
    """
    try:
        # Create performance logger
        perf_logger = logging.getLogger('performance')
        perf_logger.setLevel(logging.INFO)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Performance log format
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s'
        )
        
        # File handler for performance logs
        perf_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=3
        )
        perf_handler.setFormatter(perf_formatter)
        perf_logger.addHandler(perf_handler)
        
        # Don't propagate to root logger
        perf_logger.propagate = False
        
        logging.getLogger().info(f"Performance logging setup: {log_file}")
        
    except Exception as e:
        logging.getLogger().error(f"Failed to setup performance logging: {e}")


def log_performance_metric(metric_name: str, value: float, unit: str = "", **context):
    """
    Log a performance metric.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        **context: Additional context
    """
    perf_logger = logging.getLogger('performance')
    
    context_str = ""
    if context:
        context_str = " | " + " | ".join([f"{k}={v}" for k, v in context.items()])
    
    perf_logger.info(f"{metric_name}: {value}{unit}{context_str}")


def setup_audit_logging(log_file: str = '/opt/triage-station/logs/audit.log'):
    """
    Setup audit logging for security and compliance.
    
    Args:
        log_file: Audit log file path
    """
    try:
        # Create audit logger
        audit_logger = logging.getLogger('audit')
        audit_logger.setLevel(logging.INFO)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Audit log format
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s'
        )
        
        # File handler for audit logs
        audit_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        audit_handler.setFormatter(audit_formatter)
        audit_logger.addHandler(audit_handler)
        
        # Don't propagate to root logger
        audit_logger.propagate = False
        
        logging.getLogger().info(f"Audit logging setup: {log_file}")
        
    except Exception as e:
        logging.getLogger().error(f"Failed to setup audit logging: {e}")


def log_audit_event(event_type: str, details: str, user: str = "system", **context):
    """
    Log an audit event.
    
    Args:
        event_type: Type of event
        details: Event details
        user: User who triggered the event
        **context: Additional context
    """
    audit_logger = logging.getLogger('audit')
    
    context_str = ""
    if context:
        context_str = " | " + " | ".join([f"{k}={v}" for k, v in context.items()])
    
    audit_logger.info(f"{event_type} | User: {user} | {details}{context_str}")


# Example usage and testing
if __name__ == "__main__":
    # Test basic logging setup
    logger = setup_logging(
        level='DEBUG',
        log_file='/tmp/test_triage.log',
        max_size='1MB',
        backup_count=3
    )
    
    # Test basic logging
    logger.info("Testing basic logging")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test custom logger
    custom_logger = TriageStationLogger('test_component')
    custom_logger.info("Testing custom logger")
    custom_logger.log_examination_start('heart', 'test_patient')
    custom_logger.log_ml_inference('heart_model', 0.123, 0.95)
    
    # Test performance logging
    setup_performance_logging('/tmp/test_performance.log')
    log_performance_metric('inference_time', 123.45, 'ms', model='heart')
    
    # Test audit logging
    setup_audit_logging('/tmp/test_audit.log')
    log_audit_event('EXAMINATION_START', 'Heart examination started', 'nurse_1')
    
    print("Logging test completed - check /tmp/test_*.log files")