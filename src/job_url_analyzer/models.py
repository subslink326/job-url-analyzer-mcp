"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class AnalysisRequest(BaseModel):
    """Request model for job URL analysis."""
    
    url: HttpUrl = Field(..., description="Job posting or company URL to analyze")
    include_enrichment: bool = Field(
        default=True,
        description="Whether to include data enrichment from external providers"
    )
    force_refresh: bool = Field(
        default=False,
        description="Force re-analysis even if cached data exists"
    )


class CompanyProfile(BaseModel):
    """Company profile data model."""
    
    # Basic information
    name: Optional[str] = Field(None, description="Company name")
    description: Optional[str] = Field(None, description="Company description")
    industry: Optional[str] = Field(None, description="Industry")
    website: Optional[HttpUrl] = Field(None, description="Company website")
    
    # Size and funding
    employee_count: Optional[int] = Field(None, description="Number of employees")
    employee_count_range: Optional[str] = Field(None, description="Employee count range")
    funding_stage: Optional[str] = Field(None, description="Funding stage")
    total_funding: Optional[float] = Field(None, description="Total funding amount")
    
    # Location
    headquarters: Optional[str] = Field(None, description="Headquarters location")
    locations: List[str] = Field(default_factory=list, description="Office locations")
    
    # Technology and culture
    tech_stack: List[str] = Field(default_factory=list, description="Technology stack")
    benefits: List[str] = Field(default_factory=list, description="Company benefits")
    culture_keywords: List[str] = Field(default_factory=list, description="Culture keywords")
    
    # Social and contact
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn company page")
    twitter_url: Optional[HttpUrl] = Field(None, description="Twitter profile")
    
    # Metadata
    logo_url: Optional[HttpUrl] = Field(None, description="Company logo URL")
    founded_year: Optional[int] = Field(None, description="Year founded")


class AnalysisResponse(BaseModel):
    """Response model for job URL analysis."""
    
    profile_id: UUID = Field(default_factory=uuid4, description="Unique profile identifier")
    source_url: HttpUrl = Field(..., description="Original URL analyzed")
    company_profile: CompanyProfile = Field(..., description="Extracted company profile")
    
    # Analysis metadata
    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Data completeness score (0-1)"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score (0-1)"
    )
    
    # Processing details
    analysis_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the analysis was performed"
    )
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    
    # Enrichment status
    enrichment_sources: List[str] = Field(
        default_factory=list,
        description="External data sources used for enrichment"
    )
    enrichment_errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered during enrichment"
    )
    
    # Generated report
    markdown_report: str = Field(
        default="",
        description="Markdown-formatted analysis report"
    )


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )