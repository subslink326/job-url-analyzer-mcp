"""Database configuration and session management."""

import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Optional
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, Boolean, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class CompanyProfileDB(Base):
    """Database model for company profiles."""
    
    __tablename__ = "company_profiles"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)
    
    # Source information
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    source_url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    
    # Company basic info
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    company_description: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(2048))
    
    # Size and funding
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    employee_count_range: Mapped[Optional[str]] = mapped_column(String(50))
    funding_stage: Mapped[Optional[str]] = mapped_column(String(100))
    total_funding: Mapped[Optional[float]] = mapped_column(Float)
    
    # Location
    headquarters: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Social links
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(2048))
    twitter_url: Mapped[Optional[str]] = mapped_column(String(2048))
    
    # Metadata
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048))
    founded_year: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Analysis scores
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Processing metadata
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    analysis_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
    )
    
    # Enrichment status
    enrichment_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    enrichment_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # JSON fields for flexible data storage
    locations: Mapped[Optional[dict]] = mapped_column(JSON)  # List of office locations
    tech_stack: Mapped[Optional[dict]] = mapped_column(JSON)  # Technology stack
    benefits: Mapped[Optional[dict]] = mapped_column(JSON)  # Company benefits
    culture_keywords: Mapped[Optional[dict]] = mapped_column(JSON)  # Culture keywords
    enrichment_sources: Mapped[Optional[dict]] = mapped_column(JSON)  # External sources used
    enrichment_errors: Mapped[Optional[dict]] = mapped_column(JSON)  # Enrichment errors
    
    # Generated report
    markdown_report: Mapped[Optional[str]] = mapped_column(Text)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
    )


class CrawlLogDB(Base):
    """Database model for crawl logs."""
    
    __tablename__ = "crawl_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[UUID] = mapped_column(index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    content_length: Mapped[Optional[int]] = mapped_column(Integer)
    robots_txt_allowed: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
    )


async def init_database() -> None:
    """Initialize the database and create tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()