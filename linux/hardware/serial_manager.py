#!/usr/bin/env python3
"""
Smart Rural Triage Station - Serial Communication Manager
=========================================================

This module handles serial communication with the Arduino MCU side,
including message parsing, protocol handling, and connection management.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import asyncio
import json
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import serial
import serial.tools.list_ports
from queue import Queue, Empty


class SerialProtocol:
    """
    Serial communication protocol handler.
    
    Defines the message format and protocol for communication
    between Linux and MCU sides.
    """
    
    # Message types
    SENSOR_DATA = "sensor_data"
    ERROR_REPORT = "error_report"
    HEARTBEAT = "heartbeat"
    STARTUP = "startup"
    CONTROL_COMMAND = "control_command"
    SYSTEM_STATUS = "system_status"
    CALIBRATION_CMD = "calibration_cmd"
    CONFIG_UPDATE = "config_update"
    RESET_COMMAND = "reset_command"
    
    @staticmethod
    def create_message(message_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a protocol message.
        
        Args:
            message_type: Type of message
            data: Message data
            
        Returns:
            dict: Formatted message
        """
        return {
            'timestamp': int(time.time() * 1000),
            'message_type': message_type,
            'data': data
        }
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        """
        Validate message format.
        
        Args:
            message: Message to validate
            
        Returns:
            bool: True if valid
        """
        required_fields = ['timestamp', 'message_type']
        return all(field in message for field in required_fields)


class SerialManager:
    """
    Serial communication manager.
    
    Handles all serial communication with the MCU, including
    connection management, message queuing, and error recovery.
    """
    
    def __init__(self, 
                 port: str = '/dev/ttyACM0',
                 baud_rate: int = 115200,
                 timeout: float = 1.0,
                 reconnect_interval: float = 5.0):
        """
        Initialize serial manager.
        
        Args:
            port: Serial port path
            baud_rate: Communication baud rate
            timeout: Read timeout in seconds
            reconnect_interval: Reconnection attempt interval
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.reconnect_interval = reconnect_interval
        
        # Serial connection
        self.serial_connection = None
        self.connected = False
        
        # Message handling
        self.message_handlers = {}
        self.send_queue = Queue()
        self.receive_queue = Queue()
        
        # Threading
        self.send_thread = None
        self.receive_thread = None
        self.running = False
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'reconnections': 0,
            'last_message_time': None,
            'connection_time': None
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Serial manager initialized for {port} at {baud_rate} baud")
    
    async def initialize(self) -> bool:
        """
        Initialize serial communication.
        
        Returns:
            bool: True if successful
        """
        try:
            # Attempt to connect
            if not await self._connect():
                return False
            
            # Start communication threads
            self._start_threads()
            
            self.logger.info("Serial communication initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Serial initialization failed: {e}")
            return False
    
    async def _connect(self) -> bool:
        """
        Establish serial connection.
        
        Returns:
            bool: True if connected successfully
        """
        try:
            # Auto-detect port if needed
            if not self.port or self.port == 'auto':
                detected_port = self._detect_arduino_port()
                if detected_port:
                    self.port = detected_port
                    self.logger.info(f"Auto-detected Arduino port: {self.port}")
                else:
                    self.logger.error("Could not auto-detect Arduino port")
                    return False
            
            # Create serial connection
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # Wait for Arduino to initialize
            await asyncio.sleep(2.0)
            
            # Clear any pending data
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            self.connected = True
            self.stats['connection_time'] = datetime.now()
            
            self.logger.info(f"Serial connection established: {self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.port}: {e}")
            self.connected = False
            return False
    
    def _detect_arduino_port(self) -> Optional[str]:
        """
        Auto-detect Arduino port.
        
        Returns:
            str: Detected port path or None
        """
        try:
            ports = serial.tools.list_ports.comports()
            
            # Look for Arduino-like devices
            arduino_keywords = ['arduino', 'uno', 'ch340', 'cp210', 'ftdi']
            
            for port in ports:
                port_info = f"{port.description} {port.manufacturer}".lower()
                
                if any(keyword in port_info for keyword in arduino_keywords):
                    self.logger.info(f"Found potential Arduino port: {port.device} ({port.description})")
                    return port.device
            
            # If no Arduino-specific port found, try common ports
            common_ports = ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyACM1', '/dev/ttyUSB1']
            for port_path in common_ports:
                try:
                    test_serial = serial.Serial(port_path, self.baud_rate, timeout=0.1)
                    test_serial.close()
                    self.logger.info(f"Found working serial port: {port_path}")
                    return port_path
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting Arduino port: {e}")
            return None
    
    def _start_threads(self):
        """Start communication threads."""
        self.running = True
        
        # Send thread
        self.send_thread = threading.Thread(
            target=self._send_loop,
            name="SerialSendThread",
            daemon=True
        )
        self.send_thread.start()
        
        # Receive thread
        self.receive_thread = threading.Thread(
            target=self._receive_loop,
            name="SerialReceiveThread",
            daemon=True
        )
        self.receive_thread.start()
        
        self.logger.info("Serial communication threads started")
    
    def _send_loop(self):
        """Send thread main loop."""
        self.logger.info("Serial send thread started")
        
        while self.running:
            try:
                # Get message from queue (with timeout)
                try:
                    message = self.send_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Send message if connected
                if self.connected and self.serial_connection:
                    self._send_message_raw(message)
                else:
                    self.logger.warning("Cannot send message - not connected")
                
                self.send_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in send loop: {e}")
                self.stats['errors'] += 1
    
    def _receive_loop(self):
        """Receive thread main loop."""
        self.logger.info("Serial receive thread started")
        
        while self.running:
            try:
                if not self.connected or not self.serial_connection:
                    time.sleep(1.0)
                    continue
                
                # Read line from serial
                try:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    
                    if line:
                        self._process_received_message(line)
                        
                except serial.SerialTimeoutException:
                    # Timeout is normal, continue
                    continue
                except serial.SerialException as e:
                    self.logger.error(f"Serial error: {e}")
                    self.connected = False
                    asyncio.create_task(self._handle_disconnection())
                    
            except Exception as e:
                self.logger.error(f"Error in receive loop: {e}")
                self.stats['errors'] += 1
                time.sleep(1.0)
    
    def _send_message_raw(self, message: Dict[str, Any]):
        """
        Send raw message over serial.
        
        Args:
            message: Message to send
        """
        try:
            # Convert to JSON and send
            json_message = json.dumps(message, separators=(',', ':'))
            self.serial_connection.write((json_message + '\n').encode('utf-8'))
            self.serial_connection.flush()
            
            self.stats['messages_sent'] += 1
            self.stats['last_message_time'] = datetime.now()
            
            self.logger.debug(f"Sent message: {message['message_type']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self.stats['errors'] += 1
            self.connected = False
    
    def _process_received_message(self, line: str):
        """
        Process received message line.
        
        Args:
            line: Raw message line
        """
        try:
            # Parse JSON
            message = json.loads(line)
            
            # Validate message
            if not SerialProtocol.validate_message(message):
                self.logger.warning(f"Invalid message format: {line}")
                return
            
            # Update statistics
            self.stats['messages_received'] += 1
            self.stats['last_message_time'] = datetime.now()
            
            # Get message type
            message_type = message.get('message_type')
            
            # Call registered handler
            if message_type in self.message_handlers:
                try:
                    self.message_handlers[message_type](message)
                except Exception as e:
                    self.logger.error(f"Error in message handler for {message_type}: {e}")
            else:
                self.logger.debug(f"No handler for message type: {message_type}")
            
            # Add to receive queue for other consumers
            self.receive_queue.put(message)
            
            self.logger.debug(f"Received message: {message_type}")
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON message: {line} - {e}")
            self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f"Error processing received message: {e}")
            self.stats['errors'] += 1
    
    async def send_message(self, message: Dict[str, Any]):
        """
        Send message to MCU.
        
        Args:
            message: Message to send
        """
        try:
            # Add to send queue
            self.send_queue.put(message)
            
        except Exception as e:
            self.logger.error(f"Failed to queue message: {e}")
    
    def send_control_command(self, commands: Dict[str, Any]):
        """
        Send control command to MCU.
        
        Args:
            commands: Control commands
        """
        message = SerialProtocol.create_message(
            SerialProtocol.CONTROL_COMMAND,
            {'commands': commands}
        )
        asyncio.create_task(self.send_message(message))
    
    def send_system_status(self, status: Dict[str, Any]):
        """
        Send system status to MCU.
        
        Args:
            status: System status
        """
        message = SerialProtocol.create_message(
            SerialProtocol.SYSTEM_STATUS,
            {'status': status}
        )
        asyncio.create_task(self.send_message(message))
    
    def send_calibration_command(self, command: str, parameters: Dict[str, Any] = None):
        """
        Send calibration command to MCU.
        
        Args:
            command: Calibration command
            parameters: Optional parameters
        """
        data = {'command': command}
        if parameters:
            data['parameters'] = parameters
        
        message = SerialProtocol.create_message(
            SerialProtocol.CALIBRATION_CMD,
            data
        )
        asyncio.create_task(self.send_message(message))
    
    def set_message_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Set message handler for specific message type.
        
        Args:
            message_type: Message type to handle
            handler: Handler function
        """
        self.message_handlers[message_type] = handler
        self.logger.debug(f"Registered handler for message type: {message_type}")
    
    def remove_message_handler(self, message_type: str):
        """
        Remove message handler.
        
        Args:
            message_type: Message type
        """
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            self.logger.debug(f"Removed handler for message type: {message_type}")
    
    async def _handle_disconnection(self):
        """Handle serial disconnection."""
        self.logger.warning("Serial connection lost - attempting reconnection")
        
        # Close current connection
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None
        
        self.connected = False
        
        # Attempt reconnection
        await self.reconnect()
    
    async def reconnect(self) -> bool:
        """
        Attempt to reconnect to serial port.
        
        Returns:
            bool: True if reconnected successfully
        """
        self.logger.info("Attempting serial reconnection...")
        
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts and self.running:
            attempt += 1
            
            try:
                if await self._connect():
                    self.stats['reconnections'] += 1
                    self.logger.info(f"Serial reconnection successful (attempt {attempt})")
                    return True
                
            except Exception as e:
                self.logger.debug(f"Reconnection attempt {attempt} failed: {e}")
            
            # Wait before next attempt
            await asyncio.sleep(self.reconnect_interval)
        
        self.logger.error(f"Failed to reconnect after {max_attempts} attempts")
        return False
    
    async def reset_connection(self):
        """Reset serial connection."""
        self.logger.info("Resetting serial connection")
        
        # Close current connection
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None
        
        self.connected = False
        
        # Wait a moment
        await asyncio.sleep(1.0)
        
        # Reconnect
        await self.reconnect()
    
    def is_connected(self) -> bool:
        """
        Check if serial connection is active.
        
        Returns:
            bool: True if connected
        """
        return self.connected and self.serial_connection is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get communication statistics.
        
        Returns:
            dict: Statistics
        """
        stats = self.stats.copy()
        stats['connected'] = self.connected
        stats['port'] = self.port
        stats['baud_rate'] = self.baud_rate
        stats['queue_size'] = self.send_queue.qsize()
        
        return stats
    
    def get_received_messages(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent received messages.
        
        Args:
            max_messages: Maximum number of messages to return
            
        Returns:
            list: Recent messages
        """
        messages = []
        count = 0
        
        while count < max_messages:
            try:
                message = self.receive_queue.get_nowait()
                messages.append(message)
                count += 1
            except Empty:
                break
        
        return messages
    
    async def shutdown(self):
        """Shutdown serial communication."""
        try:
            self.logger.info("Shutting down serial communication")
            
            self.running = False
            
            # Wait for threads to finish
            if self.send_thread and self.send_thread.is_alive():
                self.send_thread.join(timeout=5.0)
            
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=5.0)
            
            # Close serial connection
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None
            
            self.connected = False
            
            self.logger.info("Serial communication shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during serial shutdown: {e}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_serial_manager():
        """Test serial manager functionality."""
        # Create serial manager
        serial_manager = SerialManager(port='auto')  # Auto-detect port
        
        # Message handlers
        def handle_sensor_data(message):
            print(f"Sensor data: {message['data']}")
        
        def handle_heartbeat(message):
            print(f"MCU heartbeat: {message['data']}")
        
        def handle_error(message):
            print(f"MCU error: {message['data']}")
        
        # Register handlers
        serial_manager.set_message_handler('sensor_data', handle_sensor_data)
        serial_manager.set_message_handler('heartbeat', handle_heartbeat)
        serial_manager.set_message_handler('error_report', handle_error)
        
        # Initialize
        if await serial_manager.initialize():
            print("Serial manager initialized successfully")
            
            # Send test commands
            await asyncio.sleep(2.0)  # Wait for MCU to be ready
            
            # Test control command
            serial_manager.send_control_command({
                'led': {'state': 'ON'},
                'buzzer': {'state': 'ON', 'frequency': 1000, 'duration': 200}
            })
            
            # Test system status
            serial_manager.send_system_status({
                'state': 'IDLE',
                'progress': 0
            })
            
            # Run for a while to receive messages
            print("Running for 30 seconds to test communication...")
            await asyncio.sleep(30.0)
            
            # Print statistics
            stats = serial_manager.get_statistics()
            print(f"Communication statistics: {stats}")
            
        else:
            print("Failed to initialize serial manager")
        
        # Shutdown
        await serial_manager.shutdown()
    
    # Run test
    asyncio.run(test_serial_manager())