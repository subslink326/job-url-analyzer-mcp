"""Test analysis orchestrator."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from job_url_analyzer.orchestrator import JobAnalysisOrchestrator
from job_url_analyzer.models import AnalysisRequest


@pytest.mark.asyncio
async def test_calculate_completeness_score(test_db_session, sample_company_data):
    """Test completeness score calculation."""
    orchestrator = JobAnalysisOrchestrator(test_db_session)
    
    # Test with complete data
    score = orchestrator._calculate_completeness_score(sample_company_data)
    assert 0.8 <= score <= 1.0  # Should be high with complete data
    
    # Test with minimal data
    minimal_data = {"name": "Test Company"}
    score = orchestrator._calculate_completeness_score(minimal_data)
    assert 0.0 <= score <= 0.3  # Should be low with minimal data


@pytest.mark.asyncio
async def test_calculate_confidence_score(test_db_session):
    """Test confidence score calculation."""
    orchestrator = JobAnalysisOrchestrator(test_db_session)
    
    # Test with enrichment sources
    score = orchestrator._calculate_confidence_score(
        {"name": "Test", "description": "Test company"},
        ["crunchbase", "linkedin"]
    )
    assert 0.7 <= score <= 1.0
    
    # Test without enrichment
    score = orchestrator._calculate_confidence_score(
        {"name": "Test"},
        []
    )
    assert 0.5 <= score <= 0.7


@pytest.mark.asyncio
@patch('job_url_analyzer.orchestrator.WebCrawler')
@patch('job_url_analyzer.orchestrator.ContentExtractor')
async def test_analyze_success(mock_extractor, mock_crawler, test_db_session, sample_company_data):
    """Test successful analysis flow."""
    # Mock crawler
    mock_crawler_instance = AsyncMock()
    mock_crawler_instance.crawl_site.return_value = ["<html>Mock content</html>"]
    mock_crawler.return_value = mock_crawler_instance
    
    # Mock extractor
    mock_extractor_instance = MagicMock()
    mock_extractor_instance.extract_info.return_value = sample_company_data
    mock_extractor.return_value = mock_extractor_instance
    
    # Create orchestrator and run analysis
    orchestrator = JobAnalysisOrchestrator(test_db_session)
    orchestrator.enrichment_manager = AsyncMock()
    orchestrator.enrichment_manager.enrich_company_data.return_value = {
        "enriched_data": sample_company_data,
        "enrichment_sources": [],
        "enrichment_errors": [],
    }
    
    request = AnalysisRequest(
        url="https://techcorp.com/jobs",
        include_enrichment=False
    )
    
    with patch.object(orchestrator, 'report_generator') as mock_report_gen:
        mock_report_gen.generate_report.return_value = "# Mock Report"
        
        result = await orchestrator.analyze(request)
    
    assert result.source_url == str(request.url)
    assert result.company_profile.name == sample_company_data["name"]
    assert result.completeness_score > 0
    assert result.confidence_score > 0