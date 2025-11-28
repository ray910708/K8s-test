#!/bin/bash

# Build Docker images for all services
# This script builds all Docker images locally

set -e

echo "========================================="
echo "Building Docker Images"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Build API Gateway
echo -e "${BLUE}Building API Gateway...${NC}"
docker build -t api-gateway:latest ./services/api-gateway
echo -e "${GREEN}✓ API Gateway built successfully${NC}"

# Build Worker Service
echo -e "${BLUE}Building Worker Service...${NC}"
docker build -t worker-service:latest ./services/worker-service
echo -e "${GREEN}✓ Worker Service built successfully${NC}"

# Build Dashboard
echo -e "${BLUE}Building Dashboard...${NC}"
docker build -t dashboard:latest ./services/dashboard
echo -e "${GREEN}✓ Dashboard built successfully${NC}"

echo ""
echo "========================================="
echo "All images built successfully!"
echo "========================================="
echo ""
echo "To view images:"
echo "  docker images | grep -E 'api-gateway|worker-service|dashboard'"
echo ""
