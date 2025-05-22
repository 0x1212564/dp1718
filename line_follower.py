"""Main line follower robot implementation"""
import logging
import time
from pyfirmata2 import Arduino, util

from config import LOOP_DELAY, TABLE_PAUSE_TIME, ROUTE_PLAN, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from sensors import SensorManager
from motors import MotorController
from pid_controller import PIDController
from junction_handler import JunctionHandler
from recovery_handler import RecoveryHandler
from state_manager import StateManager, STATE_LINE_FOLLOWING, STATE_JUNCTION, STATE_LOST, STATE_FINISHED, STATE_CONTINUE_TURNING, STATE_CONTINUE_TO_WHITE
from database_handler import DatabaseHandler
from table_service import TableService

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
        self.db_handler = None
        self.table_service = None
        
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
            
            # Initialize database and table service
            self.db_handler = DatabaseHandler(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            self.table_service = TableService(self.db_handler)
            
            # Setup components
            sensor_setup_ok = self.sensor_manager.setup()
            motor_setup_ok = self.motor_controller.setup()
            
            if sensor_setup_ok and motor_setup_ok:
                # Load initial route
                self.table_service.load_tables()
                initial_route = self.table_service.get_route_to_next_table()
                if initial_route:
                    self.junction_handler.set_route(initial_route)
                else:
                    self.junction_handler.set_route(ROUTE_PLAN)  # Use default if no route found
                
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
                left_speed, right_speed = 0, 0
                if current_state == STATE_LINE_FOLLOWING:
                    left_speed, right_speed = self.pid_controller.calculate(sensor_readings)
                elif current_state == STATE_JUNCTION:
                    if not self.junction_handler.handled_current_junction:
                        self.junction_handler.handled_current_junction = True
                        left_speed, right_speed = self.junction_handler.handle_junction(self.motor_controller)
                        self.junction_handler.current_turn_speeds = (left_speed, right_speed)
                        
                        # Check if we've completed the current route
                        if self.junction_handler.junction_count >= len(self.junction_handler.current_route):
                            # Pause at the table
                            self.motor_controller.stop()
                            logging.info(f"Arrived at table {self.table_service.current_destination}. Pausing for {TABLE_PAUSE_TIME} seconds.")
                            time.sleep(TABLE_PAUSE_TIME)
                            
                            # Set flag to continue after table
                            self.state_manager.set_continue_after_table(True)
                            
                            # Get route to next table
                            next_route = self.table_service.get_route_to_next_table()
                            if next_route:
                                self.junction_handler.set_route(next_route)
                            else:
                                # No more tables, return to kitchen
                                return_route = self.table_service.return_to_kitchen()
                                if return_route:
                                    self.junction_handler.set_route(return_route)
                                    logging.info("Returning to kitchen.")
                                else:
                                    logging.info("No return route found. Stopping.")
                                    self.motor_controller.stop()
                                    return
                    else:
                        left_speed, right_speed = self.junction_handler.current_turn_speeds
                elif current_state == STATE_LOST:
                    left_speed, right_speed = self.recovery_handler.handle_lost_line(
                        self.sensor_manager.last_valid_pattern
                    )
                elif current_state == STATE_CONTINUE_TURNING:
                    # Continue turning in the last direction
                    left_speed, right_speed = self.state_manager.get_last_turn_direction()
                elif current_state == STATE_CONTINUE_TO_WHITE:
                    # Continue line following until all white
                    left_speed, right_speed = self.pid_controller.calculate(sensor_readings)
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