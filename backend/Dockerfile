# Use Python 3.11 based on Debian/Alpine
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app /app/app
COPY backend/scripts /app/scripts

# Create data directory and generate database
RUN mkdir -p /app/backend/data
# Generate the database from the JSON source
# Note: init_db.py writes to ../data/trains.db relative to the script location
# Since we run from /app/scripts, it writes to /app/data/trains.db
RUN python scripts/init_db.py && \
    python scripts/ingest_schedule_json.py && \
    mv /app/data/trains.db /app/backend/data/trains.db

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
