import logging
import time
from pyfirmata2 import Arduino, util
from config import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('line_follower.log', mode='w'),
        logging.StreamHandler()
    ]
)

# State definitions
STATE_LINE_FOLLOWING = "LINE_FOLLOWING"
STATE_JUNCTION = "JUNCTION"
STATE_LOST = "LOST"
STATE_FINISHED = "FINISHED"


class SensorManager:
    """Manages the robot's sensors and provides readings"""
    
    def __init__(self, board):
        self.board = board
        self.sensors = {}
        self.sensor_values = {}
        self.prev_readings = [1, 1, 1, 1, 1]
        self.last_valid_pattern = None
        
    def setup(self):
        """Initialize and set up the sensors"""
        try:
            for i in range(5):
                sensor_name = f'sensor_{i}'
                pin = self.board.get_pin(f'a:{i}:i')
                pin.register_callback(self.create_callback(sensor_name))
                pin.enable_reporting()
                self.sensors[sensor_name] = pin
            return True
        except Exception as e:
            logging.error(f"Sensor setup failed: {e}")
            return False
            
    def create_callback(self, sensor_name):
        """Create callback function for sensor reading"""
        def callback(value):
            self.sensor_values[sensor_name] = value
        return callback
        
    def read_sensors(self):
        """Read current sensor values and return binary array"""
        try:
            readings = [
                1 if self.sensor_values.get(f'sensor_{i}', 1) > SENSOR_THRESHOLD else 0
                for i in range(5)
            ]
            self.prev_readings = readings.copy()
            
            # Update last valid pattern if we see something
            if not all(s == 1 for s in readings):
                self.last_valid_pattern = readings.copy()
                
            return readings
        except Exception as e:
            logging.error(f"Sensor reading error: {e}")
            return self.prev_readings.copy()
    @staticmethod
    def detect_junction(sensors):
        """Detect if robot is at a junction"""
        black_count = sum(1 for s in sensors if s == 0)
        return black_count >= MIN_BLACK_SENSORS_JUNCTION
    @staticmethod
    def detect_line_lost(sensors):
        """Detect if line is lost (all sensors see white)"""
        return all(s == 1 for s in sensors)


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


class JunctionHandler:
    """Handles junction detection and navigation"""
    
    def __init__(self):
        self.junction_count = 0
        self.junction_cooldown_active = False
        self.junction_cooldown_start = 0
        self.JUNCTION_COOLDOWN_TIME = 2.0
        self.handled_current_junction = False
        
    def handle_junction(self):
        """Handle behavior at junctions"""
        if self.junction_count < len(ROUTE_PLAN):
            direction = ROUTE_PLAN[self.junction_count]
            self.junction_count += 1
            
           
            logging.info(f"Junction {self.junction_count}: Taking {direction}")
            
            if direction == "LEFT":
                return 0, BASE_SPEED * JUNCTION_TURN_FACTOR
            elif direction == "RIGHT":
                return BASE_SPEED * JUNCTION_TURN_FACTOR, 0
            else:
                return BASE_SPEED, BASE_SPEED
        else:
            logging.info("Route complete!")
            return 0, 0
            
    def start_cooldown(self):
        """Start the junction cooldown timer"""
        self.junction_cooldown_active = True
        self.junction_cooldown_start = time.time()
        self.handled_current_junction = False
        logging.info(f"Junction detected - cooldown active for {self.JUNCTION_COOLDOWN_TIME} seconds")
        
    def update_cooldown(self):
        """Update the junction cooldown status"""
        if self.junction_cooldown_active and (time.time() - self.junction_cooldown_start) >= self.JUNCTION_COOLDOWN_TIME:
            self.junction_cooldown_active = False
            logging.info("Junction cooldown ended")


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


class StateManager:
    """Manages the robot's state transitions"""
    
    def __init__(self):
        self.current_state = STATE_LINE_FOLLOWING
        
    def update_state(self, sensors, sensor_manager, junction_handler, recovery_handler):
        """Update robot state based on sensor readings"""
        junction_handler.update_cooldown()
        
        if self.current_state == STATE_LINE_FOLLOWING:
            if sensor_manager.detect_junction(sensors) and not junction_handler.junction_cooldown_active:
                self.current_state = STATE_JUNCTION
                junction_handler.start_cooldown()
            elif sensor_manager.detect_line_lost(sensors):
                self.current_state = STATE_LOST
                recovery_handler.start_recovery()
                logging.info("Line lost")
        
        elif self.current_state == STATE_JUNCTION:
            if not sensor_manager.detect_junction(sensors) and not sensor_manager.detect_line_lost(sensors):
                self.current_state = STATE_LINE_FOLLOWING
                logging.info("Returning to line following from junction")
        
        elif self.current_state == STATE_LOST:
            if not sensor_manager.detect_line_lost(sensors):
                self.current_state = STATE_LINE_FOLLOWING
                logging.info("Line found - resuming line following")
        
        return self.current_state


class LineFollower:
    """Main class that coordinates the robot's components"""
    
    def __init__(self):
        self.board = None
        self.iterator = None
        self.sensor_manager = None
        self.motor_controller = None
        self.pid_controller = None
        self.junction_handler = None
        self.recovery_handler = None
        self.state_manager = None
        
    def setup(self):
        """Initialize the robot and its components"""
        logging.info("Setting up line follower robot...")
        
        try:
            # Initialize Arduino board
            port = Arduino.AUTODETECT
            self.board = Arduino(port)
            self.iterator = util.Iterator(self.board)
            self.iterator.start()
            time.sleep(1)
            
            # Initialize components
            self.sensor_manager = SensorManager(self.board)
            self.motor_controller = MotorController(self.board)
            self.pid_controller = PIDController()
            self.junction_handler = JunctionHandler()
            self.recovery_handler = RecoveryHandler()
            self.state_manager = StateManager()
            
            # Setup components
            sensor_setup_ok = self.sensor_manager.setup()
            motor_setup_ok = self.motor_controller.setup()
            
            if sensor_setup_ok and motor_setup_ok:
                logging.info("Setup complete. Ready to start.")
                return True
            else:
                logging.error("Setup failed.")
                return False
                
        except Exception as e:
            logging.error(f"Setup failed: {e}")
            return False
            
    def run(self):
        """Main control loop"""
        logging.info("Starting line follower with dynamic junction handling...")
        
        try:
            while True:
                sensor_readings = self.sensor_manager.read_sensors()
                
                current_state = self.state_manager.update_state(
                    sensor_readings, 
                    self.sensor_manager,
                    self.junction_handler,
                    self.recovery_handler
                )
                
                # Display state and sensor readings
                state_str = "█" if current_state == STATE_JUNCTION else (
                    "?" if current_state == STATE_LOST else "-")
                sensors_str = "".join(["█" if s == 0 else "□" for s in sensor_readings])
                logging.info(f"{state_str} [{sensors_str}] State: {current_state}")
                
                # Handle different states
                left_speed, right_speed = 0,0
                if current_state == STATE_LINE_FOLLOWING:
                    left_speed, right_speed = self.pid_controller.calculate(sensor_readings)
                elif current_state == STATE_JUNCTION:
                    if not self.junction_handler.handled_current_junction:
                        self.junction_handler.current_turn_speeds = self.junction_handler.handle_junction(self.motor_controller)
                        self.junction_handler.handled_current_junction = True
                    left_speed, right_speed = self.junction_handler.current_turn_speeds
                elif current_state == STATE_LOST:
                    left_speed, right_speed = self.recovery_handler.handle_lost_line(
                        self.sensor_manager.last_valid_pattern
                    )
                elif current_state == STATE_FINISHED:
                    left_speed, right_speed = 0, 0
                
                self.motor_controller.set_motor_speed(left_speed, right_speed)
                time.sleep(LOOP_DELAY)
                
        except KeyboardInterrupt:
            logging.info("Program stopped by user")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources when program exits."""
        logging.info("Cleaning up resources...")

        try:
            if self.motor_controller:
                self.motor_controller.stop()
        except Exception as e:
            logging.error(f"Error stopping motor controller: {e}")

        try:
            if self.board:
                self.board.exit()
        except Exception as e:
            logging.error(f"Error exiting board: {e}")


# Main entry point
if __name__ == "__main__":
    robot = LineFollower()
    if robot.setup():
        robot.run()
    else:
        logging.error("Failed to set up the robot. Exiting.")