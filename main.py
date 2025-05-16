"""
Line follower robot with table service functionality
Main entry point for the application
"""
import logging

from line_follower import LineFollower

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('line_follower.log', mode='w'),
        logging.StreamHandler()
    ]
)

def main():
    """Main entry point for the line follower robot application"""
    try:
        # Create and setup the line follower robot
        robot = LineFollower()
        if robot.setup():
            # Start the robot
            robot.run()
        else:
            logging.error("Failed to set up the robot. Exiting.")
    except Exception as e:
        logging.error(f"Unhandled exception in main: {e}")
    finally:
        logging.info("Program terminated")

if __name__ == "__main__":
    main()