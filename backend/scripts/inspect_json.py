import json

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(BASE_DIR, 'data', 'schedules.json')

try:
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    print(f"Total records: {len(data)}")
    print("First 3 records structure:")
    print(json.dumps(data[:3], indent=2))
    
    # Analyze keys
    keys = set()
    for item in data:
        keys.update(item.keys())
    print(f"\nAll unique keys found: {sorted(list(keys))}")

    # Check for nulls/empty strings in key fields for first 1000 records
    print("\nData Quality Check (First 1000):")
    for i, item in enumerate(data[:1000]):
        if not item.get('station_code'):
            print(f"Missing station_code at index {i}")
        if not item.get('train_number'):
            print(f"Missing train_number at index {i}")

except Exception as e:
    print(f"Error reading JSON: {e}")
