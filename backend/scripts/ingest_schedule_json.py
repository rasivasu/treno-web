import json
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'schedules.json')
DB_PATH = os.path.join(BASE_DIR, 'data', 'trains.db')

def ingest_data():
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} not found.")
        return

    print("Loading JSON data...")
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Use simple optimized settings for bulk insert
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")

    # PHASE 1: Extract and Insert Stations
    print("Extracting unique stations...")
    stations = set()
    for item in data:
        code = item.get('station_code')
        name = item.get('station_name')
        if code and name:
            stations.add((code, name))
        else:
            # Handle edge case where name might be missing but code exists? 
            # For now strict check
            pass
            
    print(f"Found {len(stations)} unique stations.")
    
    cursor.execute("BEGIN TRANSACTION")
    cursor.executemany("INSERT OR IGNORE INTO stations (station_code, station_name) VALUES (?, ?)", stations)
    conn.commit()
    
    # Force FTS index rebuild to ensure sync
    print("Rebuilding FTS index...")
    cursor.execute("INSERT INTO stations_fts(stations_fts) VALUES('rebuild')")
    conn.commit()
    
    print("Stations inserted.")

    # PHASE 2: Process Schedules
    print("Processing schedules and calculating stop numbers...")
    
    # Group by train_number
    trains = {}
    for item in data:
        t_num = item.get('train_number')
        if not t_num:
            continue
            
        if t_num not in trains:
            trains[t_num] = []
        trains[t_num].append(item)
        
    schedule_rows = []
    
    for t_num, stops in trains.items():
        # Sort logic: Day -> Arrival (if present) else Departure
        # Handle "None" strings for sorting
        def sort_key(stop):
            # Ensure day is an integer. Some records might have None or string.
            day_val = stop.get('day')
            if day_val is None or day_val == "None":
                day_val = 1
            else:
                try:
                    day_val = int(day_val)
                except ValueError:
                    day_val = 1
            
            arr = stop.get('arrival')
            dep = stop.get('departure')
            
            # Use 24h time format for sorting. 
            # If arrival is "None" (Source), it happens before departure.
            # If departure is "None" (Dest), it happens after arrival.
            # Effectively we need a comparable time.
            
            time_val = "00:00:00"
            if arr != "None":
                time_val = arr
            elif dep != "None":
                time_val = dep
                
            return (day_val, time_val)
            
        stops.sort(key=sort_key)
        
        for idx, stop in enumerate(stops):
            stop_number = idx + 1
            
            # Sanitize day
            day_val = stop.get('day')
            if day_val is None or day_val == "None":
                day_val = 1
            else:
                try:
                    day_val = int(day_val)
                except ValueError:
                    day_val = 1

            # Prepare row: 
            # id, train_number, train_name, station_code, station_name, a_time, d_time, day, stop_number
            
            # Validate FK
            s_code = stop.get('station_code')
            if not s_code: 
                continue # Skip invalid
                
            row = (
                stop.get('id'),
                stop.get('train_number'),
                stop.get('train_name'),
                s_code,
                stop.get('station_name'),
                stop.get('arrival'),      # Keep as "None" string if present
                stop.get('departure'),    # Keep as "None" string if present
                day_val,                  # Use sanitized day value
                stop_number
            )
            schedule_rows.append(row)
            
    print(f"Prepared {len(schedule_rows)} schedule rows.")
    
    # Batch Insert
    print("Inserting schedules...")
    BATCH_SIZE = 10000
    cursor.execute("BEGIN TRANSACTION")
    
    for i in range(0, len(schedule_rows), BATCH_SIZE):
        batch = schedule_rows[i:i + BATCH_SIZE]
        try:
            cursor.executemany("""
                INSERT INTO train_schedule (
                    id, train_number, train_name, station_code, station_name, 
                    arrival_time, departure_time, day, stop_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            cursor.execute("BEGIN TRANSACTION") # Start new for next batch
            print(f"Inserted {i + len(batch)} records...")
        except sqlite3.Error as e:
            print(f"Error executing batch starting at {i}: {e}")
            conn.rollback() # Rollback only this batch? 
            # In simple script, fail. But user asked for error handling.
            # Without savepoints, rollback rolls back entire transaction.
            # We are committing every batch, so previous batches are safe.
            cursor.execute("BEGIN TRANSACTION") 

    conn.commit()
    print("Ingestion complete.")
    conn.close()

if __name__ == "__main__":
    ingest_data()
