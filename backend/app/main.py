from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
from contextlib import asynccontextmanager

# --- Configuration ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trains.db')

# --- Lifespan & App Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Determine absolute path for DB to avoid CWD issues
    if not os.path.exists(DB_PATH):
        print(f"WARNING: Database not found at {DB_PATH}")
    yield
    # Cleanup if needed

app = FastAPI(lifespan=lifespan)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://treno-web.vercel.app",
        "https://treno-web-woad.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class Station(BaseModel):
    station_code: str
    station_name: str

class TrainResult(BaseModel):
    train_number: str
    train_name: str
    from_station_name: str
    to_station_name: str
    departure_time: str
    arrival_time: str
    duration: str  # Pre-calculated or client-calc? Sending raw for now.
    
# --- Database Helper ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH) # Sync for now, can migrate to aiosqlite for high concurrency
    conn.row_factory = sqlite3.Row
    return conn

# --- Endpoints ---
@app.get("/api/health")
def read_root():
    return {"status": "ok", "db_path": DB_PATH}

@app.get("/api/stations")
def search_stations(q: str = Query(..., min_length=2)):
    """
    Search for stations by name or code.
    returns top 10 matches.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Simple prefix search for now. Improve with FTS later if needed.
    query = """
        SELECT station_code, station_name 
        FROM stations 
        WHERE station_code LIKE ? OR station_name LIKE ?
        LIMIT 10
    """
    pattern = f"{q.upper()}%"
    
    try:
        cursor.execute(query, (pattern, pattern))
        rows = cursor.fetchall()
        
        return [
            {"station_code": row["station_code"], "station_name": row["station_name"]} 
            for row in rows
        ]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/search")
def search_trains(
    from_station: str = Query(..., min_length=2, max_length=5),
    to_station: str = Query(..., min_length=2, max_length=5),
    date: str = Query(..., description="YYYY-MM-DD") # Date for day filtering (future feature)
):
    """
    Search for trains between two stations.
    Query:
    1. Find train_numbers that have BOTH stations.
    2. Ensure Stop(From) < Stop(To).
    3. Return details.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We join train_schedule to itself to find the route
    # T1 = Origin, T2 = Destination
    query = """
        SELECT 
            t1.train_number,
            t1.train_name,
            t1.station_name as from_station_name,
            t2.station_name as to_station_name,
            t1.departure_time,
            t2.arrival_time,
            (t2.day - t1.day) as day_diff
        FROM train_schedule t1
        JOIN train_schedule t2 ON t1.train_number = t2.train_number
        WHERE 
            t1.station_code = ? 
            AND t2.station_code = ?
            AND t1.stop_number < t2.stop_number
            AND t1.departure_time != 'None' -- Must depart from origin
            AND t2.arrival_time != 'None'   -- Must arrive at destination
        ORDER BY t1.departure_time
    """
    
    try:
        cursor.execute(query, (from_station.upper(), to_station.upper()))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "train_number": row["train_number"],
                "train_name": row["train_name"],
                "from_station_name": row["from_station_name"],
                "to_station_name": row["to_station_name"],
                "departure_time": row["departure_time"],
                "arrival_time": row["arrival_time"],
                "duration": f"{row['day_diff']} days" if row['day_diff'] > 0 else "Same day"
            })
            
        return {"results": results, "count": len(results)}
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
