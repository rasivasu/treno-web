from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_search_stations():
    # Test with a known station code prefix
    response = client.get("/api/stations?q=HY")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Check if we get some results. Note: Depends on DB content.
    # Assuming standard DB has HYB/HYDERABAD
    if len(data) > 0:
        assert any("HY" in s["station_code"] or "HY" in s["station_name"] for s in data)

def test_search_trains_param_validation():
    # Missing params
    response = client.get("/api/search")
    assert response.status_code == 422

    # Invalid station code length
    response = client.get("/api/search?from_station=A&to_station=B&date=2023-01-01")
    assert response.status_code == 422 

def test_search_trains_valid():
    # Test SBC to NDLS which we know exists from manual verification
    response = client.get("/api/search?from_station=SBC&to_station=NDLS&date=2023-01-01")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data
    assert data["count"] >= 0
    
    if data["count"] > 0:
        train = data["results"][0]
        assert "train_number" in train
        assert "train_name" in train
