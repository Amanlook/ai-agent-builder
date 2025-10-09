# Contributing to API Debugger

Thank you for your interest in contributing to API Debugger! This document provides guidelines and instructions for contributing.

## 🚀 Quick Start for Contributors

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/api-debugger.git
cd api-debugger

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api_debugger --cov-report=html --cov-report=term

# Run specific test files
pytest tests/test_client.py -v

# Run and watch for changes
pytest-watch
```

## 🐛 Bug Reports

When filing an issue, please include:

- Python version
- Operating system
- API Debugger version
- Minimal code example that reproduces the issue
- Full error traceback
- Expected vs actual behavior

## 💡 Feature Requests

We welcome feature requests! Please:

- Check existing issues first
- Describe the use case
- Explain why it would be useful
- Consider backward compatibility

## 🔧 Development Guidelines

### Code Style

We use several tools to maintain code quality:

```bash
# Format code with Black
black api_debugger/ tests/ examples/

# Sort imports with isort
isort api_debugger/ tests/ examples/

# Type checking with mypy
mypy api_debugger/

# Linting with flake8
flake8 api_debugger/ tests/
```

### Testing Guidelines

- Write tests for all new features
- Maintain or improve test coverage
- Use descriptive test names
- Mock external dependencies
- Test both success and failure cases

### Commit Guidelines

We follow conventional commits:

```bash
feat: add support for custom formatters
fix: resolve masking issue with nested objects  
docs: update installation instructions
test: add tests for retry mechanism
refactor: simplify configuration logic
```

## 📦 Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create pull request
5. Tag release after merge
6. Publish to PyPI (maintainers only)

## 🤝 Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Commit your changes
8. Push to your fork
9. Create a Pull Request

### PR Checklist

- [ ] Tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Code follows style guidelines
- [ ] No breaking changes (or clearly documented)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🆘 Getting Help

- Check the documentation
- Search existing issues
- Ask in GitHub Discussions
- Contact maintainers

Thank you for contributing! 🎉