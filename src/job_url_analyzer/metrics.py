"""Prometheus metrics for monitoring."""

import time
from functools import wraps
from typing import Callable, Any

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    "job_analyzer_requests_total",
    "Total number of analysis requests",
    ["endpoint", "method", "status_code"],
)

REQUEST_DURATION = Histogram(
    "job_analyzer_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint", "method"],
)

# Analysis metrics
ANALYSIS_SUCCESS_COUNT = Counter(
    "job_analyzer_analysis_success_total",
    "Total number of successful analyses",
)

ANALYSIS_ERROR_COUNT = Counter(
    "job_analyzer_analysis_error_total",
    "Total number of failed analyses",
)

COMPLETENESS_SCORE = Histogram(
    "job_analyzer_completeness_score",
    "Distribution of completeness scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

CONFIDENCE_SCORE = Histogram(
    "job_analyzer_confidence_score",
    "Distribution of confidence scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# Provider metrics
ENRICHMENT_PROVIDER_SUCCESS = Counter(
    "job_analyzer_enrichment_success_total",
    "Successful enrichment calls by provider",
    ["provider"],
)

ENRICHMENT_PROVIDER_ERROR = Counter(
    "job_analyzer_enrichment_error_total",
    "Failed enrichment calls by provider",
    ["provider"],
)

ENRICHMENT_PROVIDER_DURATION = Histogram(
    "job_analyzer_enrichment_duration_seconds",
    "Enrichment call duration by provider",
    ["provider"],
)

# Crawl metrics
CRAWL_REQUEST_COUNT = Counter(
    "job_analyzer_crawl_requests_total",
    "Total number of crawl requests",
    ["status_code"],
)

CRAWL_DURATION = Histogram(
    "job_analyzer_crawl_duration_seconds",
    "Crawl request duration in seconds",
)

ROBOTS_TXT_BLOCKS = Counter(
    "job_analyzer_robots_txt_blocks_total",
    "Total number of requests blocked by robots.txt",
)

# Database metrics
DATABASE_OPERATION_DURATION = Histogram(
    "job_analyzer_database_operation_duration_seconds",
    "Database operation duration",
    ["operation"],
)

ACTIVE_PROFILES = Gauge(
    "job_analyzer_active_profiles",
    "Number of active profiles in database",
)


def track_request_metrics(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to track request metrics."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status_code = "200"
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = "500"
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                endpoint=func.__name__,
                method="POST",
            ).observe(duration)
            REQUEST_COUNT.labels(
                endpoint=func.__name__,
                method="POST",
                status_code=status_code,
            ).inc()
    
    return wrapper