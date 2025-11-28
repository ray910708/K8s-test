#!/bin/bash

# Cleanup all Kubernetes resources
# This script removes all deployed resources from the cluster

set -e

echo "========================================="
echo "Cleaning up Kubernetes Resources"
echo "========================================="

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Confirm deletion
echo -e "${YELLOW}This will delete all resources in the microservices-demo namespace.${NC}"
read -p "Are you sure you want to continue? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo -e "${RED}Deleting namespace microservices-demo...${NC}"
kubectl delete namespace microservices-demo

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
echo ""
echo "All resources have been removed from the cluster."
echo ""
echo "To verify:"
echo "  kubectl get namespace microservices-demo"
echo ""
