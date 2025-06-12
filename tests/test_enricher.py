"""Test enrichment functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from job_url_analyzer.enricher.manager import EnrichmentManager
from job_url_analyzer.enricher.base import EnrichmentResult
from job_url_analyzer.enricher.crunchbase import CrunchbaseProvider


class TestEnrichmentManager:
    """Test enrichment manager."""
    
    @pytest.mark.asyncio
    async def test_enrich_company_data(self, sample_company_data):
        """Test company data enrichment."""
        manager = EnrichmentManager()
        
        # Mock providers
        for provider in manager.providers:
            provider.enabled = False  # Disable all providers for testing
        
        result = await manager.enrich_company_data(sample_company_data)
        
        assert "enriched_data" in result
        assert "enrichment_sources" in result
        assert "enrichment_errors" in result
        assert result["enriched_data"] == sample_company_data


class TestCrunchbaseProvider:
    """Test Crunchbase enrichment provider."""
    
    def test_can_enrich_with_name(self, sample_company_data):
        """Test enrichment eligibility with company name."""
        provider = CrunchbaseProvider()
        provider.enabled = True
        provider.api_key = "test-key"
        
        assert provider.can_enrich(sample_company_data) == True
    
    def test_can_enrich_without_data(self):
        """Test enrichment eligibility without sufficient data."""
        provider = CrunchbaseProvider()
        provider.enabled = True
        provider.api_key = "test-key"
        
        assert provider.can_enrich({}) == False
    
    def test_can_enrich_disabled(self, sample_company_data):
        """Test enrichment when provider is disabled."""
        provider = CrunchbaseProvider()
        provider.enabled = False
        
        assert provider.can_enrich(sample_company_data) == False