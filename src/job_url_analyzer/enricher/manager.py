"""Enrichment manager to coordinate multiple providers."""

import asyncio
from typing import Dict, Any, List, Optional

import structlog
from opentelemetry import trace

from .base import EnrichmentProvider, EnrichmentResult
from .crunchbase import CrunchbaseProvider
from .linkedin import LinkedInProvider

logger = structlog.get_logger(__name__)


class EnrichmentManager:
    """Manages multiple enrichment providers."""
    
    def __init__(self):
        self.providers: List[EnrichmentProvider] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available enrichment providers."""
        # Add providers here
        self.providers = [
            CrunchbaseProvider(),
            LinkedInProvider(),
        ]
        
        enabled_providers = [p.name for p in self.providers if p.enabled]
        logger.info("Initialized enrichment providers", providers=enabled_providers)
    
    async def enrich_company_data(
        self, 
        company_data: Dict[str, Any],
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """Enrich company data using all available providers."""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("enrich_company_data") as span:
            span.set_attribute("available_providers", len(self.providers))
            
            # Filter providers that can enrich this data
            applicable_providers = [
                provider for provider in self.providers 
                if provider.enabled and provider.can_enrich(company_data)
            ]
            
            span.set_attribute("applicable_providers", len(applicable_providers))
            
            if not applicable_providers:
                logger.info("No enrichment providers applicable for this company data")
                return {
                    "enriched_data": company_data,
                    "enrichment_sources": [],
                    "enrichment_errors": [],
                    "enrichment_results": [],
                }
            
            logger.info(
                "Starting enrichment process",
                company_name=company_data.get("name"),
                providers=[p.name for p in applicable_providers],
            )
            
            # Run enrichment providers concurrently with timeout
            try:
                enrichment_tasks = [
                    provider.enrich(company_data)
                    for provider in applicable_providers
                ]
                
                results = await asyncio.wait_for(
                    asyncio.gather(*enrichment_tasks, return_exceptions=True),
                    timeout=timeout_seconds
                )
                
            except asyncio.TimeoutError:
                logger.warning("Enrichment process timed out", timeout=timeout_seconds)
                results = []
            
            # Process results
            enriched_data = company_data.copy()
            enrichment_sources = []
            enrichment_errors = []
            enrichment_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    provider_name = applicable_providers[i].name
                    error_msg = f"{provider_name}: {str(result)}"
                    enrichment_errors.append(error_msg)
                    logger.error("Enrichment provider failed", provider=provider_name, error=str(result))
                    continue
                
                if isinstance(result, EnrichmentResult):
                    enrichment_results.append(result)
                    
                    if result.success:
                        enrichment_sources.append(result.provider_name)
                        # Merge enriched data (new data takes precedence)
                        for key, value in result.data.items():
                            if value is not None:
                                enriched_data[key] = value
                        
                        logger.info(
                            "Enrichment successful",
                            provider=result.provider_name,
                            confidence=result.confidence_score,
                            processing_time_ms=result.processing_time_ms,
                        )
                    else:
                        if result.error_message:
                            enrichment_errors.append(f"{result.provider_name}: {result.error_message}")
            
            span.set_attribute("successful_providers", len(enrichment_sources))
            span.set_attribute("failed_providers", len(enrichment_errors))
            
            logger.info(
                "Enrichment process completed",
                company_name=company_data.get("name"),
                successful_providers=enrichment_sources,
                failed_providers=len(enrichment_errors),
                total_fields_enriched=len(enriched_data) - len(company_data),
            )
            
            return {
                "enriched_data": enriched_data,
                "enrichment_sources": enrichment_sources,
                "enrichment_errors": enrichment_errors,
                "enrichment_results": enrichment_results,
            }
    
    async def __aenter__(self):
        # Initialize provider clients if needed
        for provider in self.providers:
            if hasattr(provider, '__aenter__'):
                await provider.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup provider clients
        for provider in self.providers:
            if hasattr(provider, '__aexit__'):
                await provider.__aexit__(exc_type, exc_val, exc_tb)