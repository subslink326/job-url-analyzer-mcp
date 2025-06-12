"""Base classes for enrichment providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EnrichmentResult:
    """Result from an enrichment provider."""
    
    provider_name: str
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    confidence_score: float = 0.0
    processing_time_ms: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EnrichmentProvider(ABC):
    """Abstract base class for enrichment providers."""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.logger = structlog.get_logger(f"enricher.{name}")
    
    @abstractmethod
    async def enrich(self, company_data: Dict[str, Any]) -> EnrichmentResult:
        """Enrich company data using this provider."""
        pass
    
    @abstractmethod
    def can_enrich(self, company_data: Dict[str, Any]) -> bool:
        """Check if this provider can enrich the given company data."""
        pass
    
    def _calculate_confidence(self, original_data: Dict[str, Any], enriched_data: Dict[str, Any]) -> float:
        """Calculate confidence score for enriched data."""
        if not enriched_data:
            return 0.0
        
        # Simple confidence calculation based on number of fields enriched
        original_fields = len([v for v in original_data.values() if v is not None])
        enriched_fields = len([v for v in enriched_data.values() if v is not None])
        
        if original_fields == 0:
            return 1.0 if enriched_fields > 0 else 0.0
        
        improvement = (enriched_fields - original_fields) / original_fields
        return min(1.0, max(0.0, improvement))