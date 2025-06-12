"""Test the main FastAPI application."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    """Test the health check endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(test_client: AsyncClient):
    """Test the metrics endpoint."""
    response = await test_client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_analyze_invalid_url(test_client: AsyncClient):
    """Test analysis with invalid URL."""
    response = await test_client.post(
        "/analyze",
        json={"url": "not-a-url"}
    )
    assert response.status_code == 422  # Validation error