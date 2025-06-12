"""FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from .config import get_settings
from .database import init_database, get_db_session
from .models import AnalysisRequest, AnalysisResponse, HealthResponse
from .orchestrator import JobAnalysisOrchestrator
from .metrics import (
    REQUEST_COUNT,
    REQUEST_DURATION,
    ANALYSIS_SUCCESS_COUNT,
    ANALYSIS_ERROR_COUNT,
    track_request_metrics,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting Job URL Analyzer MCP Server", version="0.1.0")
    
    # Initialize OpenTelemetry
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Add console exporter for development
    span_processor = BatchSpanProcessor(ConsoleSpanExporter())
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Initialize database
    await init_database()
    logger.info("Database initialized successfully")
    
    yield
    
    logger.info("Shutting down Job URL Analyzer MCP Server")


# Create FastAPI app
app = FastAPI(
    title="Job URL Analyzer MCP Server",
    description="Analyze job URLs and extract company information",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/analyze", response_model=AnalysisResponse)
@track_request_metrics
async def analyze_job_url(request: AnalysisRequest) -> AnalysisResponse:
    """Analyze a job URL and extract company information."""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("analyze_job_url") as span:
        span.set_attribute("url", str(request.url))
        span.set_attribute("include_enrichment", request.include_enrichment)
        
        logger.info(
            "Starting job URL analysis",
            url=str(request.url),
            include_enrichment=request.include_enrichment,
        )
        
        try:
            async with get_db_session() as db:
                orchestrator = JobAnalysisOrchestrator(db)
                result = await orchestrator.analyze(request)
                
                ANALYSIS_SUCCESS_COUNT.inc()
                span.set_attribute("analysis_success", True)
                span.set_attribute("completeness_score", result.completeness_score)
                
                logger.info(
                    "Job URL analysis completed successfully",
                    url=str(request.url),
                    completeness_score=result.completeness_score,
                    profile_id=result.profile_id,
                )
                
                return result
                
        except Exception as e:
            ANALYSIS_ERROR_COUNT.inc()
            span.set_attribute("analysis_success", False)
            span.set_attribute("error", str(e))
            
            logger.error(
                "Job URL analysis failed",
                url=str(request.url),
                error=str(e),
                exc_info=True,
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            ) from e


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "job_url_analyzer.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # Use structlog instead
    )