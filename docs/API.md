# Job URL Analyzer API Documentation

This document provides detailed information about the Job URL Analyzer MCP Server API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, you should implement proper authentication and authorization.

## Endpoints

### Health Check

**GET** `/health`

Check the health status of the service.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-06-12T10:30:00Z"
}
```

### Metrics

**GET** `/metrics`

Prometheus metrics endpoint for monitoring.

**Response:**
```
# HELP job_analyzer_requests_total Total number of analysis requests
# TYPE job_analyzer_requests_total counter
job_analyzer_requests_total{endpoint="analyze_job_url",method="POST",status_code="200"} 42
...
```

### Analyze Job URL

**POST** `/analyze`

Analyze a job URL and extract company information.

**Request Body:**
```json
{
  "url": "https://company.com/jobs/software-engineer",
  "include_enrichment": true,
  "force_refresh": false
}
```

**Parameters:**
- `url` (required): Job posting or company URL to analyze
- `include_enrichment` (optional, default: true): Whether to include data enrichment from external providers
- `force_refresh` (optional, default: false): Force re-analysis even if cached data exists

**Response:**
```json
{
  "profile_id": "123e4567-e89b-12d3-a456-426614174000",
  "source_url": "https://company.com/jobs/software-engineer",
  "company_profile": {
    "name": "TechCorp",
    "description": "Leading AI company building the future of automation",
    "industry": "Technology",
    "website": "https://techcorp.com",
    "employee_count": 150,
    "employee_count_range": "51-200",
    "funding_stage": "Series B",
    "total_funding": 25.0,
    "headquarters": "San Francisco, CA",
    "locations": ["San Francisco, CA", "New York, NY"],
    "tech_stack": ["Python", "React", "AWS", "PostgreSQL"],
    "benefits": ["Health insurance", "Remote work", "Stock options"],
    "culture_keywords": ["Innovative", "Fast-paced", "Collaborative"],
    "linkedin_url": "https://linkedin.com/company/techcorp",
    "twitter_url": "https://twitter.com/techcorp",
    "logo_url": "https://techcorp.com/logo.png",
    "founded_year": 2020
  },
  "completeness_score": 0.85,
  "confidence_score": 0.90,
  "analysis_timestamp": "2025-06-12T10:30:00Z",
  "processing_time_ms": 3450,
  "enrichment_sources": ["crunchbase"],
  "enrichment_errors": [],
  "markdown_report": "# TechCorp - Company Analysis Report\n\n*Generated on 2025-06-12 10:30:00 UTC*\n\n## Executive Summary\n\nTechCorp is a leading artificial intelligence company building the future of automation in the technology industry founded 5 years ago (2020) headquartered in San Francisco, CA..."
}
```

## Error Responses

### 422 Validation Error

Returned when request data is invalid.

```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "invalid or missing URL scheme",
      "type": "value_error.url.scheme"
    }
  ]
}
```

### 500 Internal Server Error

Returned when analysis fails.

```json
{
  "detail": "Analysis failed: Failed to crawl any content from the provided URL"
}
```

## Data Models

### CompanyProfile

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Company name |
| `description` | string | Company description |
| `industry` | string | Industry |
| `website` | string | Company website URL |
| `employee_count` | integer | Number of employees |
| `employee_count_range` | string | Employee count range (e.g., "51-200") |
| `funding_stage` | string | Funding stage (e.g., "Series B") |
| `total_funding` | number | Total funding amount in millions |
| `headquarters` | string | Headquarters location |
| `locations` | array[string] | Office locations |
| `tech_stack` | array[string] | Technology stack |
| `benefits` | array[string] | Company benefits |
| `culture_keywords` | array[string] | Culture keywords |
| `linkedin_url` | string | LinkedIn company page URL |
| `twitter_url` | string | Twitter profile URL |
| `logo_url` | string | Company logo URL |
| `founded_year` | integer | Year founded |

### AnalysisResponse

| Field | Type | Description |
|-------|------|-------------|
| `profile_id` | UUID | Unique profile identifier |
| `source_url` | string | Original URL analyzed |
| `company_profile` | CompanyProfile | Extracted company profile |
| `completeness_score` | number | Data completeness score (0-1) |
| `confidence_score` | number | Extraction confidence score (0-1) |
| `analysis_timestamp` | datetime | When the analysis was performed |
| `processing_time_ms` | integer | Processing time in milliseconds |
| `enrichment_sources` | array[string] | External data sources used |
| `enrichment_errors` | array[string] | Errors during enrichment |
| `markdown_report` | string | Markdown-formatted analysis report |

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 10 requests per second per IP address
- Burst allowance of 20 requests

When rate limited, you'll receive a 429 status code.

## Examples

### Analyze a Job Posting

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://careers.openai.com/jobs/software-engineer",
    "include_enrichment": true
  }'
```

### Force Refresh Analysis

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://careers.openai.com/jobs/software-engineer",
    "force_refresh": true
  }'
```

### Analyze Without Enrichment

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://careers.openai.com/jobs/software-engineer",
    "include_enrichment": false
  }'
```

## Interactive Documentation

When running the server, visit `/docs` for interactive API documentation powered by Swagger UI, or `/redoc` for ReDoc-style documentation.