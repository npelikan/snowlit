# test_api.py
import os
import pytest
import datetime
from fastapi.testclient import TestClient
from api import app, API_KEY

client = TestClient(app)

# Mock DuckDB query results
mock_weather_station_data = [
    {"date": datetime.datetime(2024, 11, 1, 0, 0), "tobs": 15.5},
    {"date": datetime.datetime(2024, 11, 2, 0, 0), "tobs": 16.0}
]

mock_snotel_data = [
    {"dateTime": datetime.datetime(2024, 11, 1, 0, 0), "TOBS": 15.5, "SNWD": 20.0, "WTEQ": 5.5},
    {"dateTime": datetime.datetime(2024, 11, 2, 0, 0), "TOBS": 16.0, "SNWD": 21.0, "WTEQ": 5.6}
]

# Helper function to mock DuckDB queries
def mock_duckdb_query(query):
    if "wx_data" in query:
        return mock_weather_station_data
    elif "snotel_data" in query:
        return mock_snotel_data
    return []

# Mock duckdb.query
@pytest.fixture(autouse=True)
def mock_duckdb(monkeypatch):
    def mock_query(query):
        return mock_duckdb_query(query)
    
    def mock
    monkeypatch.setattr("duckdb.query", mock_query)

# Tests for weather station data query
@pytest.mark.asyncio
async def test_weather_station_data():
    response = client.post(
        "/graphql",
        headers={"X-API-Key": API_KEY},
        json={
            "query": """
                query {
                    weatherStationData(stationId: "123", sensors: ["tobs"]) {
                        dateTime
                        tobs
                    }
                }
            """
        }
    )
    assert response.status_code == 200
    data = response.json()["data"]["weatherStationData"]
    assert len(data) == len(mock_weather_station_data)
    for i, entry in enumerate(mock_weather_station_data):
        assert data[i]["dateTime"] == entry["date"].isoformat()
        assert data[i]["tobs"] == entry["tobs"]

# Tests for Snotel data query
@pytest.mark.asyncio
async def test_snotel_data():
    response = client.post(
        "/graphql",
        headers={"X-API-Key": API_KEY},
        json={
            "query": """
                query {
                    snotelData(stationId: "123", sensors: ["tobs", "snwd", "wteq"]) {
                        dateTime
                        tobs
                        snwd
                        wteq
                    }
                }
            """
        }
    )
    assert response.status_code == 200
    data = response.json()["data"]["snotelData"]
    assert len(data) == len(mock_snotel_data)
    for i, entry in enumerate(mock_snotel_data):
        assert data[i]["dateTime"] == entry["dateTime"].isoformat()
        assert data[i]["tobs"] == entry["TOBS"]
        assert data[i]["snwd"] == entry["SNWD"]
        assert data[i]["wteq"] == entry["WTEQ"]

# Test for API key authentication failure
def test_invalid_api_key():
    response = client.post(
        "/graphql",
        headers={"X-API-Key": "invalid_api_key"},
        json={
            "query": """
                query {
                    weatherStationData(stationId: "123", sensors: ["tobs"]) {
                        dateTime
                        tobs
                    }
                }
            """
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

# Test for missing API key
def test_missing_api_key():
    response = client.post(
        "/graphql",
        json={
            "query": """
                query {
                    weatherStationData(stationId: "123", sensors: ["tobs"]) {
                        dateTime
                        tobs
                    }
                }
            """
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"
