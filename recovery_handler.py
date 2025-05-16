"""Line loss recovery for the line follower robot"""
import logging
import time
from config import BASE_SPEED, RECOVERY_SPEED

class RecoveryHandler:
    """Handles line loss recovery strategies"""
    
    def __init__(self):
        self.lost_time = 0
        
    def start_recovery(self):
        """Start the recovery timer"""
        self.lost_time = time.time()
        
    def handle_lost_line(self, last_valid_pattern):
        """Handle recovery when line is lost"""
        recovery_time = time.time() - self.lost_time
        recovery_factor = min(1.0, recovery_time / 2.0)
        
        if last_valid_pattern:
            weights = [-2, -1, 0, 1, 2]
            inverted_sensors = [1 - s for s in last_valid_pattern]
            weighted_sum = sum(w * s for w, s in zip(weights, inverted_sensors))
            
            if weighted_sum < 0:
                logging.info(f"Lost line - recovering left (factor: {recovery_factor:.2f})")
                return 0.0, max(0.4, BASE_SPEED * RECOVERY_SPEED * recovery_factor)
            elif weighted_sum > 0:
                
                logging.info(f"Lost line - recovering right (factor: {recovery_factor:.2f})")
                return max(0.4, BASE_SPEED * RECOVERY_SPEED * recovery_factor), 0.0
        
        logging.info(f"Lost line - searching in place (factor: {recovery_factor:.2f})")
        return max(0.4, BASE_SPEED * RECOVERY_SPEED * recovery_factor), 0.0