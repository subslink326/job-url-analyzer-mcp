"""Enrichment providers for external data integration."""

from .base import EnrichmentProvider, EnrichmentResult
from .crunchbase import CrunchbaseProvider
from .linkedin import LinkedInProvider
from .manager import EnrichmentManager

__all__ = [
    "EnrichmentProvider",
    "EnrichmentResult", 
    "CrunchbaseProvider",
    "LinkedInProvider",
    "EnrichmentManager",
]