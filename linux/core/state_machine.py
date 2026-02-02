#!/usr/bin/env python3
"""
Smart Rural Triage Station - System State Machine
=================================================

This module implements the system state machine that manages the different
operational states of the triage station and handles state transitions.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import logging
import time
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Callable
import threading


class SystemState(Enum):
    """
    System operational states.
    
    The triage station operates in different states depending on the current
    activity and user interactions.
    """
    
    # Core operational states
    INITIALIZING = auto()    # System is starting up
    IDLE = auto()           # Ready for examination, waiting for user input
    CALIBRATING = auto()    # Performing system calibration
    EXAMINING = auto()      # Actively capturing and analyzing data
    PROCESSING = auto()     # Processing captured data through ML pipeline
    SHOWING_RESULTS = auto() # Displaying examination results
    ERROR = auto()          # System error state
    MAINTENANCE = auto()    # Maintenance mode
    SHUTDOWN = auto()       # System shutting down
    
    def __str__(self):
        return self.name
    
    def is_operational(self) -> bool:
        """Check if state allows normal operation."""
        return self in [
            SystemState.IDLE,
            SystemState.EXAMINING,
            SystemState.PROCESSING,
            SystemState.SHOWING_RESULTS
        ]
    
    def is_busy(self) -> bool:
        """Check if system is busy and cannot accept new commands."""
        return self in [
            SystemState.INITIALIZING,
            SystemState.CALIBRATING,
            SystemState.EXAMINING,
            SystemState.PROCESSING,
            SystemState.MAINTENANCE,
            SystemState.SHUTDOWN
        ]


class StateTransition:
    """
    Represents a state transition with conditions and actions.
    """
    
    def __init__(self, 
                 from_state: SystemState, 
                 to_state: SystemState,
                 condition: Optional[Callable] = None,
                 action: Optional[Callable] = None,
                 timeout: Optional[float] = None):
        """
        Initialize state transition.
        
        Args:
            from_state: Source state
            to_state: Target state
            condition: Optional condition function that must return True
            action: Optional action to execute during transition
            timeout: Optional timeout for automatic transition
        """
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.action = action
        self.timeout = timeout
    
    def can_transition(self, context: Dict[str, Any] = None) -> bool:
        """
        Check if transition is allowed.
        
        Args:
            context: Optional context data for condition evaluation
            
        Returns:
            bool: True if transition is allowed
        """
        if self.condition is None:
            return True
        
        try:
            return self.condition(context or {})
        except Exception:
            return False
    
    def execute_action(self, context: Dict[str, Any] = None):
        """
        Execute transition action.
        
        Args:
            context: Optional context data for action execution
        """
        if self.action:
            try:
                self.action(context or {})
            except Exception as e:
                logging.error(f"Error executing transition action: {e}")


class SystemStateMachine:
    """
    System state machine implementation.
    
    Manages system states, transitions, and associated data. Provides
    thread-safe state management with event handling and automatic
    timeout transitions.
    """
    
    def __init__(self):
        """Initialize the state machine."""
        self.current_state = SystemState.INITIALIZING
        self.previous_state = None
        self.state_data = {}
        self.state_history = []
        self.transitions = {}
        self.state_enter_callbacks = {}
        self.state_exit_callbacks = {}
        self.state_enter_time = time.time()
        self.lock = threading.RLock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize valid transitions
        self._setup_transitions()
        
        self.logger.info("State machine initialized")
    
    def _setup_transitions(self):
        """Setup valid state transitions and their conditions."""
        
        # Define all valid transitions
        valid_transitions = [
            # From INITIALIZING
            (SystemState.INITIALIZING, SystemState.IDLE),
            (SystemState.INITIALIZING, SystemState.ERROR),
            
            # From IDLE
            (SystemState.IDLE, SystemState.CALIBRATING),
            (SystemState.IDLE, SystemState.EXAMINING),
            (SystemState.IDLE, SystemState.MAINTENANCE),
            (SystemState.IDLE, SystemState.ERROR),
            (SystemState.IDLE, SystemState.SHUTDOWN),
            
            # From CALIBRATING
            (SystemState.CALIBRATING, SystemState.IDLE),
            (SystemState.CALIBRATING, SystemState.ERROR),
            
            # From EXAMINING
            (SystemState.EXAMINING, SystemState.PROCESSING),
            (SystemState.EXAMINING, SystemState.IDLE),  # Cancel examination
            (SystemState.EXAMINING, SystemState.ERROR),
            
            # From PROCESSING
            (SystemState.PROCESSING, SystemState.SHOWING_RESULTS),
            (SystemState.PROCESSING, SystemState.ERROR),
            
            # From SHOWING_RESULTS
            (SystemState.SHOWING_RESULTS, SystemState.IDLE),
            (SystemState.SHOWING_RESULTS, SystemState.ERROR),
            
            # From ERROR
            (SystemState.ERROR, SystemState.IDLE),
            (SystemState.ERROR, SystemState.MAINTENANCE),
            (SystemState.ERROR, SystemState.SHUTDOWN),
            
            # From MAINTENANCE
            (SystemState.MAINTENANCE, SystemState.IDLE),
            (SystemState.MAINTENANCE, SystemState.ERROR),
            (SystemState.MAINTENANCE, SystemState.SHUTDOWN),
            
            # To SHUTDOWN (from any state)
            (SystemState.INITIALIZING, SystemState.SHUTDOWN),
            (SystemState.IDLE, SystemState.SHUTDOWN),
            (SystemState.CALIBRATING, SystemState.SHUTDOWN),
            (SystemState.EXAMINING, SystemState.SHUTDOWN),
            (SystemState.PROCESSING, SystemState.SHUTDOWN),
            (SystemState.SHOWING_RESULTS, SystemState.SHUTDOWN),
            (SystemState.ERROR, SystemState.SHUTDOWN),
            (SystemState.MAINTENANCE, SystemState.SHUTDOWN),
        ]
        
        # Create transition objects
        for from_state, to_state in valid_transitions:
            if from_state not in self.transitions:
                self.transitions[from_state] = []
            
            # Add conditions for specific transitions
            condition = None
            action = None
            timeout = None
            
            # Examination start condition
            if from_state == SystemState.IDLE and to_state == SystemState.EXAMINING:
                condition = self._can_start_examination
                action = self._on_examination_start
            
            # Processing completion condition
            elif from_state == SystemState.PROCESSING and to_state == SystemState.SHOWING_RESULTS:
                condition = self._processing_complete
                action = self._on_results_ready
            
            # Auto-return to idle from results
            elif from_state == SystemState.SHOWING_RESULTS and to_state == SystemState.IDLE:
                timeout = 10.0  # Auto-return after 10 seconds
                action = self._on_return_to_idle
            
            # Error recovery conditions
            elif from_state == SystemState.ERROR and to_state == SystemState.IDLE:
                condition = self._error_resolved
                action = self._on_error_recovery
            
            transition = StateTransition(
                from_state=from_state,
                to_state=to_state,
                condition=condition,
                action=action,
                timeout=timeout
            )
            
            self.transitions[from_state].append(transition)
    
    def transition_to(self, new_state: SystemState, context: Dict[str, Any] = None) -> bool:
        """
        Attempt to transition to a new state.
        
        Args:
            new_state: Target state
            context: Optional context data
            
        Returns:
            bool: True if transition was successful
        """
        with self.lock:
            # Check if transition is valid
            if not self._is_valid_transition(self.current_state, new_state):
                self.logger.warning(
                    f"Invalid transition from {self.current_state} to {new_state}"
                )
                return False
            
            # Find the transition
            transition = self._find_transition(self.current_state, new_state)
            if not transition:
                self.logger.error(
                    f"No transition found from {self.current_state} to {new_state}"
                )
                return False
            
            # Check transition condition
            if not transition.can_transition(context):
                self.logger.warning(
                    f"Transition condition failed for {self.current_state} -> {new_state}"
                )
                return False
            
            # Execute state exit callbacks
            self._execute_state_exit_callbacks(self.current_state, context)
            
            # Record state history
            self.state_history.append({
                'from_state': self.current_state,
                'to_state': new_state,
                'timestamp': datetime.now(),
                'context': context
            })
            
            # Update states
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_enter_time = time.time()
            
            # Execute transition action
            transition.execute_action(context)
            
            # Execute state enter callbacks
            self._execute_state_enter_callbacks(new_state, context)
            
            self.logger.info(f"State transition: {self.previous_state} -> {self.current_state}")
            return True
    
    def _is_valid_transition(self, from_state: SystemState, to_state: SystemState) -> bool:
        """Check if a transition is valid."""
        if from_state not in self.transitions:
            return False
        
        return any(
            transition.to_state == to_state 
            for transition in self.transitions[from_state]
        )
    
    def _find_transition(self, from_state: SystemState, to_state: SystemState) -> Optional[StateTransition]:
        """Find a specific transition."""
        if from_state not in self.transitions:
            return None
        
        for transition in self.transitions[from_state]:
            if transition.to_state == to_state:
                return transition
        
        return None
    
    def process(self):
        """
        Process the state machine.
        
        This should be called regularly to handle automatic transitions
        and timeout-based state changes.
        """
        with self.lock:
            current_time = time.time()
            time_in_state = current_time - self.state_enter_time
            
            # Check for timeout-based transitions
            if self.current_state in self.transitions:
                for transition in self.transitions[self.current_state]:
                    if (transition.timeout and 
                        time_in_state >= transition.timeout and
                        transition.can_transition()):
                        
                        self.logger.info(
                            f"Automatic transition due to timeout: "
                            f"{self.current_state} -> {transition.to_state}"
                        )
                        self.transition_to(transition.to_state)
                        break
    
    def get_valid_transitions(self) -> List[SystemState]:
        """
        Get list of valid transitions from current state.
        
        Returns:
            List of valid target states
        """
        with self.lock:
            if self.current_state not in self.transitions:
                return []
            
            return [
                transition.to_state 
                for transition in self.transitions[self.current_state]
                if transition.can_transition()
            ]
    
    def set_data(self, key: str, value: Any):
        """
        Set state-associated data.
        
        Args:
            key: Data key
            value: Data value
        """
        with self.lock:
            self.state_data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get state-associated data.
        
        Args:
            key: Data key
            default: Default value if key not found
            
        Returns:
            Data value or default
        """
        with self.lock:
            return self.state_data.get(key, default)
    
    def clear_data(self, key: str = None):
        """
        Clear state data.
        
        Args:
            key: Specific key to clear, or None to clear all
        """
        with self.lock:
            if key is None:
                self.state_data.clear()
            elif key in self.state_data:
                del self.state_data[key]
    
    def register_state_enter_callback(self, state: SystemState, callback: Callable):
        """
        Register callback for state entry.
        
        Args:
            state: State to monitor
            callback: Callback function
        """
        if state not in self.state_enter_callbacks:
            self.state_enter_callbacks[state] = []
        self.state_enter_callbacks[state].append(callback)
    
    def register_state_exit_callback(self, state: SystemState, callback: Callable):
        """
        Register callback for state exit.
        
        Args:
            state: State to monitor
            callback: Callback function
        """
        if state not in self.state_exit_callbacks:
            self.state_exit_callbacks[state] = []
        self.state_exit_callbacks[state].append(callback)
    
    def _execute_state_enter_callbacks(self, state: SystemState, context: Dict[str, Any]):
        """Execute callbacks for state entry."""
        if state in self.state_enter_callbacks:
            for callback in self.state_enter_callbacks[state]:
                try:
                    callback(state, context)
                except Exception as e:
                    self.logger.error(f"Error in state enter callback: {e}")
    
    def _execute_state_exit_callbacks(self, state: SystemState, context: Dict[str, Any]):
        """Execute callbacks for state exit."""
        if state in self.state_exit_callbacks:
            for callback in self.state_exit_callbacks[state]:
                try:
                    callback(state, context)
                except Exception as e:
                    self.logger.error(f"Error in state exit callback: {e}")
    
    def get_time_in_state(self) -> float:
        """
        Get time spent in current state.
        
        Returns:
            Time in seconds
        """
        with self.lock:
            return time.time() - self.state_enter_time
    
    def get_state_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent state history.
        
        Args:
            limit: Maximum number of history entries
            
        Returns:
            List of state transition records
        """
        with self.lock:
            return self.state_history[-limit:] if self.state_history else []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current state machine status.
        
        Returns:
            Status dictionary
        """
        with self.lock:
            return {
                'current_state': self.current_state.name,
                'previous_state': self.previous_state.name if self.previous_state else None,
                'time_in_state': self.get_time_in_state(),
                'valid_transitions': [state.name for state in self.get_valid_transitions()],
                'is_operational': self.current_state.is_operational(),
                'is_busy': self.current_state.is_busy(),
                'data_keys': list(self.state_data.keys()),
                'history_count': len(self.state_history)
            }
    
    # Transition condition methods
    def _can_start_examination(self, context: Dict[str, Any]) -> bool:
        """Check if examination can be started."""
        # Check if all required components are ready
        sensor_data = self.get_data('latest_sensor_data', {})
        
        # Check distance sensor
        distance_data = sensor_data.get('distance', {})
        if not distance_data.get('valid', False):
            return False
        
        # Check movement sensor (patient should be still)
        movement_data = sensor_data.get('movement', {})
        if movement_data.get('detected', True):  # Default to True for safety
            return False
        
        # Check if mode is selected
        knob_data = sensor_data.get('knob', {})
        mode = knob_data.get('mode', -1)
        if mode < 0 or mode > 2:
            return False
        
        return True
    
    def _processing_complete(self, context: Dict[str, Any]) -> bool:
        """Check if audio processing is complete."""
        return self.get_data('processing_complete', False)
    
    def _error_resolved(self, context: Dict[str, Any]) -> bool:
        """Check if error condition is resolved."""
        return self.get_data('error_resolved', False)
    
    # Transition action methods
    def _on_examination_start(self, context: Dict[str, Any]):
        """Action when examination starts."""
        self.logger.info("Examination started")
        self.set_data('examination_start_time', time.time())
        self.clear_data('processing_complete')
        self.clear_data('examination_results')
    
    def _on_results_ready(self, context: Dict[str, Any]):
        """Action when results are ready."""
        self.logger.info("Results ready for display")
        self.set_data('results_display_time', time.time())
    
    def _on_return_to_idle(self, context: Dict[str, Any]):
        """Action when returning to idle state."""
        self.logger.info("Returning to idle state")
        self.clear_data('examination_start_time')
        self.clear_data('results_display_time')
        self.clear_data('processing_complete')
    
    def _on_error_recovery(self, context: Dict[str, Any]):
        """Action when recovering from error."""
        self.logger.info("Recovering from error state")
        self.clear_data('error_resolved')
        self.clear_data('error_message')
    
    def force_state(self, new_state: SystemState, reason: str = "Manual override"):
        """
        Force transition to a new state (emergency use only).
        
        Args:
            new_state: Target state
            reason: Reason for forced transition
        """
        with self.lock:
            self.logger.warning(f"Forced state transition to {new_state}: {reason}")
            
            # Record in history
            self.state_history.append({
                'from_state': self.current_state,
                'to_state': new_state,
                'timestamp': datetime.now(),
                'forced': True,
                'reason': reason
            })
            
            # Update state
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_enter_time = time.time()
    
    def reset(self):
        """Reset state machine to initial state."""
        with self.lock:
            self.logger.info("Resetting state machine")
            
            self.current_state = SystemState.INITIALIZING
            self.previous_state = None
            self.state_data.clear()
            self.state_history.clear()
            self.state_enter_time = time.time()


# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create state machine
    sm = SystemStateMachine()
    
    # Test basic transitions
    print(f"Initial state: {sm.current_state}")
    print(f"Valid transitions: {[s.name for s in sm.get_valid_transitions()]}")
    
    # Transition to idle
    sm.transition_to(SystemState.IDLE)
    print(f"Current state: {sm.current_state}")
    
    # Set some test data
    sm.set_data('latest_sensor_data', {
        'distance': {'valid': True, 'in_range': True},
        'movement': {'detected': False},
        'knob': {'mode': 1}
    })
    
    # Try to start examination
    if sm.transition_to(SystemState.EXAMINING):
        print("Examination started successfully")
        
        # Simulate processing
        time.sleep(1)
        sm.set_data('processing_complete', True)
        
        if sm.transition_to(SystemState.PROCESSING):
            print("Processing state entered")
            
            # Simulate processing completion
            time.sleep(1)
            if sm.transition_to(SystemState.SHOWING_RESULTS):
                print("Results displayed")
                
                # Wait for auto-return to idle
                time.sleep(2)
                sm.process()  # Process timeout
                print(f"Final state: {sm.current_state}")
    
    # Print status
    status = sm.get_status()
    print(f"State machine status: {status}")
    
    # Print history
    history = sm.get_state_history()
    print(f"State history: {len(history)} transitions")