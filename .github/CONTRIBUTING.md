# Contributing to K8s-test

Thank you for your interest in contributing to the Microservices Health Monitor project! This document provides guidelines for contributing.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/K8s-test.git`
3. Add upstream remote: `git remote add upstream https://github.com/ORIGINAL_OWNER/K8s-test.git`
4. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl

### Local Setup

```bash
# Install dependencies for a service
cd services/api-gateway
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run tests
pytest

# Run locally with Docker Compose
docker-compose up
```

### Running in Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
```

## Making Changes

### Branch Naming Convention

- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation changes
- `test/` - Test improvements

Example: `feature/add-rate-limiting`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(api-gateway): add rate limiting

Implement Redis-based rate limiting using sliding window algorithm.
Limits: 100 requests per minute per client IP.

Closes #123
```

## Testing

### Running Tests

```bash
# Run tests for a specific service
cd services/api-gateway
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run all service tests
./scripts/run_all_tests.sh
```

### Test Requirements

- All new features must include unit tests
- Maintain test coverage above 70%
- Integration tests for external dependencies
- Update existing tests when changing functionality

### Test Structure

```python
@pytest.mark.unit
def test_feature_name():
    """Test description."""
    # Arrange
    expected = "value"

    # Act
    result = function_to_test()

    # Assert
    assert result == expected
```

## Submitting Changes

### Pull Request Process

1. **Update your branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests locally**
   ```bash
   pytest
   flake8
   ```

3. **Push your changes**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request**
   - Use the PR template
   - Link related issues
   - Add relevant labels
   - Request reviews

5. **Address Review Comments**
   - Make requested changes
   - Push updates to the same branch
   - Re-request review

### PR Requirements

- [ ] All tests pass
- [ ] Code coverage maintained or improved
- [ ] Linter checks pass
- [ ] Security scans pass
- [ ] Documentation updated
- [ ] Changelog updated (if applicable)

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Maximum line length: 127 characters
- Use type hints where appropriate

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Security check
bandit -r .

# Dependency check
safety check
```

### Documentation

- Add docstrings to all public functions/classes
- Update README.md when adding features
- Keep API documentation current
- Comment complex logic

Example docstring:
```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of the function.

    Detailed description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### Docker Best Practices

- Use multi-stage builds
- Minimize layer count
- Don't run as root
- Use .dockerignore
- Pin base image versions

### Kubernetes Best Practices

- Define resource limits
- Use health checks
- Implement graceful shutdown
- Use ConfigMaps and Secrets
- Label all resources

## Security

### Reporting Security Issues

**Do not open public issues for security vulnerabilities.**

Email security concerns to: [security email]

### Security Checklist

- [ ] No secrets in code or commits
- [ ] Input validation implemented
- [ ] Output sanitization implemented
- [ ] Dependencies scanned for vulnerabilities
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Authentication/authorization checked

## Review Process

### For Contributors

1. Self-review your code before submitting
2. Respond to review comments promptly
3. Be open to feedback and suggestions
4. Test your changes thoroughly

### For Reviewers

1. Review within 2 business days
2. Provide constructive feedback
3. Approve or request changes
4. Verify CI checks pass

## Questions?

- Create a [Discussion](https://github.com/OWNER/K8s-test/discussions)
- Join our [Slack/Discord] (if applicable)
- Check existing [Issues](https://github.com/OWNER/K8s-test/issues)

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing! 🎉
