"""Test web crawler functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from job_url_analyzer.crawler import WebCrawler


@pytest.mark.asyncio
async def test_crawler_initialization(test_db_session):
    """Test crawler initialization."""
    crawler = WebCrawler(test_db_session)
    
    assert crawler.db_session == test_db_session
    assert crawler.robots_cache == {}
    assert crawler.last_request_times == {}


@pytest.mark.asyncio
async def test_get_domain():
    """Test domain extraction from URL."""
    crawler = WebCrawler(None)
    
    assert crawler._get_domain("https://example.com/path") == "example.com"
    assert crawler._get_domain("http://subdomain.example.com") == "subdomain.example.com"


@pytest.mark.asyncio
async def test_should_follow_link():
    """Test link following logic."""
    crawler = WebCrawler(None)
    
    # Same domain, good path
    assert crawler._should_follow_link(
        "https://example.com/about",
        "https://example.com/"
    ) == True
    
    # Different domain
    assert crawler._should_follow_link(
        "https://other.com/about",
        "https://example.com/"
    ) == False
    
    # Same domain, bad path
    assert crawler._should_follow_link(
        "https://example.com/api/data",
        "https://example.com/"
    ) == False