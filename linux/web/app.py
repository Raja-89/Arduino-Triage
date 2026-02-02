#!/usr/bin/env python3
"""
Smart Rural Triage Station - Web Application
===========================================

This module provides the Flask web application for the triage station
interface, including real-time monitoring, examination control, and results display.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import logging
import asyncio
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os


def create_web_app(system_manager, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """
    Create and configure Flask web application.
    
    Args:
        system_manager: System manager instance
        host: Host address
        port: Port number
        debug: Debug mode
        
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'triage-station-secret-key'
    
    # Initialize SocketIO for real-time communication
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Store system manager reference
    app.system_manager = system_manager
    app.socketio = socketio
    
    # Setup logging
    logger = logging.getLogger(__name__)
    
    # ============================================================================
    # WEB ROUTES
    # ============================================================================
    
    @app.route('/')
    def index():
        """Main dashboard page."""
        try:
            # Get system status
            system_status = system_manager.get_system_status()
            
            return render_template('index.html', 
                                 system_status=system_status,
                                 page_title='Smart Rural Triage Station')
        except Exception as e:
            logger.error(f"Error loading index page: {e}")
            return render_template('error.html', error=str(e))
    
    @app.route('/examination')
    def examination():
        """Examination control page."""
        try:
            system_status = system_manager.get_system_status()
            
            return render_template('examination.html',
                                 system_status=system_status,
                                 page_title='Medical Examination')
        except Exception as e:
            logger.error(f"Error loading examination page: {e}")
            return render_template('error.html', error=str(e))
    
    @app.route('/results')
    def results():
        """Results display page."""
        try:
            system_status = system_manager.get_system_status()
            examination_results = system_status.get('examination_results', {})
            
            return render_template('results.html',
                                 examination_results=examination_results,
                                 system_status=system_status,
                                 page_title='Examination Results')
        except Exception as e:
            logger.error(f"Error loading results page: {e}")
            return render_template('error.html', error=str(e))
    
    @app.route('/calibration')
    def calibration():
        """Calibration management page."""
        try:
            system_status = system_manager.get_system_status()
            
            # Get calibration status
            calibration_status = {}
            if hasattr(system_manager, 'calibration_manager') and system_manager.calibration_manager:
                calibration_status = system_manager.calibration_manager.get_calibration_status()
            
            return render_template('calibration.html',
                                 calibration_status=calibration_status,
                                 system_status=system_status,
                                 page_title='System Calibration')
        except Exception as e:
            logger.error(f"Error loading calibration page: {e}")
            return render_template('error.html', error=str(e))
    
    @app.route('/settings')
    def settings():
        """System settings page."""
        try:
            system_status = system_manager.get_system_status()
            
            return render_template('settings.html',
                                 system_status=system_status,
                                 page_title='System Settings')
        except Exception as e:
            logger.error(f"Error loading settings page: {e}")
            return render_template('error.html', error=str(e))
    
    # ============================================================================
    # API ROUTES
    # ============================================================================
    
    @app.route('/api/status')
    def api_status():
        """Get system status API."""
        try:
            status = system_manager.get_system_status()
            return jsonify({
                'success': True,
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/examination/start', methods=['POST'])
    def api_start_examination():
        """Start examination API."""
        try:
            data = request.get_json()
            mode = data.get('mode', 'heart')
            
            # Validate mode
            if mode not in ['heart', 'lung', 'both']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid examination mode'
                }), 400
            
            # Start examination
            result = asyncio.run(system_manager.start_examination(mode))
            
            return jsonify({
                'success': result.get('success', False),
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error starting examination: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/examination/stop', methods=['POST'])
    def api_stop_examination():
        """Stop examination API."""
        try:
            result = asyncio.run(system_manager.stop_examination())
            
            return jsonify({
                'success': result.get('success', False),
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error stopping examination: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/calibration/start', methods=['POST'])
    def api_start_calibration():
        """Start calibration API."""
        try:
            data = request.get_json()
            component = data.get('component', 'all')  # 'all', 'audio', 'sensors'
            
            if not hasattr(system_manager, 'calibration_manager') or not system_manager.calibration_manager:
                return jsonify({
                    'success': False,
                    'error': 'Calibration manager not available'
                }), 500
            
            # Start appropriate calibration
            if component == 'all':
                result = asyncio.run(system_manager.calibration_manager.run_full_calibration())
            elif component == 'audio':
                result = asyncio.run(system_manager.calibration_manager.calibrate_audio_only())
            elif component == 'sensors':
                result = asyncio.run(system_manager.calibration_manager.calibrate_sensors_only())
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid calibration component'
                }), 400
            
            return jsonify({
                'success': result.get('success', False),
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error starting calibration: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/calibration/status')
    def api_calibration_status():
        """Get calibration status API."""
        try:
            if not hasattr(system_manager, 'calibration_manager') or not system_manager.calibration_manager:
                return jsonify({
                    'success': False,
                    'error': 'Calibration manager not available'
                }), 500
            
            status = system_manager.calibration_manager.get_calibration_status()
            
            return jsonify({
                'success': True,
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting calibration status: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/sensor-data')
    def api_sensor_data():
        """Get latest sensor data API."""
        try:
            system_status = system_manager.get_system_status()
            sensor_data = system_status.get('latest_sensor_data', {})
            
            return jsonify({
                'success': True,
                'data': sensor_data,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting sensor data: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # ============================================================================
    # WEBSOCKET EVENTS
    # ============================================================================
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        logger.info(f"Client connected: {request.sid}")
        
        # Send initial system status
        try:
            status = system_manager.get_system_status()
            emit('system_status', {
                'success': True,
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending initial status: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('request_status')
    def handle_request_status():
        """Handle status request."""
        try:
            status = system_manager.get_system_status()
            emit('system_status', {
                'success': True,
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error handling status request: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('start_examination')
    def handle_start_examination(data):
        """Handle examination start request."""
        try:
            mode = data.get('mode', 'heart')
            result = asyncio.run(system_manager.start_examination(mode))
            
            emit('examination_started', {
                'success': result.get('success', False),
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
            
            # Broadcast to all clients
            socketio.emit('system_status_update', {
                'state': 'EXAMINING',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling examination start: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('stop_examination')
    def handle_stop_examination():
        """Handle examination stop request."""
        try:
            result = asyncio.run(system_manager.stop_examination())
            
            emit('examination_stopped', {
                'success': result.get('success', False),
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
            
            # Broadcast to all clients
            socketio.emit('system_status_update', {
                'state': 'IDLE',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling examination stop: {e}")
            emit('error', {'message': str(e)})
    
    # ============================================================================
    # BACKGROUND TASKS
    # ============================================================================
    
    def start_background_tasks():
        """Start background tasks for real-time updates."""
        def status_broadcast_loop():
            """Background loop to broadcast system status."""
            while True:
                try:
                    if socketio:
                        status = system_manager.get_system_status()
                        socketio.emit('system_status_update', {
                            'data': status,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    time.sleep(2.0)  # Update every 2 seconds
                    
                except Exception as e:
                    logger.error(f"Error in status broadcast loop: {e}")
                    time.sleep(5.0)
        
        # Start background thread
        status_thread = threading.Thread(
            target=status_broadcast_loop,
            name="WebStatusBroadcast",
            daemon=True
        )
        status_thread.start()
        
        logger.info("Web application background tasks started")
    
    # Start background tasks
    start_background_tasks()
    
    # ============================================================================
    # ERROR HANDLERS
    # ============================================================================
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return render_template('error.html', 
                             error='Page not found',
                             error_code=404), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return render_template('error.html',
                             error='Internal server error',
                             error_code=500), 500
    
    logger.info(f"Web application created - Host: {host}, Port: {port}")
    
    return app


# Example usage and testing
if __name__ == "__main__":
    import logging
    from unittest.mock import Mock
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create mock system manager for testing
    mock_system_manager = Mock()
    mock_system_manager.get_system_status.return_value = {
        'state': 'IDLE',
        'uptime': 3600,
        'error_count': 0,
        'component_status': {
            'serial_manager': True,
            'camera_manager': True,
            'audio_manager': True,
            'inference_engine': True
        }
    }
    
    # Create web app
    app = create_web_app(mock_system_manager, debug=True)
    
    # Run app
    print("Starting web application...")
    print("Open http://localhost:5000 in your browser")
    app.socketio.run(app, host='0.0.0.0', port=5000, debug=True)