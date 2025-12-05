# Microservices Health Monitor

[![CI Pipeline](https://github.com/OWNER/K8s-test/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/K8s-test/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/OWNER/K8s-test/branch/main/graph/badge.svg)](https://codecov.io/gh/OWNER/K8s-test)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一個生產級的 Kubernetes 微服務專案，展示完整的 DevOps/SRE 最佳實踐，包括安全性、可觀測性、測試和 CI/CD。

## 🚀 專案簡介

這是一個基於 Python/Flask 的微服務健康監控系統，由三個微服務組成：
- **API Gateway**：提供 RESTful API，包含速率限制、請求追蹤、輸入驗證
- **Worker Service**：執行背景任務，具備線程安全和連接池管理
- **Dashboard**：Web UI 介面，實時顯示系統狀態

## 📐 架構圖

```
                    ┌─────────────┐
                    │   Internet  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────────┐
                    │   Ingress +     │
                    │ NetworkPolicy   │
                    └────┬────────┬───┘
                         │        │
          ┌──────────────┘        └──────────────┐
          │                                      │
    ┌─────▼─────┐                         ┌─────▼──────┐
    │ Dashboard │◀───── trace_id ────────▶│API Gateway │
    │ (port 3000)│                        │ (port 8080)│
    └───────────┘                         └─────┬──────┘
                                                │
                                          ┌─────▼──────┐
                                          │  Worker    │
                                          │  Service   │
                                          └─────┬──────┘
                                                │
                                          ┌─────▼──────┐
                                          │   Redis    │
                                          │ (Connection│
                                          │    Pool)   │
                                          └────────────┘

監控層:
    Prometheus ◀──── metrics ──── All Services

日誌層:
    All Services ──── JSON logs ──▶ ELK Stack / CloudWatch

安全層:
    - NetworkPolicies (Zero-Trust)
    - PodSecurityContext (Non-root)
    - PodDisruptionBudgets (High Availability)
```

## 🛠 技術棧

### 核心技術
- **語言**：Python 3.11
- **框架**：Flask 3.0+
- **容器化**：Docker with multi-stage builds
- **編排**：Kubernetes 1.28+
- **快取**：Redis 7.0+ with connection pooling

### DevOps 工具鏈
- **CI/CD**：GitHub Actions
- **測試**：pytest, pytest-cov, fakeredis
- **代碼質量**：flake8, bandit, black
- **安全掃描**：Trivy, Bandit, Safety
- **監控**：Prometheus + Grafana
- **日誌**：Structured JSON logging
- **追蹤**：Distributed tracing with trace_id

### Registry & Storage
- **Container Registry**：Docker Hub
- **Artifact Storage**：GitHub Artifacts

## ✨ 功能特性

### 🏗 基礎架構與安全
- ✅ **Kubernetes 生產級部署**：Deployment, Service, ConfigMap, Secret
- ✅ **Pod 安全上下文**：非 root 用戶運行，只讀根文件系統
- ✅ **網絡安全策略**：Zero-trust 網絡模型，default-deny + 白名單
- ✅ **高可用性配置**：PodDisruptionBudget, Pod Anti-Affinity
- ✅ **資源管理**：Requests/Limits, HPA 自動擴展

### 💎 應用代碼質量
- ✅ **Redis 連接池**：健康檢查、自動重連、電路斷路器模式
- ✅ **結構化日誌**：JSON 格式，支持 ELK/CloudWatch 聚合
- ✅ **分散式追蹤**：trace_id 自動生成和傳播
- ✅ **輸入驗證**：marshmallow schema 驗證
- ✅ **速率限制**：Redis-based 滑動窗口算法
- ✅ **增強健康檢查**：依賴項狀態監控

### 🧪 測試覆蓋
- ✅ **完整測試套件**：64+ 單元測試，>70% 覆蓋率
- ✅ **Mock 策略**：fakeredis, unittest.mock
- ✅ **測試自動化**：pytest, pytest-cov
- ✅ **測試文檔**：詳細的測試指南和最佳實踐

### 🚀 CI/CD Pipeline
- ✅ **4 階段 Pipeline**：Test → Security → Build → Push
- ✅ **安全掃描**：Trivy (鏡像), Bandit (代碼), Safety (依賴)
- ✅ **代碼質量**：flake8 Lint, 測試覆蓋率報告
- ✅ **自動化**：PR 自動標籤，Codecov 集成
- ✅ **優化構建**：Docker layer caching, pip 緩存

### 📊 可觀測性
- ✅ **Prometheus 指標**：請求計數、延遲、連接池統計
- ✅ **健康端點**：Liveness, Readiness with 依賴檢查
- ✅ **分散式追蹤**：X-Trace-ID 支持
- ✅ **結構化日誌**：JSON 格式，包含 trace_id

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

## 🔌 API 端點

### API Gateway (port 8080)

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/health/live` | GET | Liveness probe | None |
| `/health/ready` | GET | Readiness probe with dependencies | None |
| `/api/status` | GET | 系統狀態 + Redis 連接池統計 | 60 req/min |
| `/api/info` | GET | 服務信息和可用端點 | None |
| `/metrics` | GET | Prometheus metrics | None |
| `/` | GET | 服務歡迎頁面 | None |

**特殊響應頭**:
- `X-Trace-ID`: 請求追蹤 ID（自動生成或傳播）
- `X-RateLimit-Limit`: 速率限制上限
- `X-RateLimit-Remaining`: 剩餘請求數
- `X-RateLimit-Reset`: 重置時間戳

### Dashboard (port 3000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI 主頁 |
| `/health/live` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe |
| `/api/health-check` | GET | 所有服務健康狀態 |
| `/api/system-info` | GET | 系統詳細信息 |

### Worker Service (port 8081)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health/live` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe（檢查任務處理）|
| `/status` | GET | Worker 狀態和任務統計 |
| `/metrics` | GET | Prometheus metrics |

## 🧪 測試

### 運行測試

```bash
# 運行單個服務測試
cd services/api-gateway
pytest

# 運行所有服務測試
./scripts/run_all_tests.sh

# 運行特定測試標記
pytest -m unit           # 只運行單元測試
pytest -m integration    # 只運行集成測試

# 查看覆蓋率報告
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### 測試統計

- **總測試數**: 64+ 單元測試
- **覆蓋率**: >70%
- **執行時間**: <10 秒
- **CI 集成**: ✅ 自動運行

詳見 [測試文檔](docs/TESTING.md)

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

## 📚 文檔

### 核心文檔
- [📖 測試文檔](docs/TESTING.md) - 測試策略、運行指南、最佳實踐
- [🔧 CI/CD 文檔](docs/CI-CD.md) - Pipeline 架構、安全掃描、故障排查
- [📊 可觀測性文檔](docs/OBSERVABILITY.md) - Prometheus、Grafana、告警配置
- [⚙️ 資源優化指南](docs/RESOURCE-OPTIMIZATION.md) - ResourceQuota、HPA、PriorityClass
- [🔐 Secrets 配置](docs/SECRETS-SETUP.md) - GitHub Secrets 設置指南

### 部署與運維
- [🚀 部署指南](docs/DEPLOYMENT-GUIDE.md) - 本地/雲端部署、故障排查、升級回滾
- [🎯 面試準備指南](docs/INTERVIEW-PREP.md) - Demo 流程、技術亮點、常見問題

### 開發流程
- [🤝 貢獻指南](.github/CONTRIBUTING.md) - 如何貢獻代碼
- [📝 Pull Request 模板](.github/pull_request_template.md)
- [🐛 Issue 模板](.github/ISSUE_TEMPLATE/)
- [📋 Changelog](CHANGELOG.md) - 版本變更記錄

## 🎯 面試展示重點

這個專案展示了完整的生產級 DevOps/SRE 能力：

### 1. 🏗 基礎設施即代碼 (IaC)
- ✅ Kubernetes manifests 完整配置
- ✅ 多環境支持（dev/staging/prod）
- ✅ GitOps 工作流程
- ✅ 版本化配置管理

### 2. 🔒 安全最佳實踐
- ✅ **三層安全掃描**: Trivy (鏡像), Bandit (代碼), Safety (依賴)
- ✅ **Pod 安全**: 非 root 運行，只讀文件系統，capabilities drop
- ✅ **網絡安全**: NetworkPolicy 零信任模型
- ✅ **密鑰管理**: Kubernetes Secrets，永不硬編碼

### 3. 🚀 CI/CD 自動化
- ✅ **完整 Pipeline**: 測試 → 安全掃描 → 構建 → 部署
- ✅ **質量門禁**: 70% 測試覆蓋率，Lint 檢查
- ✅ **自動化發布**: 基於分支的部署策略
- ✅ **回滾機制**: Git-based 回滾策略

### 4. 🧪 測試驅動開發
- ✅ **測試金字塔**: 70% 單元，20% 集成，10% E2E
- ✅ **高覆蓋率**: >70% 代碼覆蓋
- ✅ **Mock 策略**: 隔離外部依賴
- ✅ **CI 集成**: 每次提交自動測試

### 5. 📊 可觀測性 (Observability)
- ✅ **指標**: Prometheus metrics，RED 方法
- ✅ **日誌**: 結構化 JSON 日誌，支持聚合
- ✅ **追蹤**: 分散式追蹤 with trace_id
- ✅ **健康檢查**: 依賴項狀態監控

### 6. 🎛 運維能力
- ✅ **高可用**: PodDisruptionBudget, Anti-Affinity
- ✅ **自動擴展**: HPA 基於 CPU/Memory
- ✅ **零停機部署**: 滾動更新策略
- ✅ **災難恢復**: 備份和恢復策略

### 7. 💎 代碼質量
- ✅ **設計模式**: 連接池，電路斷路器，速率限制
- ✅ **錯誤處理**: 完善的異常處理和重試機制
- ✅ **並發安全**: 線程安全實現
- ✅ **性能優化**: 緩存策略，連接池管理

## 🏆 項目指標

| 指標 | 數值 |
|------|------|
| **代碼覆蓋率** | >70% |
| **測試數量** | 64+ 單元測試 |
| **CI/CD 時間** | ~8-13 分鐘 |
| **服務數量** | 3 個微服務 |
| **Kubernetes 資源** | 20+ manifests |
| **安全掃描** | 3 層掃描 |
| **文檔頁面** | 10+ 文檔 |

## 🤝 貢獻

歡迎貢獻！請參閱 [貢獻指南](.github/CONTRIBUTING.md)。

1. Fork 項目
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## License

MIT License
