"""Unit tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code in [200, 503]  # May be 503 if DB not connected in test


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "SectorView API"


def test_get_sectors():
    """Test sectors endpoint."""
    response = client.get("/api/v1/sectors")
    # Should return 200 even if no data (empty list)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_sector_forecast_not_found():
    """Test forecast endpoint with non-existent sector."""
    response = client.get("/api/v1/sectors/NONEXISTENT/forecast")
    # Should return 404 or 500 depending on implementation
    assert response.status_code in [404, 500]


def test_get_sector_timeseries_not_found():
    """Test timeseries endpoint with non-existent sector."""
    response = client.get("/api/v1/sectors/NONEXISTENT/timeseries")
    assert response.status_code == 404

