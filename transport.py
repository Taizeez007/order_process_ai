import sqlite3

def create_and_populate_database():
    conn = sqlite3.connect('transport.db')
    cursor = conn.cursor()

    # Create the vehicles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id TEXT PRIMARY KEY NOT NULL UNIQUE,
            vehicle_type TEXT NOT NULL,
            capacity TEXT NOT NULL,
            goods_type TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    # Insert sample vehicle data
    vehicles_data = [
        ('T123', 'Truck', '10 tons', "fuel", "available"),
        ('T222', 'Truck', '2 tons', "fuel", "on_transit"),
        ('V101', 'Van', '1 ton', 'packages', 'available') # Added a Van
    ]
    cursor.executemany("INSERT INTO vehicles (vehicle_id, vehicle_type, capacity, goods_type, status) VALUES (:vehicle_id, :vehicle_type, :capacity, :goods_type, :status)",
                       [{'vehicle_id': vid, 'vehicle_type': vtype, 'capacity': cap, 'goods_type': gtype, 'status': stat} for vid, vtype, cap, gtype, stat in vehicles_data])
    # Create the drivers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            driver_id TEXT PRIMARY KEY NOT NULL UNIQUE,
            driver_name TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    # Insert sample driver data
    drivers_data = [
        ('uv123', 'Alice', 'Truck', 'available'),
        ('uv202', 'Bob', 'Van', 'available')
    ]
    cursor.executemany("INSERT INTO drivers (driver_id, driver_name, vehicle_type, status) VALUES (:driver_id, :driver_name, :vehicle_type, :status)",
                       [{'driver_id': did, 'driver_name': dname, 'vehicle_type': vtype, 'status': stat} for did, dname, vtype, stat in drivers_data]) #Named placeholders

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_and_populate_database()
    print("SQLite database 'transport.db' created and populated with sample data.")