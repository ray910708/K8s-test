#!/bin/bash

# Deploy all Kubernetes resources
# This script deploys the microservices to a Kubernetes cluster

set -e

echo "========================================="
echo "Deploying to Kubernetes"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Deploy base resources
echo -e "${BLUE}Creating namespace...${NC}"
kubectl apply -f k8s/namespace.yaml
echo -e "${GREEN}✓ Namespace created${NC}"

echo -e "${BLUE}Creating ConfigMap...${NC}"
kubectl apply -f k8s/configmap.yaml
echo -e "${GREEN}✓ ConfigMap created${NC}"

echo -e "${BLUE}Creating Secrets...${NC}"
kubectl apply -f k8s/secrets.yaml
echo -e "${GREEN}✓ Secrets created${NC}"

# Deploy Redis
echo -e "${BLUE}Deploying Redis...${NC}"
kubectl apply -f k8s/redis/
echo -e "${GREEN}✓ Redis deployed${NC}"

# Wait a bit for Redis to be ready
echo -e "${YELLOW}Waiting for Redis to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=redis -n microservices-demo --timeout=60s || true

# Deploy services
echo -e "${BLUE}Deploying API Gateway...${NC}"
kubectl apply -f k8s/api-gateway/deployment.yaml
kubectl apply -f k8s/api-gateway/service.yaml
echo -e "${GREEN}✓ API Gateway deployed${NC}"

echo -e "${BLUE}Deploying Worker Service...${NC}"
kubectl apply -f k8s/worker-service/deployment.yaml
kubectl apply -f k8s/worker-service/service.yaml
echo -e "${GREEN}✓ Worker Service deployed${NC}"

echo -e "${BLUE}Deploying Dashboard...${NC}"
kubectl apply -f k8s/dashboard/deployment.yaml
kubectl apply -f k8s/dashboard/service.yaml
echo -e "${GREEN}✓ Dashboard deployed${NC}"

# Deploy HPA
echo -e "${BLUE}Deploying HPA configurations...${NC}"
kubectl apply -f k8s/api-gateway/hpa.yaml || echo -e "${YELLOW}Warning: HPA requires metrics-server${NC}"
kubectl apply -f k8s/worker-service/hpa.yaml || echo -e "${YELLOW}Warning: HPA requires metrics-server${NC}"
echo -e "${GREEN}✓ HPA configurations applied${NC}"

# Deploy Ingress
echo -e "${BLUE}Deploying Ingress...${NC}"
kubectl apply -f k8s/ingress.yaml || echo -e "${YELLOW}Warning: Ingress requires ingress controller${NC}"
echo -e "${GREEN}✓ Ingress deployed${NC}"

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "To check the status:"
echo "  kubectl get pods -n microservices-demo"
echo "  kubectl get svc -n microservices-demo"
echo "  kubectl get ingress -n microservices-demo"
echo ""
echo "To view logs:"
echo "  kubectl logs -f -l app=api-gateway -n microservices-demo"
echo "  kubectl logs -f -l app=worker-service -n microservices-demo"
echo "  kubectl logs -f -l app=dashboard -n microservices-demo"
echo ""
echo "To access the dashboard (if using Minikube):"
echo "  minikube service dashboard-service --namespace=microservices-demo"
echo ""
