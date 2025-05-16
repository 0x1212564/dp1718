"""Junction detection and handling for the line follower robot"""
import logging
import time
from config import BASE_SPEED, JUNCTION_TURN_FACTOR, JUNCTION_COOLDOWN_TIME

class JunctionHandler:
    """Handles junction detection and navigation"""
    
    def __init__(self):
        self.junction_count = 0
        self.junction_cooldown_active = False
        self.junction_cooldown_start = 0
        self.JUNCTION_COOLDOWN_TIME = JUNCTION_COOLDOWN_TIME
        self.handled_current_junction = False
        self.current_turn_speeds = (0, 0)
        self.current_route = []
        
    def set_route(self, route):
        """Set the current route plan"""
        self.current_route = route if route else []
        self.junction_count = 0
        logging.info(f"New route set: {self.current_route}")
        
    def handle_junction(self, motor_controller=None):
        """Handle behavior at junctions"""
        if self.junction_count < len(self.current_route):
            direction = self.current_route[self.junction_count]
            self.junction_count += 1
            
            logging.info(f"Junction {self.junction_count}: Taking {direction}")
            
            if direction == "LEFT":
                return 0, BASE_SPEED * JUNCTION_TURN_FACTOR
            elif direction == "RIGHT":
                return BASE_SPEED * JUNCTION_TURN_FACTOR, 0
            elif direction == "STRAIGHT":
                return BASE_SPEED, BASE_SPEED
            else:
                return BASE_SPEED, BASE_SPEED
        else:
            logging.info("Route complete!")
            return 0, 0
            
    def start_cooldown(self):
        """Start the junction cooldown timer"""
        self.junction_cooldown_active = True
        self.junction_cooldown_start = time.time()
        logging.info("Junction cooldown started")
        
    def update_cooldown(self):
        """Update the junction cooldown status"""
        if self.junction_cooldown_active and (time.time() - self.junction_cooldown_start) >= self.JUNCTION_COOLDOWN_TIME:
            self.junction_cooldown_active = False
            logging.info("Junction cooldown ended")