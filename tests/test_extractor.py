"""Test content extraction functionality."""

import pytest
from job_url_analyzer.extractor import ContentExtractor


class TestContentExtractor:
    """Test content extraction from HTML."""
    
    def test_extract_company_name(self, mock_html_content):
        """Test company name extraction."""
        extractor = ContentExtractor()
        result = extractor.extract_info(mock_html_content, "https://techcorp.com")
        
        assert result["name"] == "TechCorp - Leading AI Company"
    
    def test_extract_description(self, mock_html_content):
        """Test description extraction."""
        extractor = ContentExtractor()
        result = extractor.extract_info(mock_html_content, "https://techcorp.com")
        
        assert "artificial intelligence company" in result["description"]
    
    def test_extract_employee_count(self, mock_html_content):
        """Test employee count extraction."""
        extractor = ContentExtractor()
        result = extractor.extract_info(mock_html_content, "https://techcorp.com")
        
        assert result["employee_count"] == 150
    
    def test_extract_funding_amount(self, mock_html_content):
        """Test funding amount extraction."""
        extractor = ContentExtractor()
        result = extractor.extract_info(mock_html_content, "https://techcorp.com")
        
        assert result["total_funding"] == 25.0
    
    def test_extract_tech_stack(self, mock_html_content):
        """Test technology stack extraction."""
        extractor = ContentExtractor()
        result = extractor.extract_info(mock_html_content, "https://techcorp.com")
        
        tech_stack = result["tech_stack"]
        assert "Python" in tech_stack
        assert "React" in tech_stack
    
    def test_extract_social_links(self, mock_html_content):
        """Test social media link extraction."""
        extractor = ContentExtractor()
        result = extractor.extract_info(mock_html_content, "https://techcorp.com")
        
        assert result["linkedin_url"] == "https://linkedin.com/company/techcorp"
        assert result["twitter_url"] == "https://twitter.com/techcorp"