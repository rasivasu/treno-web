import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'trains.db')

def init_db():
    print(f"Initializing database at {DB_PATH}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable FTS5
    conn.enable_load_extension(True)
    
    # 1. Master Stations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            station_code TEXT PRIMARY KEY,
            station_name TEXT NOT NULL
        )
    """)
    
    # 2. Train Schedules Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS train_schedule (
            id INTEGER PRIMARY KEY,
            train_number TEXT NOT NULL,
            train_name TEXT NOT NULL,
            station_code TEXT NOT NULL,
            station_name TEXT NOT NULL,
            arrival_time TEXT,
            departure_time TEXT,
            day INTEGER NOT NULL,
            stop_number INTEGER NOT NULL,
            FOREIGN KEY(station_code) REFERENCES stations(station_code)
        )
    """)
    
    # 3. Full Text Search for Stations (Virtual Table)
    # Using content='stations' to avoid duplicating data (External Content Table)
    cursor.execute("DROP TABLE IF EXISTS stations_fts")
    cursor.execute("""
        CREATE VIRTUAL TABLE stations_fts USING fts5(
            station_code,
            station_name,
            content='stations',
            content_rowid='rowid'
        )
    """)

    # Triggers to keep FTS updated
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS stations_ai AFTER INSERT ON stations BEGIN
            INSERT INTO stations_fts(rowid, station_code, station_name) 
            VALUES (new.rowid, new.station_code, new.station_name);
        END;
    """)
    
    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_train_number ON train_schedule(train_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_station_code ON train_schedule(station_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_composite ON train_schedule(station_code, day, departure_time)")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
