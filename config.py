"""Configuration parameters for the line follower and table service robot"""

# --- Line Follower Settings ---
# Motor control pins
MOTOR_LEFT_PIN = "d:11:p"
MOTOR_RIGHT_PIN = "d:3:p"

# Speed and threshold settings
BASE_SPEED = 0.17
SENSOR_THRESHOLD = 0.5
RECOVERY_SPEED = 1.2

# PID controller parameters
PID_KP = 0.2  # Proportional gain: response to current error strength
PID_KI = 0.01  # Integral gain: error correction over time
PID_KD = 0.2  # Derivative gain: dampening to reduce oscillation
INTEGRAL_CAP = 5.0

# Junction handling parameters
JUNCTION_PAUSE_TIME = 0.1
JUNCTION_TURN_FACTOR = 1.4
MIN_BLACK_SENSORS_JUNCTION = 3
JUNCTION_COOLDOWN_TIME = 2.0  # Time to prevent repeated junction detection


# Default route plan (will be overridden by database route)
ROUTE_PLAN = ["RIGHT","LEFT"]

# Main loop timing
LOOP_DELAY = 0.05

# --- Database Settings ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "64mz8nkb"
DB_NAME = "restaurant"
DB_CONNECTION_TIMEOUT = 5  # Seconds to wait for database connection
DB_CONNECTION_RETRY = 3    # Number of connection retry attempts
DB_QUERY_TIMEOUT = 10      # Seconds to wait for query execution

# --- Table Service Settings ---
DEFAULT_START_POINT = "0"  # Default starting point ID
KITCHEN_START_POINT = "0"  # Starting point is 'kitchen' by default
TABLE_DISPLAY_TIME = 2.0   # Time to display table number in seconds
TABLE_PAUSE_TIME = 3.0     # Time to pause at a table in seconds

# List of tables to visit (will be populated at runtime)
TABLES_TO_VISIT = ["1", "2"]  # Default tables if database connection fails
# Filter for specific tables (empty list means visit all tables)
TABLES_FILTER = [1]  # Add table IDs here to filter, e.g. ["1", "4", "6"]
