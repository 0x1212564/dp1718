"""Database handler for retrieving route data"""
import logging
import mysql.connector
from mysql.connector import Error


class DatabaseHandler:
    """Handles database connection and route data retrieval"""
    
    def __init__(self, host="localhost", user="root", password="64mz8nkb", database="restaurant"):
        """Initialize database connection parameters"""
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
    def connect(self):
        """Establish connection to the MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                logging.info(f"Connected to MySQL database: {self.database}")
                return True
        except Error as e:
            logging.error(f"Error connecting to MySQL database: {e}")
            return False
        return False
        
    def disconnect(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Database connection closed")
            
    def get_route_plan(self, start_point, table_number):
        """
        Retrieve route plan from database for given start point and table number
        
        Args:
            start_point (str): Starting point ID
            table_number (str): Destination table number
            
        Returns:
            list: List of directions (e.g., ["LEFT", "STRAIGHT", "RIGHT"])
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                logging.error("Failed to connect to database")
                return None
                
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT 
                FROM routes 
                WHERE start_point = %s AND destination = %s
            """
            cursor.execute(query, (start_point, table_number))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                # Parse the comma-separated route steps into a list
                # Translate Dutch directions to uppercase English for the robot
                route_steps_raw = result[0].split(',')
                route_steps = []
                
                for step in route_steps_raw:
                    step = step.strip().lower()
                    if step == "links":
                        route_steps.append("LEFT")
                    elif step == "rechts":
                        route_steps.append("RIGHT")
                    elif step in ["vooruit", "rechtdoor"]:
                        route_steps.append("STRAIGHT")
                
                logging.info(f"Retrieved route plan for table {table_number}: {route_steps}")
                return route_steps
            else:
                logging.warning(f"No route found for start point {start_point} to table {table_number}")
                return None
                
        except Error as e:
            logging.error(f"Error retrieving route plan: {e}")
            return None
            
    def get_all_tables(self):
        """
        Retrieve all available table numbers
        
        Returns:
            list: List of table numbers
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                logging.error("Failed to connect to database")
                return []
                
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT DISTINCT destination 
                FROM routes 
                ORDER BY destination
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            table_numbers = [result[0] for result in results]
            logging.info(f"Retrieved available tables: {table_numbers}")
            return table_numbers
            
        except Error as e:
            logging.error(f"Error retrieving available tables: {e}")
            return []