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
            
    def get_waypoints(self, from_table_id, to_table_id):
        """
        Retrieve waypoints instructions from database for navigation between tables
        
        Args:
            from_table_id (str): Starting table ID
            to_table_id (str): Destination table ID
            
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
                SELECT instructies 
                FROM waypoints 
                WHERE van_tafel_id = %s AND naar_tafel_id = %s
            """
            cursor.execute(query, (from_table_id, to_table_id))
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
                
                logging.info(f"Retrieved waypoints from table {from_table_id} to table {to_table_id}: {route_steps}")
                return route_steps
            else:
                logging.warning(f"No waypoints found from table {from_table_id} to table {to_table_id}")
                return None
                
        except Error as e:
            logging.error(f"Error retrieving waypoints: {e}")
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
                SELECT DISTINCT naar_tafel_id 
                FROM waypoints 
                ORDER BY naar_tafel_id
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