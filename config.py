"""Configuration parameters for the line follower robot"""

SENSOR_THRESHOLD = 0.5
BASE_SPEED = 0.20

MOTOR_LEFT_PIN = "d:11:p"
MOTOR_RIGHT_PIN = "d:3:p"

PID_KP = 0.2 # Robot response to current error strenght, too low robot responds slowly to line changes, too high > zigzagging
PID_KI = 0.01 # Error correction, too low > many not correct persistantly, too high > overshooting / oscilliation
PID_KD = 0.2 # Dampening, low not enough dampening, high too much noise > jerky movements

INTEGRAL_CAP = 5.0
RECOVERY_SPEED = 1.2

JUNCTION_PAUSE_TIME = 0.1
JUNCTION_TURN_FACTOR = 1.2
MIN_BLACK_SENSORS_JUNCTION = 3

ROUTE_PLAN = ["STRAIGHT", "STRAIGHT", "LEFT", "STRAIGHT", "RIGHT", "STRAIGHT", "LEFT"]

LOOP_DELAY = 0.05