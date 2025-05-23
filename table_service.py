"""Table service functionality for the robot"""
import logging

from config import KITCHEN_START_POINT, TABLES_TO_VISIT, TABLES_FILTER
from database_handler import DatabaseHandler


class TableService:
    """Manages table service functionality"""
    
    def __init__(self, db_handler=None):
        self.db_handler = db_handler if db_handler else DatabaseHandler()
        self.current_location = KITCHEN_START_POINT
        self.tables_to_visit = []
        self.current_destination = None
        self.route_complete = False
        
    def load_tables(self):
        """Load tables to visit from database or use defaults"""
        db_tables = self.db_handler.get_all_tables()
        
        if db_tables:
            # Apply filter if TABLES_FILTER is not empty
            if TABLES_FILTER:
                filtered_tables = [table for table in db_tables if table in TABLES_FILTER]
                if filtered_tables:
                    self.tables_to_visit = filtered_tables
                    logging.info(f"Filtered tables to visit: {self.tables_to_visit} (from filter: {TABLES_FILTER})")
                else:
                    logging.warning(f"No tables match the filter {TABLES_FILTER}. Using all tables.")
                    self.tables_to_visit = db_tables
            else:
                # No filter specified, use all tables
                self.tables_to_visit = db_tables
        else:
            # Fallback to default tables
            if TABLES_FILTER:
                filtered_defaults = [table for table in TABLES_TO_VISIT if table in TABLES_FILTER]
                if filtered_defaults:
                    self.tables_to_visit = filtered_defaults
                    logging.info(f"Using filtered default tables: {self.tables_to_visit}")
                else:
                    self.tables_to_visit = TABLES_TO_VISIT
                    logging.warning(f"No default tables match the filter {TABLES_FILTER}. Using all default tables.")
            else:
                self.tables_to_visit = TABLES_TO_VISIT
                
        logging.info(f"Tables to visit: {self.tables_to_visit}")
        
    def get_next_table(self):
        """Get the next table to visit"""
        if not self.tables_to_visit:
            self.route_complete = True
            return None
            
        next_table = self.tables_to_visit.pop(0)
        self.current_destination = next_table
        logging.info(f"Next table to visit: {next_table}")
        return next_table
        
    def get_route_to_next_table(self):
        """Get route to the next table"""
        if self.route_complete:
            return None
            
        next_table = self.get_next_table()
        if not next_table:
            return None
            
        route = self.db_handler.get_waypoints(self.current_location, next_table)
        if route:
            logging.info(f"Route from {self.current_location} to {next_table}: {route}")
            self.current_location = next_table
            return route
        else:
            logging.warning(f"No route found from {self.current_location} to {next_table}")
            return None
            
    def return_to_kitchen(self):
        """Get route back to kitchen"""
        route = self.db_handler.get_waypoints(self.current_location, KITCHEN_START_POINT)
        if route:
            logging.info(f"Route from {self.current_location} to kitchen: {route}")
            self.current_location = KITCHEN_START_POINT
            return route
        else:
            logging.warning(f"No route found from {self.current_location} to kitchen")
            return None