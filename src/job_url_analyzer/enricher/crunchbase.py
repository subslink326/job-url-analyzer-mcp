"""Crunchbase enrichment provider."""

import asyncio
import time
from typing import Dict, Any, Optional

import httpx
from opentelemetry import trace

from .base import EnrichmentProvider, EnrichmentResult
from ..config import get_settings
from ..metrics import (
    ENRICHMENT_PROVIDER_SUCCESS,
    ENRICHMENT_PROVIDER_ERROR,
    ENRICHMENT_PROVIDER_DURATION,
)

settings = get_settings()


class CrunchbaseProvider(EnrichmentProvider):
    """Enrichment provider using Crunchbase API."""
    
    def __init__(self):
        super().__init__("crunchbase", enabled=settings.ENABLE_CRUNCHBASE)
        self.api_key = settings.CRUNCHBASE_API_KEY
        self.base_url = "https://api.crunchbase.com/api/v4"
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "X-cb-user-key": self.api_key,
                "Content-Type": "application/json",
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def can_enrich(self, company_data: Dict[str, Any]) -> bool:
        """Check if we have enough data to search Crunchbase."""
        if not self.enabled or not self.api_key:
            return False
        
        # Need at least company name or website
        return bool(
            company_data.get("name") or 
            company_data.get("website")
        )
    
    async def enrich(self, company_data: Dict[str, Any]) -> EnrichmentResult:
        """Enrich company data using Crunchbase API."""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("crunchbase_enrich") as span:
            start_time = time.time()
            
            try:
                # Search for the company
                company_info = await self._search_company(company_data)
                
                if not company_info:
                    return EnrichmentResult(
                        provider_name=self.name,
                        success=False,
                        data={},
                        error_message="Company not found in Crunchbase",
                        processing_time_ms=int((time.time() - start_time) * 1000),
                    )
                
                # Get detailed company information
                enriched_data = await self._get_company_details(company_info["uuid"])
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                confidence_score = self._calculate_confidence(company_data, enriched_data)
                
                ENRICHMENT_PROVIDER_SUCCESS.labels(provider=self.name).inc()
                ENRICHMENT_PROVIDER_DURATION.labels(provider=self.name).observe(
                    (time.time() - start_time)
                )
                
                span.set_attribute("success", True)
                span.set_attribute("confidence_score", confidence_score)
                
                self.logger.info(
                    "Crunchbase enrichment completed",
                    company_name=company_data.get("name"),
                    enriched_fields=len(enriched_data),
                    confidence_score=confidence_score,
                )
                
                return EnrichmentResult(
                    provider_name=self.name,
                    success=True,
                    data=enriched_data,
                    confidence_score=confidence_score,
                    processing_time_ms=processing_time_ms,
                )
                
            except Exception as e:
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                ENRICHMENT_PROVIDER_ERROR.labels(provider=self.name).inc()
                
                span.set_attribute("success", False)
                span.set_attribute("error", str(e))
                
                self.logger.error(
                    "Crunchbase enrichment failed",
                    company_name=company_data.get("name"),
                    error=str(e),
                )
                
                return EnrichmentResult(
                    provider_name=self.name,
                    success=False,
                    data={},
                    error_message=str(e),
                    processing_time_ms=processing_time_ms,
                )
    
    async def _search_company(self, company_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Search for company in Crunchbase."""
        search_params = {
            "field_ids": [
                "identifier",
                "name",
                "short_description",
                "website"
            ]
        }
        
        # Try searching by name first
        if company_data.get("name"):
            search_params["query"] = company_data["name"]
        
        try:
            response = await self.client.post(
                f"{self.base_url}/searches/organizations",
                json=search_params
            )
            response.raise_for_status()
            
            data = response.json()
            entities = data.get("entities", [])
            
            if entities:
                # Return the first (most relevant) result
                return entities[0]["properties"]
            
        except Exception as e:
            self.logger.warning("Crunchbase search failed", error=str(e))
        
        return None
    
    async def _get_company_details(self, company_uuid: str) -> Dict[str, Any]:
        """Get detailed company information from Crunchbase."""
        field_ids = [
            "name",
            "short_description",
            "long_description", 
            "website",
            "num_employees_enum",
            "funding_stage",
            "funding_total",
            "founded_on",
            "headquarters_location",
            "categories",
            "linkedin",
            "twitter",
            "logo_url",
        ]
        
        try:
            response = await self.client.get(
                f"{self.base_url}/entities/organizations/{company_uuid}",
                params={"field_ids": ",".join(field_ids)}
            )
            response.raise_for_status()
            
            data = response.json()
            properties = data.get("properties", {})
            
            # Map Crunchbase data to our schema
            enriched_data = {}
            
            if properties.get("name"):
                enriched_data["name"] = properties["name"]
            
            if properties.get("short_description"):
                enriched_data["description"] = properties["short_description"]
            elif properties.get("long_description"):
                enriched_data["description"] = properties["long_description"]
            
            if properties.get("website"):
                enriched_data["website"] = properties["website"]
            
            if properties.get("num_employees_enum"):
                enriched_data["employee_count_range"] = properties["num_employees_enum"]
            
            if properties.get("funding_stage"):
                enriched_data["funding_stage"] = properties["funding_stage"]
            
            if properties.get("funding_total"):
                total_funding = properties["funding_total"]
                if isinstance(total_funding, dict) and "value_usd" in total_funding:
                    enriched_data["total_funding"] = total_funding["value_usd"] / 1_000_000  # Convert to millions
            
            if properties.get("founded_on"):
                founded_on = properties["founded_on"]
                if isinstance(founded_on, dict) and "value" in founded_on:
                    year = founded_on["value"][:4]  # Extract year from YYYY-MM-DD
                    try:
                        enriched_data["founded_year"] = int(year)
                    except ValueError:
                        pass
            
            if properties.get("headquarters_location"):
                hq = properties["headquarters_location"]
                if isinstance(hq, dict) and "value" in hq:
                    enriched_data["headquarters"] = hq["value"]
            
            if properties.get("categories"):
                categories = properties["categories"]
                if categories and len(categories) > 0:
                    enriched_data["industry"] = categories[0].get("value", "")
            
            if properties.get("linkedin"):
                linkedin = properties["linkedin"]
                if isinstance(linkedin, dict) and "value" in linkedin:
                    enriched_data["linkedin_url"] = linkedin["value"]
            
            if properties.get("twitter"):
                twitter = properties["twitter"]
                if isinstance(twitter, dict) and "value" in twitter:
                    enriched_data["twitter_url"] = f"https://twitter.com/{twitter['value']}"
            
            if properties.get("logo_url"):
                enriched_data["logo_url"] = properties["logo_url"]
            
            return enriched_data
            
        except Exception as e:
            self.logger.error("Failed to get company details", company_uuid=company_uuid, error=str(e))
            return {}