# Microservices Health Monitor

一個適合 DevOps/SRE 面試展示的 Kubernetes 微服務專案，展示基礎部署和 CI/CD 整合能力。

## 專案簡介

這是一個基於 Python/Flask 的微服務健康監控系統，由三個微服務組成：
- **API Gateway**：提供 RESTful API，處理外部請求
- **Worker Service**：執行背景任務，產生日誌和指標
- **Dashboard**：Web UI 介面，顯示系統狀態

## 架構圖

```
Internet
   |
   v
Ingress
   |
   +----> Dashboard (port 3000)
   |
   +----> API Gateway (port 8080)
             |
             v
          Worker Service
             |
             v
          Redis (快取層)
```

## 技術棧

- **語言**：Python 3.11
- **框架**：Flask
- **容器化**：Docker
- **編排**：Kubernetes
- **CI/CD**：GitHub Actions
- **快取**：Redis
- **監控**：Prometheus metrics
- **Registry**：Docker Hub

## 功能特性

- ✅ 微服務架構設計
- ✅ Kubernetes 部署（Deployment, Service, ConfigMap, Secret）
- ✅ 健康檢查（Liveness & Readiness Probes）
- ✅ 滾動更新（零停機部署）
- ✅ 水平自動擴展（HPA）
- ✅ Prometheus Metrics
- ✅ CI/CD Pipeline（GitHub Actions）
- ✅ 資源限制和請求管理
- ✅ Ingress 路由配置

## 快速開始

### 前置需求

- Docker
- Kubernetes cluster（Minikube 或自建）
- kubectl
- Python 3.11+（本地開發）

### 本地開發（Minikube）

1. **啟動 Minikube**

```bash
minikube start --cpus=4 --memory=8192
minikube addons enable ingress
minikube addons enable metrics-server
```

2. **設定 Docker 環境**

```bash
eval $(minikube docker-env)
```

3. **建置 Docker Images**

```bash
chmod +x scripts/build-images.sh
./scripts/build-images.sh
```

4. **部署到 Kubernetes**

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

5. **查看部署狀態**

```bash
kubectl get pods -n microservices-demo
kubectl get svc -n microservices-demo
kubectl get ingress -n microservices-demo
```

6. **訪問服務**

```bash
# 方法 1: 使用 minikube service
minikube service dashboard-service --namespace=microservices-demo

# 方法 2: 配置 /etc/hosts
echo "$(minikube ip) microservices-demo.local" | sudo tee -a /etc/hosts
# 然後訪問 http://microservices-demo.local
```

### 雲端部署

詳見 [部署指南](docs/deployment-guide.md)

## 專案結構

```
k8s-microservices-demo/
├── services/               # 微服務程式碼
│   ├── api-gateway/       # API 閘道服務
│   ├── worker-service/    # 背景工作服務
│   └── dashboard/         # 儀表板服務
├── k8s/                   # Kubernetes 配置
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── api-gateway/
│   ├── worker-service/
│   ├── dashboard/
│   ├── redis/
│   └── ingress.yaml
├── .github/workflows/     # CI/CD pipelines
├── scripts/               # 部署腳本
└── docs/                  # 文檔
```

## API 端點

### API Gateway (port 8080)

- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /api/status` - 系統狀態
- `GET /metrics` - Prometheus metrics

### Dashboard (port 3000)

- `GET /` - Web UI
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe

## 測試 HPA 自動擴展

```bash
# 觀察 HPA 狀態
kubectl get hpa -n microservices-demo -w

# 產生負載（另一個終端）
kubectl run -it --rm load-generator --image=busybox --restart=Never -- /bin/sh
# 在 pod 內執行
while true; do wget -q -O- http://api-gateway-service.microservices-demo.svc.cluster.local:8080/api/status; done
```

## 清理資源

```bash
chmod +x scripts/cleanup.sh
./scripts/cleanup.sh
```

或手動刪除：

```bash
kubectl delete namespace microservices-demo
```

## 文檔

- [架構設計](docs/architecture.md)
- [部署指南](docs/deployment-guide.md)
- [故障排除](docs/troubleshooting.md)

## 展示重點

這個專案展示了以下 DevOps/SRE 核心能力：

1. **容器化**：Multi-stage Docker builds，安全最佳實踐
2. **Kubernetes**：資源管理、健康檢查、滾動更新、服務發現
3. **自動擴展**：HPA 基於 CPU/Memory 自動擴展
4. **CI/CD**：自動化測試、建置、安全掃描、部署
5. **可觀測性**：健康檢查端點、Prometheus metrics
6. **安全性**：Secrets 管理、非 root 用戶運行

## License

MIT License
