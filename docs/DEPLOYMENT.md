# Deployment Guide

This guide covers various deployment options for the Job URL Analyzer MCP Server.

## 🐳 Docker Deployment

### Development

```bash
# Clone the repository
git clone https://github.com/subslink326/job-url-analyzer-mcp.git
cd job-url-analyzer-mcp

# Start with Docker Compose
docker-compose up --build
```

The service will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Production

```bash
# Copy and configure environment
cp .env.production .env
# Edit .env with your production settings

# Start production stack
docker-compose -f docker-compose.prod.yml up -d
```

### With Monitoring

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d
```

Access monitoring:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Ingress controller (nginx recommended)
- cert-manager for SSL (optional)

### Deploy

1. **Customize secrets**:
   ```bash
   # Edit kubernetes/secrets.yaml with your API keys
   kubectl apply -f kubernetes/secrets.yaml
   ```

2. **Deploy the application**:
   ```bash
   kubectl apply -f kubernetes/
   ```

3. **Verify deployment**:
   ```bash
   kubectl get pods -l app=job-analyzer
   kubectl logs -f deployment/job-analyzer
   ```

4. **Access the service**:
   ```bash
   # Port forward for testing
   kubectl port-forward service/job-analyzer-service 8000:80
   
   # Or configure ingress with your domain
   ```

### Scaling

```bash
# Scale replicas
kubectl scale deployment/job-analyzer --replicas=5

# Auto-scaling (optional)
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: job-analyzer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: job-analyzer
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF
```

## 🌐 Manual Deployment

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL (optional, SQLite works for small deployments)
- Nginx (for production)

### Setup

1. **Install dependencies**:
   ```bash
   git clone https://github.com/subslink326/job-url-analyzer-mcp.git
   cd job-url-analyzer-mcp
   poetry install --only=main
   ```

2. **Configure environment**:
   ```bash
   cp .env.production .env
   # Edit .env with your settings
   ```

3. **Run migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

4. **Start the service**:
   ```bash
   poetry run uvicorn job_url_analyzer.main:app --host 0.0.0.0 --port 8000
   ```

### Systemd Service

Create `/etc/systemd/system/job-analyzer.service`:

```ini
[Unit]
Description=Job URL Analyzer MCP Server
After=network.target

[Service]
Type=exec
User=job-analyzer
Group=job-analyzer
WorkingDirectory=/opt/job-analyzer
Environment=PATH=/opt/job-analyzer/.venv/bin
ExecStart=/opt/job-analyzer/.venv/bin/uvicorn job_url_analyzer.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable job-analyzer
sudo systemctl start job-analyzer
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `DEBUG` | Enable debug mode | `false` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DATABASE_URL` | Database connection | SQLite |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent requests | `10` |
| `CRAWL_DELAY` | Delay between requests | `1.0` |
| `ENABLE_CRUNCHBASE` | Enable Crunchbase enrichment | `false` |
| `CRUNCHBASE_API_KEY` | Crunchbase API key | |

### Database Options

**SQLite (Development)**:
```bash
DATABASE_URL=sqlite+aiosqlite:///./data/job_analyzer.db
```

**PostgreSQL (Production)**:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
```

### SSL Configuration

For production, use nginx with SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourcompany.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoring Setup

### Prometheus

1. **Configure Prometheus** (`prometheus.yml`):
   ```yaml
   scrape_configs:
     - job_name: 'job-analyzer'
       static_configs:
         - targets: ['localhost:8000']
       metrics_path: '/metrics'
   ```

2. **Key metrics to monitor**:
   - `job_analyzer_requests_total`
   - `job_analyzer_analysis_success_total`
   - `job_analyzer_completeness_score`
   - `job_analyzer_crawl_duration_seconds`

### Grafana

1. **Import dashboard**: Use the provided dashboard JSON
2. **Set up alerts** for:
   - High error rate
   - Long response times
   - Low completeness scores

### Logging

Configure log aggregation:

**Fluentd/Fluent Bit**:
```yaml
[INPUT]
    Name tail
    Path /app/logs/*.log
    Parser json

[OUTPUT]
    Name elasticsearch
    Host elasticsearch
    Port 9200
```

## 🚀 Performance Tuning

### Application

1. **Adjust concurrency**:
   ```bash
   MAX_CONCURRENT_REQUESTS=20
   ```

2. **Database connection pooling**:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:pass@host/db?pool_size=20&max_overflow=30
   ```

3. **Worker processes** (for high load):
   ```bash
   uvicorn job_url_analyzer.main:app --workers 4
   ```

### Infrastructure

1. **Resource limits** (Kubernetes):
   ```yaml
   resources:
     limits:
       cpu: "2"
       memory: "2Gi"
     requests:
       cpu: "1"
       memory: "1Gi"
   ```

2. **Nginx caching**:
   ```nginx
   location /analyze {
       proxy_cache my_cache;
       proxy_cache_valid 200 5m;
       proxy_pass http://backend;
   }
   ```

## 🔒 Security

### Basic Security

1. **Use HTTPS** in production
2. **Set up firewall** rules
3. **Regular updates** of dependencies
4. **Secure API keys** in environment variables

### Advanced Security

1. **Rate limiting** with nginx:
   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   limit_req zone=api burst=20 nodelay;
   ```

2. **API authentication** (implement as needed)
3. **Network policies** (Kubernetes)
4. **Pod security policies**

## 🔄 Backup and Recovery

### Database Backup

**PostgreSQL**:
```bash
# Backup
pg_dump -h host -U user database > backup.sql

# Restore
psql -h host -U user database < backup.sql
```

**SQLite**:
```bash
# Backup
cp data/job_analyzer.db backup/job_analyzer_$(date +%Y%m%d).db
```

### Application Data

1. **Persistent volumes** (Kubernetes)
2. **Regular snapshots**
3. **Offsite backups**

## 🆘 Troubleshooting

### Common Issues

**Service won't start**:
```bash
# Check logs
docker-compose logs job-analyzer
kubectl logs deployment/job-analyzer

# Check health
curl http://localhost:8000/health
```

**Database connection issues**:
```bash
# Test connection
poetry run python -c "from job_url_analyzer.database import engine; print('OK')"
```

**High memory usage**:
- Reduce `MAX_CONCURRENT_REQUESTS`
- Increase resource limits
- Check for memory leaks

**Slow responses**:
- Check `CRAWL_DELAY` setting
- Monitor external API rate limits
- Review database query performance

### Debug Mode

```bash
# Enable debug logging
DEBUG=true
LOG_LEVEL=DEBUG

# Run with debug
poetry run uvicorn job_url_analyzer.main:app --reload --log-level debug
```

For more help, check the [Issues](https://github.com/subslink326/job-url-analyzer-mcp/issues) or create a new issue.