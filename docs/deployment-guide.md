# Deployment Guide

完整的部署指南，涵蓋本地開發環境和生產環境部署。

## 前置需求

### 必需工具

- **Docker**: >= 20.10
- **kubectl**: >= 1.26
- **Git**: >= 2.30

### 本地開發額外需求

- **Minikube**: >= 1.30 或
- **Kind**: >= 0.19 或
- **Docker Desktop** with Kubernetes enabled

### 生產環境額外需求

- Kubernetes cluster (自建或雲端)
- NGINX Ingress Controller
- Metrics Server (用於 HPA)
- Docker Hub 帳號（用於儲存 images）

## 本地開發部署

### 選項 1: 使用 Minikube（推薦）

#### 1. 安裝 Minikube

**macOS**:
```bash
brew install minikube
```

**Linux**:
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

**Windows**:
```bash
choco install minikube
```

#### 2. 啟動 Minikube

```bash
# 啟動 Minikube cluster（配置足夠的資源）
minikube start --cpus=4 --memory=8192 --driver=docker

# 驗證 cluster 運行
minikube status
kubectl cluster-info
```

#### 3. 啟用必要的 Addons

```bash
# 啟用 Ingress controller
minikube addons enable ingress

# 啟用 Metrics Server（用於 HPA）
minikube addons enable metrics-server

# 驗證 addons
minikube addons list
```

#### 4. 配置 Docker 環境

```bash
# 設定 Docker 使用 Minikube 的 Docker daemon
# 這樣建置的 images 會直接在 Minikube 中可用
eval $(minikube docker-env)

# 驗證（應該看到 Minikube 相關的容器）
docker ps
```

**重要**：這個設定只在當前終端有效。如果開新終端，需要重新執行。

#### 5. 建置 Docker Images

```bash
# 從專案根目錄執行
./scripts/build-images.sh

# 驗證 images 已建置
docker images | grep -E 'api-gateway|worker-service|dashboard'
```

你應該看到：
```
api-gateway       latest    <image-id>    <time>    <size>
worker-service    latest    <image-id>    <time>    <size>
dashboard         latest    <image-id>    <time>    <size>
```

#### 6. 部署到 Kubernetes

```bash
# 執行部署腳本
./scripts/deploy.sh
```

這個腳本會：
1. 創建 namespace
2. 應用 ConfigMap 和 Secrets
3. 部署 Redis
4. 部署三個微服務
5. 配置 HPA
6. 創建 Ingress

#### 7. 驗證部署

```bash
# 查看所有 Pods（應該都是 Running）
kubectl get pods -n microservices-demo

# 查看 Services
kubectl get svc -n microservices-demo

# 查看 Ingress
kubectl get ingress -n microservices-demo

# 查看 HPA（可能需要幾分鐘才有 metrics）
kubectl get hpa -n microservices-demo

# 查看詳細狀態
kubectl get all -n microservices-demo
```

預期輸出：
```
NAME                                  READY   STATUS    RESTARTS   AGE
pod/api-gateway-xxx                   1/1     Running   0          2m
pod/api-gateway-yyy                   1/1     Running   0          2m
pod/dashboard-xxx                     1/1     Running   0          2m
pod/dashboard-yyy                     1/1     Running   0          2m
pod/redis-xxx                         1/1     Running   0          2m
pod/worker-service-xxx                1/1     Running   0          2m
```

#### 8. 訪問應用

**方法 1: 使用 Minikube Service（最簡單）**

```bash
# 自動打開瀏覽器訪問 Dashboard
minikube service dashboard-service --namespace=microservices-demo

# 或者只獲取 URL
minikube service dashboard-service --namespace=microservices-demo --url
```

**方法 2: 通過 Ingress（推薦）**

```bash
# 獲取 Minikube IP
minikube ip

# 添加到 /etc/hosts
echo "$(minikube ip) microservices-demo.local" | sudo tee -a /etc/hosts

# 訪問
open http://microservices-demo.local
```

**方法 3: Port Forward**

```bash
# Dashboard
kubectl port-forward -n microservices-demo svc/dashboard-service 3000:3000

# API Gateway
kubectl port-forward -n microservices-demo svc/api-gateway-service 8080:8080

# 訪問
open http://localhost:3000
```

#### 9. 測試 API 端點

```bash
# API Gateway 健康檢查
curl http://localhost:8080/health/live
curl http://localhost:8080/health/ready

# 系統狀態
curl http://localhost:8080/api/status

# Prometheus metrics
curl http://localhost:8080/metrics
```

### 選項 2: 使用 Kind

```bash
# 安裝 Kind
brew install kind  # macOS
# 或從 https://kind.sigs.k8s.io/docs/user/quick-start/ 下載

# 創建 cluster
kind create cluster --name microservices-demo

# 安裝 NGINX Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# 等待 Ingress ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# 安裝 Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 然後按照 Minikube 的步驟 5-9 進行
```

## 生產環境部署

### 自建 Kubernetes Cluster 部署

#### 1. 前置檢查

確認你的 Kubernetes cluster 已安裝：

```bash
# 驗證 cluster 連接
kubectl cluster-info
kubectl get nodes

# 檢查 Ingress Controller
kubectl get pods -n ingress-nginx

# 檢查 Metrics Server
kubectl get deployment metrics-server -n kube-system
```

如果缺少組件，請安裝：

**安裝 NGINX Ingress Controller**:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.5/deploy/static/provider/cloud/deploy.yaml

# 等待就緒
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

**安裝 Metrics Server**:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 驗證
kubectl get deployment metrics-server -n kube-system
```

如果 Metrics Server 無法啟動（自簽名證書問題），修改部署：
```bash
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

#### 2. 準備 Docker Images

**建置並推送到 Docker Hub**:

```bash
# 登入 Docker Hub
docker login

# 設定你的 Docker Hub username
export DOCKER_USERNAME="your-dockerhub-username"

# 建置 images
./scripts/build-images.sh

# Tag images
docker tag api-gateway:latest $DOCKER_USERNAME/api-gateway:v1.0.0
docker tag worker-service:latest $DOCKER_USERNAME/worker-service:v1.0.0
docker tag dashboard:latest $DOCKER_USERNAME/dashboard:v1.0.0

# 推送到 Docker Hub
docker push $DOCKER_USERNAME/api-gateway:v1.0.0
docker push $DOCKER_USERNAME/worker-service:v1.0.0
docker push $DOCKER_USERNAME/dashboard:v1.0.0

# 也推送 latest tag
docker tag api-gateway:latest $DOCKER_USERNAME/api-gateway:latest
docker tag worker-service:latest $DOCKER_USERNAME/worker-service:latest
docker tag dashboard:latest $DOCKER_USERNAME/dashboard:latest

docker push $DOCKER_USERNAME/api-gateway:latest
docker push $DOCKER_USERNAME/worker-service:latest
docker push $DOCKER_USERNAME/dashboard:latest
```

#### 3. 更新 Kubernetes Manifests

更新所有 deployment.yaml 中的 image 名稱：

```bash
# 使用 sed 批量替換（macOS 使用 gsed）
sed -i "s|image: api-gateway:latest|image: $DOCKER_USERNAME/api-gateway:v1.0.0|g" k8s/api-gateway/deployment.yaml
sed -i "s|image: worker-service:latest|image: $DOCKER_USERNAME/worker-service:v1.0.0|g" k8s/worker-service/deployment.yaml
sed -i "s|image: dashboard:latest|image: $DOCKER_USERNAME/dashboard:v1.0.0|g" k8s/dashboard/deployment.yaml

# 改為從 registry 拉取
sed -i "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Always|g" k8s/*/deployment.yaml
```

或手動編輯每個 deployment.yaml：
```yaml
containers:
- name: api-gateway
  image: your-dockerhub-username/api-gateway:v1.0.0
  imagePullPolicy: Always
```

#### 4. 配置 Secrets（生產環境）

```bash
# 生成 Redis 密碼
REDIS_PASSWORD=$(openssl rand -base64 32)

# 創建 Secret
kubectl create secret generic app-secrets \
  --from-literal=REDIS_PASSWORD=$REDIS_PASSWORD \
  --from-literal=API_KEY=$(openssl rand -base64 32) \
  -n microservices-demo --dry-run=client -o yaml > k8s/secrets.yaml
```

#### 5. 部署應用

```bash
# 執行部署
./scripts/deploy.sh

# 或手動執行
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/redis/
kubectl apply -f k8s/api-gateway/
kubectl apply -f k8s/worker-service/
kubectl apply -f k8s/dashboard/
kubectl apply -f k8s/ingress.yaml
```

#### 6. 驗證部署

```bash
# 等待所有 Pods 就緒
kubectl wait --for=condition=ready pod --all -n microservices-demo --timeout=5m

# 檢查狀態
kubectl get pods -n microservices-demo
kubectl get svc -n microservices-demo
kubectl get ingress -n microservices-demo

# 查看 HPA
kubectl get hpa -n microservices-demo

# 檢查 Pods 日誌
kubectl logs -l app=api-gateway -n microservices-demo --tail=50
kubectl logs -l app=worker-service -n microservices-demo --tail=50
kubectl logs -l app=dashboard -n microservices-demo --tail=50
```

#### 7. 配置 DNS

**獲取 Ingress IP**:
```bash
kubectl get ingress -n microservices-demo
```

**配置 DNS**:
- 如果有域名，添加 A 記錄指向 Ingress IP
- 本地測試：添加到 `/etc/hosts`

```bash
# 獲取 Ingress External IP
INGRESS_IP=$(kubectl get ingress microservices-ingress -n microservices-demo -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# 添加到 hosts（本地測試）
echo "$INGRESS_IP microservices-demo.local" | sudo tee -a /etc/hosts
```

#### 8. 測試訪問

```bash
# 訪問 Dashboard
curl http://microservices-demo.local

# 訪問 API
curl http://microservices-demo.local/api/status

# 在瀏覽器中打開
open http://microservices-demo.local
```

## 使用 CI/CD 自動部署

### 設置 GitHub Secrets

在 GitHub repository 設置中添加以下 secrets：

1. **DOCKER_HUB_USERNAME**: 你的 Docker Hub 用戶名
2. **DOCKER_HUB_TOKEN**: Docker Hub access token
3. **KUBE_CONFIG**: Kubernetes config 文件（base64 編碼）

**獲取 KUBE_CONFIG**:
```bash
# 獲取當前的 kubeconfig
cat ~/.kube/config | base64

# 或指定特定的 config
cat /path/to/your/kubeconfig | base64
```

### 觸發 CI/CD

```bash
# 推送到 main 分支會自動觸發
git add .
git commit -m "Deploy to production"
git push origin main
```

CI/CD pipeline 會自動：
1. 運行測試
2. 建置 Docker images
3. 掃描安全漏洞
4. 推送到 Docker Hub
5. 部署到 Kubernetes
6. 運行 smoke tests

### 監控部署狀態

在 GitHub Actions 頁面查看：
- https://github.com/your-username/your-repo/actions

## 測試 HPA 自動擴展

### 產生負載

```bash
# 創建負載生成器
kubectl run load-generator -n microservices-demo \
  --image=busybox:latest \
  --restart=Never \
  --rm -it \
  -- /bin/sh

# 在 pod 內執行（持續發送請求）
while true; do
  wget -q -O- http://api-gateway-service:8080/api/status
done
```

### 觀察擴展

在另一個終端：

```bash
# 實時觀察 HPA
kubectl get hpa -n microservices-demo -w

# 觀察 Pod 數量變化
kubectl get pods -n microservices-demo -w -l app=api-gateway

# 查看 CPU/Memory 使用
kubectl top pods -n microservices-demo
```

你應該看到：
1. CPU 使用率上升
2. HPA 檢測到超過目標（70%）
3. Pod 數量逐漸增加（最多到 10 個）

停止負載後：
1. CPU 使用率下降
2. 等待穩定窗口（5 分鐘）
3. Pod 數量逐漸縮減回 2 個

## 滾動更新測試

### 更新應用

```bash
# 修改代碼後重新建置
./scripts/build-images.sh

# 如果是生產環境，推送新版本
docker tag api-gateway:latest $DOCKER_USERNAME/api-gateway:v1.1.0
docker push $DOCKER_USERNAME/api-gateway:v1.1.0

# 更新 deployment
kubectl set image deployment/api-gateway \
  api-gateway=$DOCKER_USERNAME/api-gateway:v1.1.0 \
  -n microservices-demo
```

### 監控滾動更新

```bash
# 觀察滾動更新過程
kubectl rollout status deployment/api-gateway -n microservices-demo

# 查看 Pod 變化
kubectl get pods -n microservices-demo -w -l app=api-gateway
```

你會看到：
1. 新 Pod 被創建
2. 新 Pod 通過健康檢查後變為 Ready
3. 舊 Pod 被終止
4. 零停機時間（因為 maxUnavailable: 0）

## 清理資源

### 清理應用（保留 cluster）

```bash
./scripts/cleanup.sh

# 或手動刪除
kubectl delete namespace microservices-demo
```

### 清理整個環境

**Minikube**:
```bash
minikube stop
minikube delete
```

**Kind**:
```bash
kind delete cluster --name microservices-demo
```

## 常見問題

### Pods 一直處於 Pending 狀態

**原因**：資源不足

**解決**：
```bash
# 查看事件
kubectl describe pod <pod-name> -n microservices-demo

# 增加 Minikube 資源
minikube stop
minikube start --cpus=4 --memory=8192
```

### Pods CrashLoopBackOff

**原因**：應用啟動失敗

**解決**：
```bash
# 查看日誌
kubectl logs <pod-name> -n microservices-demo

# 查看事件
kubectl describe pod <pod-name> -n microservices-demo
```

### HPA 沒有 metrics

**原因**：Metrics Server 未安裝或未就緒

**解決**：
```bash
# 檢查 Metrics Server
kubectl get deployment metrics-server -n kube-system

# Minikube 啟用
minikube addons enable metrics-server

# 手動安裝
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Ingress 無法訪問

**原因**：Ingress Controller 未安裝

**解決**：
```bash
# Minikube
minikube addons enable ingress

# 其他環境
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.5/deploy/static/provider/cloud/deploy.yaml
```

詳見 [故障排除文檔](troubleshooting.md)
