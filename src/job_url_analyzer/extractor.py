"""Content extraction from HTML pages."""

import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import structlog
from selectolax.parser import HTMLParser
from opentelemetry import trace

logger = structlog.get_logger(__name__)


class ContentExtractor:
    """Extract structured information from HTML content."""
    
    def __init__(self):
        # Compile regex patterns for better performance
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?1[-\.\s]?)?\(?([0-9]{3})\)?[-\.\s]?([0-9]{3})[-\.\s]?([0-9]{4})')
        self.employee_count_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*)\s*(?:employees?|staff|people|team members?)', re.IGNORECASE)
        self.funding_pattern = re.compile(r'\$(\d+(?:\.\d+)?)\s*(million|billion|M|B|k)', re.IGNORECASE)
        self.year_pattern = re.compile(r'\b(19|20)\d{2}\b')
    
    def extract_info(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """Extract company information from HTML content."""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("extract_info") as span:
            parser = HTMLParser(html_content)
            
            info = {
                "name": self._extract_company_name(parser),
                "description": self._extract_description(parser),
                "industry": self._extract_industry(parser),
                "website": base_url,
                "employee_count": self._extract_employee_count(parser),
                "employee_count_range": self._extract_employee_range(parser),
                "funding_stage": self._extract_funding_stage(parser),
                "total_funding": self._extract_funding_amount(parser),
                "headquarters": self._extract_headquarters(parser),
                "locations": self._extract_locations(parser),
                "tech_stack": self._extract_tech_stack(parser),
                "benefits": self._extract_benefits(parser),
                "culture_keywords": self._extract_culture_keywords(parser),
                "linkedin_url": self._extract_social_link(parser, "linkedin"),
                "twitter_url": self._extract_social_link(parser, "twitter"),
                "logo_url": self._extract_logo_url(parser, base_url),
                "founded_year": self._extract_founded_year(parser),
            }
            
            # Remove None values
            info = {k: v for k, v in info.items() if v is not None}
            
            span.set_attribute("extracted_fields", len(info))
            
            logger.info(
                "Content extraction completed",
                base_url=base_url,
                extracted_fields=list(info.keys()),
            )
            
            return info
    
    def _extract_company_name(self, parser: HTMLParser) -> Optional[str]:
        """Extract company name from various sources."""
        # Try title tag first
        title = parser.css_first("title")
        if title and title.text():
            title_text = title.text().strip()
            # Remove common suffixes
            for suffix in [" - Careers", " - Jobs", " | Careers", " | Jobs", " Careers", " Jobs"]:
                if title_text.endswith(suffix):
                    return title_text[:-len(suffix)].strip()
            return title_text
        
        # Try h1 tags
        h1_tags = parser.css("h1")
        for h1 in h1_tags:
            if h1.text():
                text = h1.text().strip()
                if len(text) < 100:  # Reasonable company name length
                    return text
        
        # Try meta property
        og_title = parser.css_first('meta[property="og:title"]')
        if og_title:
            content = og_title.attributes.get("content", "").strip()
            if content:
                return content
        
        return None
    
    def _extract_description(self, parser: HTMLParser) -> Optional[str]:
        """Extract company description."""
        # Try meta description
        meta_desc = parser.css_first('meta[name="description"]')
        if meta_desc:
            content = meta_desc.attributes.get("content", "").strip()
            if content and len(content) > 50:
                return content
        
        # Try Open Graph description
        og_desc = parser.css_first('meta[property="og:description"]')
        if og_desc:
            content = og_desc.attributes.get("content", "").strip()
            if content and len(content) > 50:
                return content
        
        # Look for about sections
        about_selectors = [
            '.about', '.company-description', '.overview',
            '[class*="about"]', '[class*="description"]', '[class*="overview"]'
        ]
        
        for selector in about_selectors:
            elements = parser.css(selector)
            for element in elements:
                text = element.text()
                if text and len(text) > 100:
                    return text.strip()[:500]  # Limit length
        
        return None
    
    def _extract_industry(self, parser: HTMLParser) -> Optional[str]:
        """Extract industry information."""
        # Look for industry keywords in text
        text_content = parser.text().lower()
        
        industries = [
            "technology", "software", "fintech", "healthcare", "biotech",
            "e-commerce", "retail", "manufacturing", "consulting",
            "marketing", "advertising", "real estate", "education",
            "automotive", "aerospace", "energy", "telecommunications"
        ]
        
        for industry in industries:
            if industry in text_content:
                return industry.title()
        
        return None
    
    def _extract_employee_count(self, parser: HTMLParser) -> Optional[int]:
        """Extract employee count."""
        text_content = parser.text()
        
        matches = self.employee_count_pattern.findall(text_content)
        if matches:
            # Return the largest number found (most likely to be accurate)
            numbers = [int(match.replace(',', '')) for match in matches]
            return max(numbers)
        
        return None
    
    def _extract_employee_range(self, parser: HTMLParser) -> Optional[str]:
        """Extract employee count range."""
        text_content = parser.text().lower()
        
        ranges = [
            ("1-10", ["1-10", "startup", "small team"]),
            ("11-50", ["11-50", "small company"]),
            ("51-200", ["51-200", "medium company"]),
            ("201-500", ["201-500", "growing company"]),
            ("501-1000", ["501-1000", "large company"]),
            ("1000+", ["1000+", "enterprise", "large corporation"]),
        ]
        
        for range_str, keywords in ranges:
            if any(keyword in text_content for keyword in keywords):
                return range_str
        
        return None
    
    def _extract_funding_stage(self, parser: HTMLParser) -> Optional[str]:
        """Extract funding stage."""
        text_content = parser.text().lower()
        
        stages = [
            "seed", "series a", "series b", "series c", "series d",
            "pre-seed", "angel", "ipo", "acquired", "public"
        ]
        
        for stage in stages:
            if stage in text_content:
                return stage.title()
        
        return None
    
    def _extract_funding_amount(self, parser: HTMLParser) -> Optional[float]:
        """Extract funding amount."""
        text_content = parser.text()
        
        matches = self.funding_pattern.findall(text_content)
        if matches:
            amount_str, unit = matches[0]
            amount = float(amount_str)
            
            if unit.lower() in ['billion', 'b']:
                return amount * 1000
            elif unit.lower() in ['million', 'm']:
                return amount
            elif unit.lower() == 'k':
                return amount / 1000
        
        return None
    
    def _extract_headquarters(self, parser: HTMLParser) -> Optional[str]:
        """Extract headquarters location."""
        # Look for address or location information
        selectors = [
            '.address', '.location', '.headquarters',
            '[class*="address"]', '[class*="location"]', '[class*="office"]'
        ]
        
        for selector in selectors:
            elements = parser.css(selector)
            for element in elements:
                text = element.text()
                if text and len(text) < 200:  # Reasonable address length
                    return text.strip()
        
        return None
    
    def _extract_locations(self, parser: HTMLParser) -> List[str]:
        """Extract office locations."""
        locations = []
        
        # Look for location lists
        text_content = parser.text()
        
        # Common city patterns
        cities = re.findall(r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b', text_content)
        locations.extend(cities[:5])  # Limit to avoid noise
        
        return list(set(locations))  # Remove duplicates
    
    def _extract_tech_stack(self, parser: HTMLParser) -> List[str]:
        """Extract technology stack."""
        tech_keywords = [
            "python", "javascript", "react", "nodejs", "java", "go",
            "kubernetes", "docker", "aws", "azure", "gcp", "postgresql",
            "mongodb", "redis", "elasticsearch", "kafka", "spark"
        ]
        
        text_content = parser.text().lower()
        found_tech = []
        
        for tech in tech_keywords:
            if tech in text_content:
                found_tech.append(tech.title())
        
        return found_tech
    
    def _extract_benefits(self, parser: HTMLParser) -> List[str]:
        """Extract company benefits."""
        benefit_keywords = [
            "health insurance", "dental", "vision", "401k", "retirement",
            "remote work", "flexible hours", "unlimited pto", "equity",
            "stock options", "gym membership", "free lunch"
        ]
        
        text_content = parser.text().lower()
        found_benefits = []
        
        for benefit in benefit_keywords:
            if benefit in text_content:
                found_benefits.append(benefit.title())
        
        return found_benefits
    
    def _extract_culture_keywords(self, parser: HTMLParser) -> List[str]:
        """Extract culture-related keywords."""
        culture_keywords = [
            "innovative", "collaborative", "fast-paced", "startup culture",
            "work-life balance", "diversity", "inclusion", "agile",
            "remote-first", "mission-driven", "customer-focused"
        ]
        
        text_content = parser.text().lower()
        found_culture = []
        
        for keyword in culture_keywords:
            if keyword in text_content:
                found_culture.append(keyword.title())
        
        return found_culture
    
    def _extract_social_link(self, parser: HTMLParser, platform: str) -> Optional[str]:
        """Extract social media links."""
        platform_domains = {
            "linkedin": "linkedin.com",
            "twitter": "twitter.com"
        }
        
        domain = platform_domains.get(platform)
        if not domain:
            return None
        
        links = parser.css("a[href]")
        for link in links:
            href = link.attributes.get("href", "")
            if domain in href:
                return href
        
        return None
    
    def _extract_logo_url(self, parser: HTMLParser, base_url: str) -> Optional[str]:
        """Extract company logo URL."""
        # Look for logo images
        selectors = [
            'img[class*="logo"]',
            'img[alt*="logo"]',
            '.logo img',
            'header img'
        ]
        
        for selector in selectors:
            img = parser.css_first(selector)
            if img:
                src = img.attributes.get("src", "")
                if src:
                    return urljoin(base_url, src)
        
        return None
    
    def _extract_founded_year(self, parser: HTMLParser) -> Optional[int]:
        """Extract founding year."""
        text_content = parser.text()
        
        # Look for "founded in YYYY" or "since YYYY" patterns
        founded_patterns = [
            r'founded in (\d{4})',
            r'since (\d{4})',
            r'established in (\d{4})',
            r'started in (\d{4})'
        ]
        
        for pattern in founded_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                year = int(matches[0])
                if 1800 <= year <= 2025:  # Reasonable year range
                    return year
        
        return None