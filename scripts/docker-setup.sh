#!/bin/bash
# Docker setup script for Job URL Analyzer MCP Server

set -e

echo "🐳 Setting up Docker environment for Job URL Analyzer..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed."
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs monitoring/grafana/{dashboards,datasources}

# Copy environment file for Docker
if [ ! -f .env.docker ]; then
    echo "⚙️ Creating .env.docker file..."
    cp .env.example .env.docker
    echo "Please edit .env.docker file with your Docker configuration."
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

# Start the development environment
echo "🚀 Starting development environment..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Job Analyzer service is healthy!"
else
    echo "❌ Job Analyzer service is not responding."
    echo "Check logs with: docker-compose logs job-analyzer"
fi

echo "✅ Docker setup complete!"
echo ""
echo "Services available:"
echo "- Job Analyzer API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo "- Health Check: http://localhost:8000/health"
echo "- Metrics: http://localhost:8000/metrics"
echo ""
echo "Optional services (use --profile flag):"
echo "- PostgreSQL: docker-compose --profile postgres up -d"
echo "- Monitoring: docker-compose --profile monitoring up -d"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo ""
echo "Useful commands:"
echo "- View logs: docker-compose logs -f"
echo "- Stop services: docker-compose down"
echo "- Rebuild: docker-compose build --no-cache"