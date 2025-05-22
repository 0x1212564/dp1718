"""State management for line following robot"""
import logging
import time

# State definitions
STATE_LINE_FOLLOWING = "LINE_FOLLOWING"
STATE_JUNCTION = "JUNCTION"
STATE_LOST = "LOST"
STATE_FINISHED = "FINISHED"
STATE_CONTINUE_TURNING = "CONTINUE_TURNING"
STATE_CONTINUE_TO_WHITE = "CONTINUE_TO_WHITE"

class StateManager:
    """Manages the robot's state transitions"""
    
    def __init__(self):
        self.current_state = STATE_LINE_FOLLOWING
        self.previous_state = STATE_LINE_FOLLOWING
        self.state_change_time = time.time()
        self.last_turn_direction = None
        self.continue_after_table = False
        
    def update_state(self, sensor_readings, sensor_manager, junction_handler, recovery_handler=None):
        """Update the robot's state based on sensor readings"""
        self.previous_state = self.current_state
        
        # Handle continuation after table
        if self.current_state == STATE_CONTINUE_TURNING:
            # Check if we're back on the line (middle sensor detects line)
            if sensor_readings[len(sensor_readings)//2] == 0:
                logging.info("Line detected. Switching to continue to white state.")
                self.current_state = STATE_CONTINUE_TO_WHITE
            # Otherwise keep turning
            return self.current_state
            
        # Handle continue to white state
        if self.current_state == STATE_CONTINUE_TO_WHITE:
            # Check if all sensors detect white
            if all(s == 1 for s in sensor_readings):
                logging.info("End of line detected (all white). Stopping.")
                self.current_state = STATE_FINISHED
                self.continue_after_table = False
            # Otherwise keep following the line
            return self.current_state
        
        # Check for junction
        if sensor_manager.detect_junction(sensor_readings):
            if not junction_handler.junction_cooldown_active:
                self.current_state = STATE_JUNCTION
                junction_handler.start_cooldown()
                junction_handler.handled_current_junction = False
                
                # Store the last turn direction for later use
                if hasattr(junction_handler, 'current_turn_speeds'):
                    self.last_turn_direction = junction_handler.current_turn_speeds
                
                # Check if we should continue after table
                if junction_handler.junction_count >= len(junction_handler.current_route):
                    self.continue_after_table = True
        # Check for lost line
        elif sensor_manager.detect_line_lost(sensor_readings):
            self.current_state = STATE_LOST
            if self.previous_state != STATE_LOST:
                recovery_handler.start_recovery()
        # Default to line following
        else:
            self.current_state = STATE_LINE_FOLLOWING
            junction_handler.handled_current_junction = False
            
            # Check if we should transition to continue turning state
            if self.continue_after_table and self.previous_state == STATE_JUNCTION:
                logging.info("Continuing in last turning direction until line is found...")
                self.current_state = STATE_CONTINUE_TURNING
                self.continue_after_table = False
        
        # Update junction cooldown
        junction_handler.update_cooldown()
        
        # Log state changes
        if self.current_state != self.previous_state:
            logging.info(f"State changed: {self.previous_state} -> {self.current_state}")
            self.state_change_time = time.time()
            
        return self.current_state
        
    def set_continue_after_table(self, value):
        """Set whether to continue after reaching a table"""
        self.continue_after_table = value
        
    def get_last_turn_direction(self):
        """Get the last turn direction"""
        return self.last_turn_direction