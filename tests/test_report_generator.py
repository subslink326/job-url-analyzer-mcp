"""Test report generation."""

import pytest
from job_url_analyzer.report_generator import ReportGenerator


@pytest.mark.asyncio
async def test_generate_report(sample_company_data):
    """Test markdown report generation."""
    generator = ReportGenerator()
    
    report = await generator.generate_report(
        company_data=sample_company_data,
        completeness_score=0.85,
        confidence_score=0.90,
        enrichment_sources=["crunchbase"],
        enrichment_errors=[],
    )
    
    # Check report structure
    assert "# TechCorp - Company Analysis Report" in report
    assert "## Executive Summary" in report
    assert "## Company Overview" in report
    assert "## Size & Funding" in report
    assert "## Analysis Quality" in report
    
    # Check content
    assert sample_company_data["description"] in report
    assert str(sample_company_data["employee_count"]) in report
    assert sample_company_data["funding_stage"] in report
    assert "85.0%" in report  # Completeness score
    assert "90.0%" in report  # Confidence score


@pytest.mark.asyncio
async def test_generate_executive_summary(sample_company_data):
    """Test executive summary generation."""
    generator = ReportGenerator()
    
    summary = generator._generate_executive_summary(sample_company_data)
    
    assert sample_company_data["description"] in summary
    assert str(sample_company_data["founded_year"]) in summary
    assert sample_company_data["headquarters"] in summary
    assert str(sample_company_data["employee_count"]) in summary