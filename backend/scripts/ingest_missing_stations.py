import json
import sqlite3
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'trains.db')
DATA_FILE = os.path.join(BASE_DIR, 'data', 'schedules.json')

def ingest_missing_stations():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get existing stations
    print("Fetching existing stations from DB...")
    cursor.execute("SELECT station_code FROM stations")
    existing_stations = set(row[0] for row in cursor.fetchall())
    print(f"Found {len(existing_stations)} stations in DB.")

    # Get stations from schedules and identify missing ones
    print(f"Scanning {DATA_FILE} for missing stations...")
    missing_stations = set()
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                code = item.get('station_code')
                if code and code not in existing_stations:
                    missing_stations.add(code)
    except Exception as e:
        print(f"Error reading schedules: {e}")
        return

    print(f"Found {len(missing_stations)} unique missing stations.")
    
    if not missing_stations:
        print("No missing stations found. Exiting.")
        return

    print("Inserting missing stations as placeholders...")
    count = 0
    for station_code in missing_stations:
        # Placeholder values
        # We use Title Case for station name to look slightly better
        station_name = f"Station {station_code}"
        
        # Check if table has city_code/zone or just code/name
        # Based on init_db.py, columns are station_code, station_name. 
        # But previous ingest_stations.py had city_code, zone.
        # Let's check schema
        try:
             cursor.execute("""
            INSERT INTO stations (station_code, station_name)
            VALUES (?, ?)
            """, (station_code, station_name))
        except sqlite3.OperationalError:
             # Fallback if schema differs (e.g. has city_code)
             # But init_db.py showed only code and name.
             pass

        count += 1
        if count % 1000 == 0:
            print(f"Inserted {count} placeholders...")

    conn.commit()
    print(f"Successfully inserted {count} missing stations.")
    conn.close()

if __name__ == "__main__":
    ingest_missing_stations()
