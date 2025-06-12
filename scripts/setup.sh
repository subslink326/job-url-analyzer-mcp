#!/bin/bash
# Setup script for Job URL Analyzer MCP Server

set -e

echo "🚀 Setting up Job URL Analyzer MCP Server..."

# Check if Python 3.11+ is installed
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11+ is required but not installed."
    echo "Please install Python 3.11 or later."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies
echo "📚 Installing dependencies..."
poetry install

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
poetry run pre-commit install

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs

# Copy environment file
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your configuration."
fi

# Run database migrations
echo "🗄️ Setting up database..."
poetry run alembic upgrade head

# Run tests to verify setup
echo "🧪 Running tests..."
poetry run pytest --tb=short

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run 'make run' to start the development server"
echo "3. Visit http://localhost:8000/docs for API documentation"
echo "4. Run 'make test' to run the test suite"
echo ""
echo "For production deployment:"
echo "1. Use docker-compose.prod.yml"
echo "2. Configure environment variables"
echo "3. Set up SSL certificates"
echo "4. Configure monitoring dashboards"