"""Main orchestrator for job URL analysis."""

import hashlib
import time
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

import structlog
from opentelemetry import trace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .crawler import WebCrawler
from .database import CompanyProfileDB
from .enricher.manager import EnrichmentManager
from .extractor import ContentExtractor
from .models import AnalysisRequest, AnalysisResponse, CompanyProfile
from .report_generator import ReportGenerator
from .metrics import COMPLETENESS_SCORE, CONFIDENCE_SCORE

logger = structlog.get_logger(__name__)


class JobAnalysisOrchestrator:
    """Orchestrates the complete job URL analysis pipeline."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.crawler = WebCrawler(db_session)
        self.extractor = ContentExtractor()
        self.enrichment_manager = EnrichmentManager()
        self.report_generator = ReportGenerator()
    
    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Perform complete analysis of a job URL."""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("analyze_job_url") as span:
            start_time = time.time()
            profile_id = uuid4()
            
            span.set_attribute("profile_id", str(profile_id))
            span.set_attribute("url", str(request.url))
            span.set_attribute("include_enrichment", request.include_enrichment)
            span.set_attribute("force_refresh", request.force_refresh)
            
            logger.info(
                "Starting job URL analysis",
                profile_id=str(profile_id),
                url=str(request.url),
                include_enrichment=request.include_enrichment,
                force_refresh=request.force_refresh,
            )
            
            try:
                # Check for existing analysis (unless force refresh)
                if not request.force_refresh:
                    existing_profile = await self._get_existing_profile(str(request.url))
                    if existing_profile:
                        logger.info(
                            "Returning cached analysis",
                            profile_id=str(existing_profile.id),
                            url=str(request.url),
                        )
                        return self._profile_to_response(existing_profile)
                
                # Step 1: Crawl the website
                async with self.crawler:
                    pages_content = await self.crawler.crawl_site(
                        str(request.url),
                        str(profile_id),
                        max_pages=3
                    )
                
                if not pages_content:
                    raise ValueError("Failed to crawl any content from the provided URL")
                
                span.set_attribute("pages_crawled", len(pages_content))
                
                # Step 2: Extract company information
                extracted_data = {}
                for content in pages_content:
                    page_data = self.extractor.extract_info(content, str(request.url))
                    # Merge data, preferring non-None values
                    for key, value in page_data.items():
                        if value is not None and (key not in extracted_data or extracted_data[key] is None):
                            extracted_data[key] = value
                
                span.set_attribute("extracted_fields", len(extracted_data))
                
                # Step 3: Enrich with external data (if requested)
                enrichment_sources = []
                enrichment_errors = []
                
                if request.include_enrichment:
                    async with self.enrichment_manager:
                        enrichment_result = await self.enrichment_manager.enrich_company_data(
                            extracted_data
                        )
                        
                        extracted_data = enrichment_result["enriched_data"]
                        enrichment_sources = enrichment_result["enrichment_sources"]
                        enrichment_errors = enrichment_result["enrichment_errors"]
                
                span.set_attribute("enrichment_sources", len(enrichment_sources))
                span.set_attribute("enrichment_errors", len(enrichment_errors))
                
                # Step 4: Calculate quality scores
                completeness_score = self._calculate_completeness_score(extracted_data)
                confidence_score = self._calculate_confidence_score(extracted_data, enrichment_sources)
                
                COMPLETENESS_SCORE.observe(completeness_score)
                CONFIDENCE_SCORE.observe(confidence_score)
                
                span.set_attribute("completeness_score", completeness_score)
                span.set_attribute("confidence_score", confidence_score)
                
                # Step 5: Generate markdown report
                markdown_report = await self.report_generator.generate_report(
                    extracted_data,
                    completeness_score,
                    confidence_score,
                    enrichment_sources,
                    enrichment_errors,
                )
                
                # Step 6: Save to database
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                profile = await self._save_profile(
                    profile_id=profile_id,
                    source_url=str(request.url),
                    company_data=extracted_data,
                    completeness_score=completeness_score,
                    confidence_score=confidence_score,
                    processing_time_ms=processing_time_ms,
                    enrichment_sources=enrichment_sources,
                    enrichment_errors=enrichment_errors,
                    markdown_report=markdown_report,
                    include_enrichment=request.include_enrichment,
                )
                
                span.set_attribute("processing_time_ms", processing_time_ms)
                
                logger.info(
                    "Job URL analysis completed successfully",
                    profile_id=str(profile_id),
                    url=str(request.url),
                    completeness_score=completeness_score,
                    confidence_score=confidence_score,
                    processing_time_ms=processing_time_ms,
                )
                
                return self._profile_to_response(profile)
                
            except Exception as e:
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                span.set_attribute("success", False)
                span.set_attribute("error", str(e))
                span.set_attribute("processing_time_ms", processing_time_ms)
                
                logger.error(
                    "Job URL analysis failed",
                    profile_id=str(profile_id),
                    url=str(request.url),
                    error=str(e),
                    processing_time_ms=processing_time_ms,
                    exc_info=True,
                )
                
                raise
    
    async def _get_existing_profile(self, source_url: str) -> Optional[CompanyProfileDB]:
        """Check for existing analysis of this URL."""
        url_hash = hashlib.sha256(source_url.encode()).hexdigest()
        
        stmt = select(CompanyProfileDB).where(
            CompanyProfileDB.source_url_hash == url_hash
        ).order_by(CompanyProfileDB.analysis_timestamp.desc())
        
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()
    
    def _calculate_completeness_score(self, company_data: dict) -> float:
        """Calculate data completeness score (0-1)."""
        # Define important fields and their weights
        field_weights = {
            "name": 0.2,
            "description": 0.15,
            "industry": 0.1,
            "website": 0.1,
            "employee_count": 0.1,
            "employee_count_range": 0.05,
            "funding_stage": 0.05,
            "headquarters": 0.1,
            "linkedin_url": 0.05,
            "founded_year": 0.05,
            "tech_stack": 0.05,
        }
        
        total_weight = 0.0
        achieved_weight = 0.0
        
        for field, weight in field_weights.items():
            total_weight += weight
            value = company_data.get(field)
            
            if value is not None:
                if isinstance(value, str) and value.strip():
                    achieved_weight += weight
                elif isinstance(value, (int, float)) and value > 0:
                    achieved_weight += weight
                elif isinstance(value, list) and len(value) > 0:
                    achieved_weight += weight
        
        return achieved_weight / total_weight if total_weight > 0 else 0.0
    
    def _calculate_confidence_score(self, company_data: dict, enrichment_sources: list) -> float:
        """Calculate extraction confidence score (0-1)."""
        base_confidence = 0.6  # Base confidence for extracted data
        
        # Boost confidence based on data richness
        field_count = len([v for v in company_data.values() if v is not None])
        richness_boost = min(0.2, field_count * 0.02)
        
        # Boost confidence based on enrichment sources
        enrichment_boost = min(0.2, len(enrichment_sources) * 0.1)
        
        total_confidence = base_confidence + richness_boost + enrichment_boost
        return min(1.0, total_confidence)
    
    async def _save_profile(
        self,
        profile_id: UUID,
        source_url: str,
        company_data: dict,
        completeness_score: float,
        confidence_score: float,
        processing_time_ms: int,
        enrichment_sources: list,
        enrichment_errors: list,
        markdown_report: str,
        include_enrichment: bool,
    ) -> CompanyProfileDB:
        """Save analysis results to database."""
        url_hash = hashlib.sha256(source_url.encode()).hexdigest()
        
        profile = CompanyProfileDB(
            id=profile_id,
            source_url=source_url,
            source_url_hash=url_hash,
            company_name=company_data.get("name"),
            company_description=company_data.get("description"),
            industry=company_data.get("industry"),
            website=company_data.get("website"),
            employee_count=company_data.get("employee_count"),
            employee_count_range=company_data.get("employee_count_range"),
            funding_stage=company_data.get("funding_stage"),
            total_funding=company_data.get("total_funding"),
            headquarters=company_data.get("headquarters"),
            linkedin_url=company_data.get("linkedin_url"),
            twitter_url=company_data.get("twitter_url"),
            logo_url=company_data.get("logo_url"),
            founded_year=company_data.get("founded_year"),
            completeness_score=completeness_score,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            analysis_timestamp=datetime.utcnow(),
            enrichment_enabled=include_enrichment,
            enrichment_complete=len(enrichment_sources) > 0,
            locations={"locations": company_data.get("locations", [])},
            tech_stack={"tech_stack": company_data.get("tech_stack", [])},
            benefits={"benefits": company_data.get("benefits", [])},
            culture_keywords={"culture_keywords": company_data.get("culture_keywords", [])},
            enrichment_sources={"sources": enrichment_sources},
            enrichment_errors={"errors": enrichment_errors},
            markdown_report=markdown_report,
        )
        
        self.db_session.add(profile)
        await self.db_session.flush()
        
        return profile
    
    def _profile_to_response(self, profile: CompanyProfileDB) -> AnalysisResponse:
        """Convert database profile to API response."""
        company_profile = CompanyProfile(
            name=profile.company_name,
            description=profile.company_description,
            industry=profile.industry,
            website=profile.website,
            employee_count=profile.employee_count,
            employee_count_range=profile.employee_count_range,
            funding_stage=profile.funding_stage,
            total_funding=profile.total_funding,
            headquarters=profile.headquarters,
            locations=profile.locations.get("locations", []) if profile.locations else [],
            tech_stack=profile.tech_stack.get("tech_stack", []) if profile.tech_stack else [],
            benefits=profile.benefits.get("benefits", []) if profile.benefits else [],
            culture_keywords=profile.culture_keywords.get("culture_keywords", []) if profile.culture_keywords else [],
            linkedin_url=profile.linkedin_url,
            twitter_url=profile.twitter_url,
            logo_url=profile.logo_url,
            founded_year=profile.founded_year,
        )
        
        return AnalysisResponse(
            profile_id=profile.id,
            source_url=profile.source_url,
            company_profile=company_profile,
            completeness_score=profile.completeness_score,
            confidence_score=profile.confidence_score,
            analysis_timestamp=profile.analysis_timestamp,
            processing_time_ms=profile.processing_time_ms,
            enrichment_sources=profile.enrichment_sources.get("sources", []) if profile.enrichment_sources else [],
            enrichment_errors=profile.enrichment_errors.get("errors", []) if profile.enrichment_errors else [],
            markdown_report=profile.markdown_report or "",
        )