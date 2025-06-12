"""Generate markdown reports from company analysis data."""

from datetime import datetime
from typing import Dict, Any, List

import structlog

logger = structlog.get_logger(__name__)


class ReportGenerator:
    """Generates comprehensive markdown reports from analysis data."""
    
    async def generate_report(
        self,
        company_data: Dict[str, Any],
        completeness_score: float,
        confidence_score: float,
        enrichment_sources: List[str],
        enrichment_errors: List[str],
    ) -> str:
        """Generate a comprehensive markdown report."""
        
        report_sections = []
        
        # Header
        company_name = company_data.get("name", "Unknown Company")
        report_sections.append(f"# {company_name} - Company Analysis Report")
        report_sections.append(f"*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")
        report_sections.append("")
        
        # Executive Summary
        report_sections.append("## Executive Summary")
        summary = self._generate_executive_summary(company_data)
        report_sections.append(summary)
        report_sections.append("")
        
        # Company Overview
        if any(company_data.get(field) for field in ["description", "industry", "founded_year"]):
            report_sections.append("## Company Overview")
            
            if company_data.get("description"):
                report_sections.append(f"**Description:** {company_data['description']}")
                report_sections.append("")
            
            overview_items = []
            if company_data.get("industry"):
                overview_items.append(f"**Industry:** {company_data['industry']}")
            if company_data.get("founded_year"):
                overview_items.append(f"**Founded:** {company_data['founded_year']}")
            if company_data.get("website"):
                overview_items.append(f"**Website:** {company_data['website']}")
            
            if overview_items:
                report_sections.extend(overview_items)
                report_sections.append("")
        
        # Size and Funding
        if any(company_data.get(field) for field in ["employee_count", "employee_count_range", "funding_stage", "total_funding"]):
            report_sections.append("## Size & Funding")
            
            if company_data.get("employee_count"):
                report_sections.append(f"**Employee Count:** {company_data['employee_count']:,}")
            elif company_data.get("employee_count_range"):
                report_sections.append(f"**Employee Range:** {company_data['employee_count_range']}")
            
            if company_data.get("funding_stage"):
                report_sections.append(f"**Funding Stage:** {company_data['funding_stage']}")
            
            if company_data.get("total_funding"):
                report_sections.append(f"**Total Funding:** ${company_data['total_funding']:.1f}M")
            
            report_sections.append("")
        
        # Location
        if company_data.get("headquarters") or company_data.get("locations"):
            report_sections.append("## Location")
            
            if company_data.get("headquarters"):
                report_sections.append(f"**Headquarters:** {company_data['headquarters']}")
            
            if company_data.get("locations") and len(company_data["locations"]) > 0:
                report_sections.append("**Other Locations:**")
                for location in company_data["locations"]:
                    report_sections.append(f"- {location}")
            
            report_sections.append("")
        
        # Technology & Culture
        tech_culture_added = False
        
        if company_data.get("tech_stack") and len(company_data["tech_stack"]) > 0:
            if not tech_culture_added:
                report_sections.append("## Technology & Culture")
                tech_culture_added = True
            
            report_sections.append("**Technology Stack:**")
            for tech in company_data["tech_stack"]:
                report_sections.append(f"- {tech}")
            report_sections.append("")
        
        if company_data.get("benefits") and len(company_data["benefits"]) > 0:
            if not tech_culture_added:
                report_sections.append("## Technology & Culture")
                tech_culture_added = True
            
            report_sections.append("**Benefits & Perks:**")
            for benefit in company_data["benefits"]:
                report_sections.append(f"- {benefit}")
            report_sections.append("")
        
        if company_data.get("culture_keywords") and len(company_data["culture_keywords"]) > 0:
            if not tech_culture_added:
                report_sections.append("## Technology & Culture")
                tech_culture_added = True
            
            report_sections.append("**Culture Keywords:**")
            culture_tags = ", ".join(company_data["culture_keywords"])
            report_sections.append(culture_tags)
            report_sections.append("")
        
        # Social Presence
        if company_data.get("linkedin_url") or company_data.get("twitter_url"):
            report_sections.append("## Social Presence")
            
            if company_data.get("linkedin_url"):
                report_sections.append(f"**LinkedIn:** {company_data['linkedin_url']}")
            
            if company_data.get("twitter_url"):
                report_sections.append(f"**Twitter:** {company_data['twitter_url']}")
            
            report_sections.append("")
        
        # Analysis Quality
        report_sections.append("## Analysis Quality")
        report_sections.append(f"**Data Completeness:** {completeness_score:.1%}")
        report_sections.append(f"**Confidence Score:** {confidence_score:.1%}")
        
        if enrichment_sources:
            sources_text = ", ".join(enrichment_sources)
            report_sections.append(f"**Enrichment Sources:** {sources_text}")
        
        if enrichment_errors:
            report_sections.append("**Enrichment Issues:**")
            for error in enrichment_errors:
                report_sections.append(f"- {error}")
        
        report_sections.append("")
        
        # Footer
        report_sections.append("---")
        report_sections.append("*This report was generated automatically by Job URL Analyzer. Data accuracy may vary.*")
        
        return "\n".join(report_sections)
    
    def _generate_executive_summary(self, company_data: Dict[str, Any]) -> str:
        """Generate an executive summary paragraph."""
        summary_parts = []
        
        company_name = company_data.get("name", "This company")
        
        # Basic description
        if company_data.get("description"):
            summary_parts.append(company_data["description"])
        else:
            summary_parts.append(f"{company_name} is a company")
        
        # Industry and stage
        details = []
        if company_data.get("industry"):
            details.append(f"in the {company_data['industry'].lower()} industry")
        
        if company_data.get("founded_year"):
            current_year = datetime.now().year
            age = current_year - company_data["founded_year"]
            details.append(f"founded {age} years ago ({company_data['founded_year']})")
        
        if company_data.get("headquarters"):
            details.append(f"headquartered in {company_data['headquarters']}")
        
        if details:
            summary_parts.append(" ".join(details))
        
        # Size information
        if company_data.get("employee_count"):
            summary_parts.append(f"The company has approximately {company_data['employee_count']:,} employees")
        elif company_data.get("employee_count_range"):
            summary_parts.append(f"The company has {company_data['employee_count_range']} employees")
        
        # Funding information
        if company_data.get("funding_stage") and company_data.get("total_funding"):
            summary_parts.append(f"and has raised ${company_data['total_funding']:.1f}M in {company_data['funding_stage'].lower()} funding")
        elif company_data.get("funding_stage"):
            summary_parts.append(f"and is at the {company_data['funding_stage'].lower()} stage")
        elif company_data.get("total_funding"):
            summary_parts.append(f"and has raised ${company_data['total_funding']:.1f}M in funding")
        
        return ". ".join(summary_parts) + "."