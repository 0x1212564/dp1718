      
"""Motor control for the line follower robot"""
import logging
from config import MOTOR_LEFT_PIN, MOTOR_RIGHT_PIN

class MotorController:
    """Controls the robot's motors"""
    
    def __init__(self, board):
        self.board = board
        self.motor_left = None
        self.motor_right = None
        
    def setup(self):
        """Initialize the motors"""
        try:
            self.motor_left = self.board.get_pin(MOTOR_LEFT_PIN)
            self.motor_right = self.board.get_pin(MOTOR_RIGHT_PIN)
            return True
        except Exception as e:
            logging.error(f"Motor setup failed: {e}")
            return False
            
    def set_motor_speed(self, left_speed, right_speed):
        """Set motor speeds with safety limits"""
        try:
            left_speed = max(0, min(1, left_speed))
            right_speed = max(0, min(1, right_speed))
            self.motor_left.write(left_speed)
            self.motor_right.write(right_speed)
            logging.info(f"Left Speed: {left_speed:.2f}, Right Speed: {right_speed:.2f}")
        except Exception as e:
            logging.error(f"Motor control error: {e}")
            try:
                self.motor_left.write(0)
                self.motor_right.write(0)
            except Exception as e:
                logging.error(f"Motor control error: {e}")
                pass
                
    def stop(self):
        """Stop both motors"""
        self.set_motor_speed(0, 0)