#create tool 
from langchain.tools import Tool
from typing import List,Tuple,Dict
import sqlite3

def match_vehicle_to_order(order):
    return order

def create_connection():
    return 1
class llmtools:
    def query_vehicle_database(goods_type: str, quantity: int) -> List[Tuple[int, str]]:
       """Searches the vehicle database for vehicles that can transport the specified goods_type and quantity."""
       conn = create_connection()
       if conn is not None:
           try:

            cursor = conn.cursor()
            cursor.execute("""
                SELECT vehicle_id, vehicle_type
                FROM vehicles
                WHERE goods_type = ? AND capacity >= ?
            """, (goods_type, quantity))
            vehicles = cursor.fetchall()

            return vehicles  # Returns a list of tuples (vehicle_id, vehicle_type)
           except sqlite3.Error as e:
            print(f"Error querying vehicle database: {e}")
            return []
           finally:
              conn.close()
       else:
        return []
        

    def query_driver_database(vehicle_type: str,goods_type:str) -> List[Tuple[int, str]]:
       """Searches the driver database for available drivers based on vehicle type"""
       conn = create_connection()
       if conn is not None:
           
           try:
               cursor = conn.cursor()
               cursor.execute("""
                SELECT driver_id, driver_name
                FROM drivers
                WHERE vehicle_type = ? AND goods_type = ? AND status = 'available'
                """, (vehicle_type, goods_type))
               drivers=cursor.fetchall()
         
               return drivers  # Returns a list of tuples: (driver_id, driver_name)
           except sqlite3.Error as e:
               print(f"Error querying driver database: {e}")
               return []
           finally:
               conn.close()
       else:
        return []

    def add_vehicle_to_order(order_data, vehicle_id: str, vehicle_type: str) -> Dict:
        """Adds the vehicle ID and type to the order data dictionary. Returns the updated order data."""
        order_data["vehicle_id"] = vehicle_id
        order_data["vehicle_type"] = vehicle_type
        print(f"Added vehicle to order: {order_data}") 
        return order_data

    def add_driver_to_order(order_data, driver_id: str, driver_name: str) -> Dict:
        """Adds the driver ID and name to the order data dictionary. Returns the updated order data."""
        order_data["driver_id"] = driver_id
        order_data["driver_name"] = driver_name
        print(f"Added driver to order: {order_data}") 
        return order_data


vehicle_id="123RTUU1"
vehicle_type="truck"
driver_id="2345th2023"
driver_name="Aliu Bamidele"
order1={"order_id":"1234567",
        "order_name":"fuel",
        "good_type":"petroleum",
        "pickup_location":"12 shitta street,Dopemu,Agege,Lagos",
        "dropoff_location":"14 samaru road,Zaria,kaduna"}
# List of all tools
new_order=llmtools.add_vehicle_to_order(order1,vehicle_id,vehicle_type)
print(new_order)
print(llmtools.add_driver_to_order(new_order,driver_id,driver_name))
print ("Tool SearchVehicles Initialized")
print ("Tool SearchDrivers Initialized")
print ("Tool AddVehicleToOrder Initialized")
print ("Tool AddDriverToOrder Initialized")

