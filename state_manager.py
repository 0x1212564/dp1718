"""State management for line following robot"""
import logging
import time

# State definitions
STATE_LINE_FOLLOWING = "LINE_FOLLOWING"
STATE_JUNCTION = "JUNCTION"
STATE_LOST = "LOST"
STATE_FINISHED = "FINISHED"

class StateManager:
    """Manages the robot's state transitions"""
    
    def __init__(self):
        self.current_state = STATE_LINE_FOLLOWING
        self.previous_state = STATE_LINE_FOLLOWING
        self.state_change_time = time.time()
        
    def update_state(self, sensor_readings, sensor_manager, junction_handler, recovery_handler=None):
        """Update the robot's state based on sensor readings"""
        self.previous_state = self.current_state
        
        # Check for junction
        if sensor_manager.detect_junction(sensor_readings):
            if not junction_handler.junction_cooldown_active:
                self.current_state = STATE_JUNCTION
                junction_handler.start_cooldown()
                junction_handler.handled_current_junction = False
        # Check for lost line
        elif sensor_manager.detect_line_lost(sensor_readings):
            self.current_state = STATE_LOST
            if self.previous_state != STATE_LOST:
                recovery_handler.start_recovery()
        # Default to line following
        else:
            self.current_state = STATE_LINE_FOLLOWING
            junction_handler.handled_current_junction = False
        
        # Update junction cooldown
        junction_handler.update_cooldown()
        
        # Log state changes
        if self.current_state != self.previous_state:
            logging.info(f"State changed: {self.previous_state} -> {self.current_state}")
            self.state_change_time = time.time()
            
        return self.current_state
