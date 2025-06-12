# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and core functionality
- FastAPI-based web server with async support
- Web crawler with robots.txt compliance and rate limiting
- Content extraction using Selectolax for fast HTML parsing
- Pluggable enrichment system with Crunchbase and LinkedIn providers
- SQLAlchemy 2.x database layer with async support
- Comprehensive test suite with pytest
- Docker and Kubernetes deployment configurations
- CI/CD pipeline with GitHub Actions
- Prometheus metrics and Grafana dashboards
- OpenTelemetry distributed tracing
- Structured logging with structlog
- Database migrations with Alembic
- Development tools (pre-commit, Makefile, etc.)

### Features
- **Web Crawling**: Respectful crawling with configurable delays and concurrent limits
- **Content Extraction**: Extract company information from job postings and company pages
- **Data Enrichment**: Enhance extracted data with external APIs (Crunchbase, LinkedIn)
- **Quality Scoring**: Completeness and confidence metrics for extracted data
- **Markdown Reports**: Generate comprehensive company analysis reports
- **Caching**: URL-based caching to avoid duplicate analysis
- **Monitoring**: Full observability with metrics, tracing, and logging
- **Deployment**: Production-ready with Docker, Kubernetes, and monitoring

### Technical Details
- Python 3.11+ with modern async/await patterns
- FastAPI for high-performance API endpoints
- SQLAlchemy 2.x with async database operations
- Selectolax for 8-10x faster HTML parsing vs BeautifulSoup
- OpenTelemetry for distributed tracing
- Prometheus metrics with custom business KPIs
- Comprehensive test coverage (80%+)
- Multi-architecture Docker images (AMD64, ARM64)
- Kubernetes-ready with health checks and auto-scaling

### Configuration
- Environment-based configuration with Pydantic Settings
- Support for SQLite (development) and PostgreSQL (production)
- Configurable rate limiting and crawler behavior
- Optional enrichment providers with API key management
- CORS configuration for frontend integration

## [0.1.0] - 2025-06-12

### Added
- Initial release with complete MCP server implementation
- Core job URL analysis functionality
- Production-ready deployment configuration
- Comprehensive documentation and examples

---

**Note**: This project follows semantic versioning. Version numbers indicate:
- MAJOR: Incompatible API changes
- MINOR: Backward-compatible functionality additions
- PATCH: Backward-compatible bug fixes