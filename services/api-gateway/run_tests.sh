#!/bin/bash
# Test runner script for API Gateway

set -e

echo "=== Running API Gateway Tests ==="
echo ""

# Install test dependencies if not already installed
echo "Installing test dependencies..."
pip install -q -r requirements-test.txt

echo ""
echo "Running pytest with coverage..."
python -m pytest tests/ \
    -v \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    --tb=short

echo ""
echo "=== Test Results ==="
echo "HTML coverage report: htmlcov/index.html"
echo "XML coverage report: coverage.xml"
