# Data Ingestion Plan

## 1. Source Data Analysis
*   **Source:** `backend/data/schedules.json`
*   **Size:** ~82 MB (~417,080 records)
*   **Structure:** Flat list of JSON objects representing individual train stops.

### Sample Record
```json
{
  "id": 302214,
  "train_number": "47154",
  "train_name": "Falaknuma Lingampalli MMTS",
  "station_code": "FM",
  "station_name": "KACHEGUDA FALAKNUMA",
  "arrival": "None",
  "departure": "07:55:00",
  "day": 1
}
```

## 2. Field Mapping Strategy

| JSON Field | Target Column (SQLite) | Transformation |
| :--- | :--- | :--- |
| `id` | `id` | Direct Map |
| `train_number` | `train_number` | Direct Map |
| `train_name` | `train_name` | Direct Map |
| `station_code` | `station_code` | Direct Map |
| `station_name` | `station_name` | Direct Map (Denormalized) |
| `arrival` | `arrival_time` | Convert "None" → `NULL` |
| `departure` | `departure_time` | Convert "None" → `NULL` |
| `day` | `day` | Direct Map |
| *(Missing)* | `stop_number` | **Calculated** (See Logic Below) |

## 3. Transformation Logic

### 3.1 Station Extraction
We will extract a unique list of stations from the schedules to populate the `stations` table first.
1.  Read all records.
2.  Extract `(station_code, station_name)` tuples.
3.  Deduplicate (Set operation).
4.  Insert into `stations`.

### 3.2 Stop Number Calculation
The source JSON lacks a sequence number. We must derive it to order the stops correctly.
**Logic:**
1.  Group records by `train_number`.
2.  Sort each group by:
    *   Primary: `day` (Ascending)
    *   Secondary: Time (Ascending).
        *   Use `arrival_time` if available.
        *   If `arrival_time` is NULL (Source Station), use `departure_time`.
3.  Assign incrementing integer (1, 2, 3...) to `stop_number`.

### 3.3 Data Cleaning
*   **"None" Strings:** The JSON uses the string `"None"` for null times. These must be converted to SQL `NULL` or Python `None`.
*   **Time Format:** Times appear to be `HH:MM:SS`. Validate this pattern.

## 4. Schema Definition

```sql
-- 1. Master Stations Table
CREATE TABLE stations (
    station_code TEXT PRIMARY KEY,
    station_name TEXT NOT NULL
);

-- 2. Full Text Search for Stations
CREATE VIRTUAL TABLE stations_fts USING fts5(
    station_code,
    station_name,
    content='stations',
    content_rowid='rowid'
);

-- 3. Train Schedules Table
CREATE TABLE train_schedule (
    id INTEGER PRIMARY KEY,
    train_number TEXT NOT NULL,
    train_name TEXT NOT NULL,
    station_code TEXT NOT NULL,
    station_name TEXT NOT NULL, -- Denormalized for simpler queries
    arrival_time TEXT,          -- Format: HH:MM:SS or NULL
    departure_time TEXT,        -- Format: HH:MM:SS or NULL
    day INTEGER NOT NULL,
    stop_number INTEGER NOT NULL,
    FOREIGN KEY(station_code) REFERENCES stations(station_code)
);

-- Indexes for Performance
CREATE INDEX idx_train_number ON train_schedule(train_number);
CREATE INDEX idx_station_code ON train_schedule(station_code);
CREATE INDEX idx_search_composite ON train_schedule(station_code, day, departure_time);
```

## 5. Execution Steps
1.  **Init DB:** Run `backend/scripts/init_db.py` to create tables.
2.  **Ingest:** Run `backend/scripts/ingest_schedule_json.py` to:
    *   Load JSON.
    *   Populate `stations` (INSERT OR IGNORE).
    *   Calculate `stop_number`.
    *   Populate `train_schedule` (Batch INSERT).
