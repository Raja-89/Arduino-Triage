#!/usr/bin/env python3
"""
Smart Rural Triage Station - Camera Manager
===========================================

This module handles camera operations for positioning guidance and
visual feedback during examinations.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import cv2
import numpy as np
import logging
import asyncio
import threading
import time
from typing import Optional, Tuple, Callable, Dict, Any
from datetime import datetime


class CameraManager:
    """
    Camera management for positioning guidance and visual feedback.
    
    Provides camera initialization, frame capture, positioning guidance,
    and visual feedback during examinations.
    """
    
    def __init__(self, 
                 device_id: int = 0,
                 width: int = 640,
                 height: int = 480,
                 fps: int = 30):
        """
        Initialize camera manager.
        
        Args:
            device_id: Camera device ID
            width: Frame width
            height: Frame height
            fps: Frames per second
        """
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        
        # Camera objects
        self.camera = None
        self.active = False
        
        # Frame processing
        self.current_frame = None
        self.frame_callback = None
        self.capture_thread = None
        self.running = False
        
        # Positioning guidance
        self.guidance_enabled = False
        self.target_position = (width // 2, height // 2)
        self.position_tolerance = 50
        
        # Statistics
        self.stats = {
            'frames_captured': 0,
            'frames_processed': 0,
            'average_fps': 0.0,
            'last_frame_time': None
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Camera manager initialized - Device: {device_id}, Resolution: {width}x{height}")
    
    async def initialize(self) -> bool:
        """
        Initialize camera system.
        
        Returns:
            bool: True if successful
        """
        try:
            # Initialize camera
            self.camera = cv2.VideoCapture(self.device_id)
            
            if not self.camera.isOpened():
                self.logger.error(f"Failed to open camera device {self.device_id}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Verify settings
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"Camera initialized - Actual resolution: {actual_width}x{actual_height}, FPS: {actual_fps}")
            
            # Test frame capture
            ret, frame = self.camera.read()
            if not ret:
                self.logger.error("Failed to capture test frame")
                return False
            
            self.current_frame = frame
            self.active = True
            
            self.logger.info("Camera system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            return False
    
    async def start_capture(self, callback: Optional[Callable] = None) -> bool:
        """
        Start continuous frame capture.
        
        Args:
            callback: Optional callback for frame processing
            
        Returns:
            bool: True if started successfully
        """
        try:
            if not self.active:
                self.logger.error("Camera not initialized")
                return False
            
            if self.running:
                self.logger.warning("Capture already running")
                return True
            
            self.frame_callback = callback
            self.running = True
            
            # Start capture thread
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                name="CameraCaptureThread",
                daemon=True
            )
            self.capture_thread.start()
            
            self.logger.info("Camera capture started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start camera capture: {e}")
            return False
    
    async def stop_capture(self):
        """Stop frame capture."""
        try:
            if not self.running:
                return
            
            self.running = False
            
            # Wait for capture thread to finish
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=5.0)
            
            self.frame_callback = None
            
            self.logger.info("Camera capture stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping camera capture: {e}")
    
    def _capture_loop(self):
        """Main capture loop."""
        self.logger.info("Camera capture loop started")
        
        frame_count = 0
        start_time = time.time()
        
        while self.running and self.camera and self.camera.isOpened():
            try:
                ret, frame = self.camera.read()
                
                if not ret:
                    self.logger.warning("Failed to capture frame")
                    continue
                
                # Update statistics
                frame_count += 1
                self.stats['frames_captured'] = frame_count
                self.stats['last_frame_time'] = datetime.now()
                
                # Calculate FPS
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    self.stats['average_fps'] = frame_count / elapsed_time
                
                # Store current frame
                self.current_frame = frame.copy()
                
                # Process frame if guidance is enabled
                if self.guidance_enabled:
                    processed_frame = self._process_frame_for_guidance(frame)
                else:
                    processed_frame = frame
                
                # Call frame callback if registered
                if self.frame_callback:
                    try:
                        self.frame_callback(processed_frame)
                        self.stats['frames_processed'] += 1
                    except Exception as e:
                        self.logger.error(f"Error in frame callback: {e}")
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                self.logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("Camera capture loop ended")
    
    def _process_frame_for_guidance(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame for positioning guidance.
        
        Args:
            frame: Input frame
            
        Returns:
            np.ndarray: Processed frame with guidance overlay
        """
        try:
            # Create a copy for processing
            processed_frame = frame.copy()
            
            # Draw target position
            cv2.circle(processed_frame, self.target_position, 30, (0, 255, 0), 2)
            cv2.circle(processed_frame, self.target_position, 5, (0, 255, 0), -1)
            
            # Draw tolerance circle
            cv2.circle(processed_frame, self.target_position, self.position_tolerance, (0, 255, 0), 1)
            
            # Add text instructions
            cv2.putText(processed_frame, "Position stethoscope in green circle", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Detect current stethoscope position (simplified)
            current_position = self._detect_stethoscope_position(frame)
            
            if current_position:
                # Draw current position
                cv2.circle(processed_frame, current_position, 10, (0, 0, 255), -1)
                
                # Calculate distance from target
                distance = np.sqrt((current_position[0] - self.target_position[0])**2 + 
                                 (current_position[1] - self.target_position[1])**2)
                
                # Provide feedback
                if distance <= self.position_tolerance:
                    cv2.putText(processed_frame, "GOOD POSITION", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(processed_frame, "ADJUST POSITION", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Draw arrow pointing to target
                    self._draw_guidance_arrow(processed_frame, current_position, self.target_position)
            
            return processed_frame
            
        except Exception as e:
            self.logger.error(f"Error processing frame for guidance: {e}")
            return frame
    
    def _detect_stethoscope_position(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect stethoscope position in frame (simplified implementation).
        
        Args:
            frame: Input frame
            
        Returns:
            tuple: (x, y) position or None if not detected
        """
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Define range for stethoscope color (adjust based on actual stethoscope)
            # This is a simplified example - in practice, you'd use more sophisticated detection
            lower_color = np.array([0, 0, 0])  # Black/dark colors
            upper_color = np.array([180, 255, 100])
            
            # Create mask
            mask = cv2.inRange(hsv, lower_color, upper_color)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find largest contour (assumed to be stethoscope)
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Get centroid
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting stethoscope position: {e}")
            return None
    
    def _draw_guidance_arrow(self, frame: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]):
        """
        Draw guidance arrow from current position to target.
        
        Args:
            frame: Frame to draw on
            start: Start position
            end: End position
        """
        try:
            # Draw arrow
            cv2.arrowedLine(frame, start, end, (255, 0, 0), 3, tipLength=0.3)
            
        except Exception as e:
            self.logger.error(f"Error drawing guidance arrow: {e}")
    
    def enable_positioning_guidance(self, target_position: Optional[Tuple[int, int]] = None,
                                  tolerance: Optional[int] = None):
        """
        Enable positioning guidance overlay.
        
        Args:
            target_position: Target position (x, y)
            tolerance: Position tolerance in pixels
        """
        self.guidance_enabled = True
        
        if target_position:
            self.target_position = target_position
        
        if tolerance:
            self.position_tolerance = tolerance
        
        self.logger.info(f"Positioning guidance enabled - Target: {self.target_position}, Tolerance: {self.position_tolerance}")
    
    def disable_positioning_guidance(self):
        """Disable positioning guidance overlay."""
        self.guidance_enabled = False
        self.logger.info("Positioning guidance disabled")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame.
        
        Returns:
            np.ndarray: Captured frame or None if failed
        """
        try:
            if not self.active or not self.camera:
                return None
            
            ret, frame = self.camera.read()
            
            if ret:
                self.current_frame = frame.copy()
                return frame
            else:
                self.logger.warning("Failed to capture frame")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame.
        
        Returns:
            np.ndarray: Current frame or None
        """
        return self.current_frame.copy() if self.current_frame is not None else None
    
    def save_frame(self, filename: str, frame: Optional[np.ndarray] = None) -> bool:
        """
        Save frame to file.
        
        Args:
            filename: Output filename
            frame: Frame to save (uses current frame if None)
            
        Returns:
            bool: True if saved successfully
        """
        try:
            frame_to_save = frame if frame is not None else self.current_frame
            
            if frame_to_save is None:
                self.logger.error("No frame to save")
                return False
            
            success = cv2.imwrite(filename, frame_to_save)
            
            if success:
                self.logger.info(f"Frame saved to {filename}")
            else:
                self.logger.error(f"Failed to save frame to {filename}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving frame: {e}")
            return False
    
    def is_active(self) -> bool:
        """
        Check if camera is active.
        
        Returns:
            bool: True if camera is active
        """
        return self.active and self.camera is not None and self.camera.isOpened()
    
    def is_healthy(self) -> bool:
        """
        Check camera health.
        
        Returns:
            bool: True if camera is healthy
        """
        if not self.is_active():
            return False
        
        # Check if we're receiving frames
        if self.stats['last_frame_time']:
            time_since_last_frame = (datetime.now() - self.stats['last_frame_time']).total_seconds()
            return time_since_last_frame < 5.0  # Healthy if frame within last 5 seconds
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get camera statistics.
        
        Returns:
            dict: Camera statistics
        """
        stats = self.stats.copy()
        stats.update({
            'active': self.active,
            'running': self.running,
            'device_id': self.device_id,
            'resolution': f"{self.width}x{self.height}",
            'target_fps': self.fps,
            'guidance_enabled': self.guidance_enabled,
            'healthy': self.is_healthy()
        })
        
        return stats
    
    async def shutdown(self):
        """Shutdown camera system."""
        try:
            self.logger.info("Shutting down camera system")
            
            # Stop capture
            await self.stop_capture()
            
            # Release camera
            if self.camera:
                self.camera.release()
                self.camera = None
            
            self.active = False
            
            self.logger.info("Camera system shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during camera shutdown: {e}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_camera_manager():
        """Test camera manager functionality."""
        # Create camera manager
        camera_manager = CameraManager(device_id=0)
        
        # Frame callback for testing
        def frame_callback(frame):
            print(f"Received frame: {frame.shape}")
        
        # Initialize camera
        if await camera_manager.initialize():
            print("Camera initialized successfully")
            
            # Enable positioning guidance
            camera_manager.enable_positioning_guidance()
            
            # Start capture
            if await camera_manager.start_capture(callback=frame_callback):
                print("Camera capture started")
                
                # Run for a while
                print("Running for 10 seconds...")
                await asyncio.sleep(10.0)
                
                # Capture and save a frame
                frame = camera_manager.capture_frame()
                if frame is not None:
                    camera_manager.save_frame("test_frame.jpg", frame)
                
                # Print statistics
                stats = camera_manager.get_statistics()
                print(f"Camera statistics: {stats}")
                
            else:
                print("Failed to start camera capture")
        else:
            print("Failed to initialize camera")
        
        # Shutdown
        await camera_manager.shutdown()
    
    # Run test
    asyncio.run(test_camera_manager())