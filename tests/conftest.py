"""Pytest configuration and fixtures."""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from job_url_analyzer.database import Base, get_db_session
from job_url_analyzer.main import app
from job_url_analyzer.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db_session():
    """Create a test database session."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_client(test_db_session):
    """Create a test client with mocked database."""
    
    async def override_get_db_session():
        yield test_db_session
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_html_content():
    """Mock HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TechCorp - Leading AI Company</title>
        <meta name="description" content="TechCorp is a leading artificial intelligence company building the future of automation.">
    </head>
    <body>
        <h1>TechCorp</h1>
        <div class="about">
            TechCorp is a cutting-edge AI company founded in 2020. We specialize in machine learning
            and natural language processing solutions for enterprise clients.
        </div>
        <div class="company-info">
            <p>Industry: Technology</p>
            <p>Employees: 150 people</p>
            <p>Headquarters: San Francisco, CA</p>
            <p>Founded in 2020</p>
            <p>Series B funding: $25 million</p>
        </div>
        <div class="tech-stack">
            <p>Technologies: Python, React, AWS, PostgreSQL</p>
        </div>
        <div class="benefits">
            <ul>
                <li>Health insurance</li>
                <li>Remote work</li>
                <li>Stock options</li>
            </ul>
        </div>
        <footer>
            <a href="https://linkedin.com/company/techcorp">LinkedIn</a>
            <a href="https://twitter.com/techcorp">Twitter</a>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "name": "TechCorp",
        "description": "Leading AI company building the future of automation",
        "industry": "Technology",
        "website": "https://techcorp.com",
        "employee_count": 150,
        "employee_count_range": "51-200",
        "funding_stage": "Series B",
        "total_funding": 25.0,
        "headquarters": "San Francisco, CA",
        "founded_year": 2020,
        "linkedin_url": "https://linkedin.com/company/techcorp",
        "twitter_url": "https://twitter.com/techcorp",
        "tech_stack": ["Python", "React", "AWS", "PostgreSQL"],
        "benefits": ["Health insurance", "Remote work", "Stock options"],
        "culture_keywords": ["Innovative", "Fast-paced"],
    }