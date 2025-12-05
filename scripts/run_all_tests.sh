#!/bin/bash
# Run all service tests with coverage

set -e

echo "========================================="
echo "  Running All Service Tests"
echo "========================================="
echo ""

SERVICES=("api-gateway" "worker-service")
FAILED_SERVICES=()
TOTAL_COVERAGE=0
SERVICE_COUNT=0

for service in "${SERVICES[@]}"; do
    echo "----------------------------------------"
    echo "Testing: $service"
    echo "----------------------------------------"

    cd "services/$service"

    # Install test dependencies
    if [ -f "requirements-test.txt" ]; then
        echo "Installing test dependencies..."
        pip install -q -r requirements-test.txt
    fi

    # Run tests
    if python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=xml --tb=short; then
        echo "✅ $service tests passed"

        # Extract coverage percentage if available
        if [ -f ".coverage" ]; then
            COVERAGE=$(python -m coverage report | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
            echo "   Coverage: ${COVERAGE}%"
            TOTAL_COVERAGE=$(echo "$TOTAL_COVERAGE + $COVERAGE" | bc)
            SERVICE_COUNT=$((SERVICE_COUNT + 1))
        fi
    else
        echo "❌ $service tests failed"
        FAILED_SERVICES+=("$service")
    fi

    cd ../..
    echo ""
done

echo "========================================="
echo "  Test Summary"
echo "========================================="
echo ""

if [ ${#FAILED_SERVICES[@]} -eq 0 ]; then
    echo "✅ All services passed tests!"
else
    echo "❌ Failed services:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo "   - $service"
    done
fi

if [ $SERVICE_COUNT -gt 0 ]; then
    AVG_COVERAGE=$(echo "scale=2; $TOTAL_COVERAGE / $SERVICE_COUNT" | bc)
    echo ""
    echo "📊 Average Coverage: ${AVG_COVERAGE}%"
fi

echo ""
echo "========================================="

# Exit with error if any service failed
if [ ${#FAILED_SERVICES[@]} -ne 0 ]; then
    exit 1
fi

exit 0
