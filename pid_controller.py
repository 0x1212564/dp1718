"""PID controller for line following"""
import logging
from config import PID_KP, PID_KI, PID_KD, INTEGRAL_CAP, BASE_SPEED

class PIDController:
    """Handles PID calculations for line following"""
    
    def __init__(self):
        self.last_error = 0
        self.integral = 0
        
    def calculate(self, sensors):
        """Calculate motor speeds using PID control"""
        weights = [-2, -1, 0, 1, 2]
        inverted_sensors = [1 - s for s in sensors]
        
        if sum(inverted_sensors) == 0:
            error = self.last_error
        else:
            error = sum(w * s for w, s in zip(weights, inverted_sensors)) / sum(inverted_sensors)
        
        if abs(error) < 0.5:
            self.integral += error
            self.integral = max(-INTEGRAL_CAP, min(INTEGRAL_CAP, self.integral))
        
        derivative = error - self.last_error
        self.last_error = error
        
        adjustment = (PID_KP * error +
                      PID_KI * self.integral +
                      PID_KD * derivative)
        
        logging.info(f"PID: error={error:.3f}, integral={self.integral:.3f}, derivative={derivative:.3f}")
        
        left_speed = BASE_SPEED + adjustment
        right_speed = BASE_SPEED - adjustment
        
        min_speed = BASE_SPEED * 0.3
        left_speed = max(min_speed, min(1.0, left_speed))
        right_speed = max(min_speed, min(1.0, right_speed))
        
        return left_speed, right_speed