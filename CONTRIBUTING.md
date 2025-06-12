# Contributing to Job URL Analyzer MCP Server

We love contributions! This document provides guidelines for contributing to the Job URL Analyzer MCP Server.

## 🚀 Quick Start

1. **Fork the repository**
   ```bash
   git clone https://github.com/subslink326/job-url-analyzer-mcp.git
   cd job-url-analyzer-mcp
   ```

2. **Set up development environment**
   ```bash
   make setup-dev
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

4. **Make your changes and test**
   ```bash
   make test
   make lint
   ```

5. **Commit and push**
   ```bash
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add docstrings for all public functions
- Keep functions focused and single-purpose
- Use descriptive variable names

### Testing
- Write tests for all new functionality
- Maintain 80%+ test coverage
- Include both positive and negative test cases
- Use pytest fixtures for common test data
- Mock external dependencies

### Documentation
- Update README.md for new features
- Add inline comments for complex logic
- Update API documentation
- Include examples in docstrings

### Commits
- Use conventional commit messages
- Keep commits atomic and focused
- Include tests in the same commit as the feature

## 🏗️ Architecture

### Adding New Enrichment Providers

1. Create a new provider class inheriting from `EnrichmentProvider`:
   ```python
   class MyProvider(EnrichmentProvider):
       def __init__(self):
           super().__init__("my_provider", enabled=settings.ENABLE_MY_PROVIDER)
       
       def can_enrich(self, company_data: Dict[str, Any]) -> bool:
           # Check if provider can enrich this data
           return bool(company_data.get("name"))
       
       async def enrich(self, company_data: Dict[str, Any]) -> EnrichmentResult:
           # Implement enrichment logic
           pass
   ```

2. Add the provider to `EnrichmentManager`
3. Add configuration settings
4. Write comprehensive tests

### Adding New Content Extractors

1. Extend the `ContentExtractor` class
2. Add extraction methods following the `_extract_*` pattern
3. Update the main `extract_info` method
4. Add tests with mock HTML content

## 🧪 Testing

### Running Tests
```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
poetry run pytest tests/test_extractor.py

# With markers
poetry run pytest -m "not slow"
```

### Test Structure
- Unit tests: Test individual components
- Integration tests: Test component interactions
- End-to-end tests: Test full workflows

## 📦 Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a pull request
4. After merge, create a release tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
5. GitHub Actions will build and publish automatically

## 🐛 Bug Reports

When reporting bugs, please include:
- Python version
- OS and architecture
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages
- Minimal reproduction example

## 💡 Feature Requests

For feature requests:
- Describe the use case
- Explain the expected behavior
- Consider backward compatibility
- Propose implementation approach

## 🔒 Security

For security issues:
- DO NOT open a public issue
- Email security concerns privately
- Include detailed information
- Allow time for response before disclosure

## 📝 Code Review Process

1. All changes require pull request review
2. At least one approving review required
3. All CI checks must pass
4. No merge conflicts
5. Up-to-date with main branch

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

## 🤝 Community

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and best practices
- Provide constructive feedback
- Celebrate contributions

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Poetry Documentation](https://python-poetry.org/docs/)

Thank you for contributing! 🎉