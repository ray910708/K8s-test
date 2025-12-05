# 部署指南

完整的 Kubernetes 微服務專案部署指南，涵蓋本地開發、測試和生產環境。

## 目錄

- [前置需求](#前置需求)
- [本地開發部署（Minikube）](#本地開發部署minikube)
- [雲端生產部署](#雲端生產部署)
- [部署驗證](#部署驗證)
- [故障排查](#故障排查)
- [升級與回滾](#升級與回滾)

## 前置需求

### 必要工具

- **Docker**: 19.03+
- **Kubernetes**: 1.28+
- **kubectl**: 1.28+
- **Minikube**: 1.32+ (本地開發)
- **Python**: 3.11+ (本地測試)
- **Git**: 2.30+

### 可選工具

- **helm**: 3.10+ (Helm charts 部署)
- **k9s**: Kubernetes CLI 管理工具
- **kubectx/kubens**: 快速切換 context 和 namespace

### 安裝工具

\`\`\`bash
# macOS
brew install kubectl minikube docker kubernetes-cli k9s

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Windows (使用 Chocolatey)
choco install kubernetes-cli minikube docker-desktop
\`\`\`

### 驗證安裝

\`\`\`bash
docker --version
kubectl version --client
minikube version
python --version
\`\`\`

## 本地開發部署（Minikube）

### 1. 啟動 Minikube

\`\`\`bash
# 啟動 Minikube（分配足夠資源）
minikube start \\
  --cpus=4 \\
  --memory=8192 \\
  --disk-size=20g \\
  --driver=docker \\
  --kubernetes-version=v1.28.0

# 啟用必要的 addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable storage-provisioner

# 驗證 Minikube 狀態
minikube status
kubectl cluster-info
\`\`\`

### 2. 配置 Docker 環境

使用 Minikube 的 Docker daemon 構建鏡像：

\`\`\`bash
# 配置 Docker 環境變量
eval $(minikube docker-env)

# 驗證（應該看到 Minikube 的 Docker 容器）
docker ps
\`\`\`

**重要**: 每次開啟新終端都需要執行 \`eval $(minikube docker-env)\`

### 3. 構建 Docker 鏡像

\`\`\`bash
# 使用腳本一鍵構建所有鏡像
chmod +x scripts/build-images.sh
./scripts/build-images.sh

# 或手動構建單個服務
cd services/api-gateway
docker build -t api-gateway:latest .

cd ../worker-service
docker build -t worker-service:latest .

cd ../dashboard
docker build -t dashboard:latest .

# 驗證鏡像
docker images | grep -E "api-gateway|worker-service|dashboard"
\`\`\`

### 4. 部署到 Kubernetes

#### 方法 1: 使用部署腳本（推薦）

\`\`\`bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
\`\`\`

#### 方法 2: 手動部署

\`\`\`bash
# 1. 創建命名空間
kubectl apply -f k8s/namespace.yaml

# 2. 創建 PriorityClass（必須先創建，因為其他資源依賴它）
kubectl apply -f k8s/priority-classes.yaml

# 3. 創建 ResourceQuota 和 LimitRange
kubectl apply -f k8s/resource-quota.yaml
kubectl apply -f k8s/limit-range.yaml

# 4. 創建 ConfigMap 和 Secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 5. 部署 Redis（其他服務的依賴）
kubectl apply -f k8s/redis/

# 6. 等待 Redis 就緒
kubectl wait --for=condition=ready pod -l app=redis -n microservices-demo --timeout=300s

# 7. 部署應用服務
kubectl apply -f k8s/api-gateway/
kubectl apply -f k8s/worker-service/
kubectl apply -f k8s/dashboard/

# 8. 部署網絡策略
kubectl apply -f k8s/network-policies/

# 9. 部署 Ingress
kubectl apply -f k8s/ingress.yaml

# 10. 部署監控（可選）
kubectl apply -f k8s/monitoring/
\`\`\`

### 5. 查看部署狀態

\`\`\`bash
# 查看所有資源
kubectl get all -n microservices-demo

# 查看 Pod 狀態
kubectl get pods -n microservices-demo

# 查看服務
kubectl get svc -n microservices-demo

# 查看 Ingress
kubectl get ingress -n microservices-demo

# 查看 HPA
kubectl get hpa -n microservices-demo

# 查看 PDB
kubectl get pdb -n microservices-demo

# 實時監控 Pod 狀態
watch kubectl get pods -n microservices-demo
\`\`\`

### 6. 訪問服務

#### 方法 1: 使用 Minikube Service（推薦）

\`\`\`bash
# 訪問 Dashboard
minikube service dashboard-service -n microservices-demo

# 訪問 API Gateway
minikube service api-gateway-service -n microservices-demo

# 訪問 Prometheus
minikube service prometheus -n microservices-demo

# 訪問 Grafana
minikube service grafana -n microservices-demo
\`\`\`

#### 方法 2: 使用 Port Forward

\`\`\`bash
# Dashboard (port 3000)
kubectl port-forward -n microservices-demo svc/dashboard-service 3000:3000

# API Gateway (port 8080)
kubectl port-forward -n microservices-demo svc/api-gateway-service 8080:8080

# Prometheus (port 9090)
kubectl port-forward -n microservices-demo svc/prometheus 9090:9090

# Grafana (port 3000)
kubectl port-forward -n microservices-demo svc/grafana 3000:3000

# 在瀏覽器訪問
# Dashboard: http://localhost:3000
# API Gateway: http://localhost:8080
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
\`\`\`

#### 方法 3: 使用 Ingress（需要配置 /etc/hosts）

\`\`\`bash
# 獲取 Minikube IP
minikube ip

# 添加到 /etc/hosts
echo "$(minikube ip) microservices-demo.local" | sudo tee -a /etc/hosts

# 訪問
# http://microservices-demo.local
\`\`\`

### 7. 測試部署

\`\`\`bash
# 測試 API Gateway
curl http://localhost:8080/health/live
curl http://localhost:8080/health/ready
curl http://localhost:8080/api/status

# 測試 Dashboard
curl http://localhost:3000/health/live

# 測試 Worker Service
kubectl port-forward -n microservices-demo svc/worker-service 8081:8081
curl http://localhost:8081/health/live

# 查看日誌
kubectl logs -n microservices-demo -l app=api-gateway --tail=50
kubectl logs -n microservices-demo -l app=worker-service --tail=50
kubectl logs -n microservices-demo -l app=dashboard --tail=50
\`\`\`

## 相關文檔

- [可觀測性配置](OBSERVABILITY.md)
- [資源優化指南](RESOURCE-OPTIMIZATION.md)
- [測試指南](TESTING.md)
- [CI/CD 文檔](CI-CD.md)
