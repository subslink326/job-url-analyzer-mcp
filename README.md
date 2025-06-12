# Job URL Analyzer MCP Server

A comprehensive FastAPI-based microservice for analyzing job URLs and extracting detailed company information. Built with modern async Python, this service crawls job postings and company websites to build rich company profiles with data enrichment from external providers.

## ✨ Features

- **🕷️ Intelligent Web Crawling**: Respectful crawling with robots.txt compliance and rate limiting
- **🧠 Content Extraction**: Advanced HTML parsing using Selectolax for fast, accurate data extraction
- **🔗 Data Enrichment**: Pluggable enrichment providers (Crunchbase, LinkedIn, custom APIs)
- **📊 Quality Scoring**: Completeness and confidence metrics for extracted data
- **📝 Markdown Reports**: Beautiful, comprehensive company analysis reports
- **🔍 Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging
- **🚀 Production Ready**: Docker, Kubernetes, health checks, graceful shutdown
- **🧪 Well Tested**: Comprehensive test suite with 80%+ coverage

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│   Orchestrator  │───▶│   Web Crawler   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Content Extract │    │    Database     │
                       └─────────────────┘    │   (SQLAlchemy)  │
                                │             └─────────────────┘
                                ▼                        
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Enrichment    │───▶│    Providers    │
                       │    Manager      │    │ (Crunchbase,etc)│
                       └─────────────────┘    └─────────────────┘
                                │                        
                                ▼                        
                       ┌─────────────────┐              
                       │ Report Generator│              
                       └─────────────────┘              
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and Setup**
   ```bash
   git clone https://github.com/subslink326/job-url-analyzer-mcp.git
   cd job-url-analyzer-mcp
   poetry install
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**
   ```bash
   poetry run alembic upgrade head
   ```

4. **Run Development Server**
   ```bash
   poetry run python -m job_url_analyzer.main
   # Server starts at http://localhost:8000
   ```

### Docker Deployment

1. **Development**
   ```bash
   docker-compose up --build
   ```

2. **Production**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 📡 API Usage

### Analyze Job URL

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://company.com/jobs/software-engineer",
    "include_enrichment": true,
    "force_refresh": false
  }'
```

### Response Example

```json
{
  "profile_id": "123e4567-e89b-12d3-a456-426614174000",
  "source_url": "https://company.com/jobs/software-engineer",
  "company_profile": {
    "name": "TechCorp",
    "description": "Leading AI company...",
    "industry": "Technology",
    "employee_count": 150,
    "funding_stage": "Series B",
    "total_funding": 25.0,
    "headquarters": "San Francisco, CA",
    "tech_stack": ["Python", "React", "AWS"],
    "benefits": ["Health insurance", "Remote work"]
  },
  "completeness_score": 0.85,
  "confidence_score": 0.90,
  "processing_time_ms": 3450,
  "enrichment_sources": ["crunchbase"],
  "markdown_report": "# TechCorp - Company Analysis Report\n..."
}
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./data/job_analyzer.db` |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent HTTP requests | `10` |
| `REQUEST_TIMEOUT` | HTTP request timeout (seconds) | `30` |
| `CRAWL_DELAY` | Delay between requests (seconds) | `1.0` |
| `RESPECT_ROBOTS_TXT` | Respect robots.txt | `true` |
| `ENABLE_CRUNCHBASE` | Enable Crunchbase enrichment | `false` |
| `CRUNCHBASE_API_KEY` | Crunchbase API key | `""` |
| `DATA_RETENTION_DAYS` | Data retention period | `90` |

## 📊 Monitoring

### Metrics Endpoints

- **Health Check**: `GET /health`
- **Prometheus Metrics**: `GET /metrics`

### Key Metrics

- `job_analyzer_requests_total` - Total API requests
- `job_analyzer_analysis_success_total` - Successful analyses
- `job_analyzer_completeness_score` - Data completeness distribution
- `job_analyzer_crawl_requests_total` - Crawl requests by status
- `job_analyzer_enrichment_success_total` - Enrichment success by provider

## 🧪 Testing

### Run Tests

```bash
# Unit tests
poetry run pytest

# With coverage
poetry run pytest --cov=job_url_analyzer --cov-report=html

# Integration tests only
poetry run pytest -m integration

# Skip slow tests
poetry run pytest -m "not slow"
```

## 🚀 Deployment

### Kubernetes

```bash
# Apply manifests
kubectl apply -f kubernetes/

# Check deployment
kubectl get pods -l app=job-analyzer
kubectl logs -f deployment/job-analyzer
```

### Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates configured
- [ ] Monitoring dashboards set up
- [ ] Log aggregation configured
- [ ] Backup strategy implemented
- [ ] Rate limiting configured
- [ ] Resource limits set

## 🔧 Development

### Project Structure

```
job-url-analyzer/
├── src/job_url_analyzer/          # Main application code
│   ├── enricher/                  # Enrichment providers
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration
│   ├── models.py                  # Pydantic models
│   ├── database.py                # Database models
│   ├── crawler.py                 # Web crawler
│   ├── extractor.py               # Content extraction
│   ├── orchestrator.py            # Main orchestrator
│   └── report_generator.py        # Report generation
├── tests/                         # Test suite
├── alembic/                       # Database migrations
├── kubernetes/                    # K8s manifests
├── monitoring/                    # Monitoring configs
├── docker-compose.yml             # Development setup
├── docker-compose.prod.yml        # Production setup
└── Dockerfile                     # Container definition
```

### Code Quality

The project uses:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking
- **Pre-commit** hooks for quality gates

```bash
# Setup pre-commit
poetry run pre-commit install

# Run quality checks
poetry run black .
poetry run ruff check .
poetry run mypy src/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`poetry run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: This README and inline code comments
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and community

---

**Built with ❤️ using FastAPI, SQLAlchemy, and modern Python tooling.**
