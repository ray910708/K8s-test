# Architecture Documentation

## 系統架構概覽

微服務健康監控系統採用現代雲原生架構設計，由三個核心微服務組成，部署在 Kubernetes 集群中。

### 架構圖

```
                    ┌─────────────────────────────────────┐
                    │         Internet / Users            │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │      Kubernetes Ingress             │
                    │   (NGINX Ingress Controller)        │
                    └──────────┬─────────────┬────────────┘
                               │             │
                 ┌─────────────▼──┐    ┌────▼──────────────┐
                 │  Dashboard     │    │  API Gateway      │
                 │  Service       │    │  Service          │
                 │  (Port 3000)   │    │  (Port 8080)      │
                 │                │    │                   │
                 │  - Web UI      │    │  - REST API       │
                 │  - Status      │◄───┤  - Health Checks  │
                 │    Display     │    │  - Metrics        │
                 └────────────────┘    └─────┬─────────────┘
                                             │
                                ┌────────────▼─────────────┐
                                │  Worker Service          │
                                │  (Port 8081)             │
                                │                          │
                                │  - Background Tasks      │
                                │  - Job Processing        │
                                │  - Metrics Collection    │
                                └────────┬─────────────────┘
                                         │
                                ┌────────▼─────────────┐
                                │      Redis           │
                                │   (Port 6379)        │
                                │                      │
                                │  - Cache Layer       │
                                │  - Shared State      │
                                │  - Task Counters     │
                                └──────────────────────┘

              ┌──────────────────────────────────────────────┐
              │    Horizontal Pod Autoscaler (HPA)           │
              │  - Auto-scales based on CPU/Memory          │
              │  - API Gateway: 2-10 replicas               │
              │  - Worker Service: 1-5 replicas             │
              └──────────────────────────────────────────────┘
```

## 微服務組件

### 1. API Gateway

**職責**：
- 作為系統的主要入口點
- 提供 RESTful API 端點
- 處理外部 HTTP 請求
- 暴露 Prometheus metrics
- 與 Redis 交互進行狀態管理

**技術細節**：
- 語言：Python 3.11
- 框架：Flask + Gunicorn
- Port：8080
- 副本數：2-10 (HPA 控制)

**關鍵端點**：
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /api/status` - 系統狀態
- `GET /api/info` - 服務資訊
- `GET /metrics` - Prometheus metrics

**資源配置**：
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 2. Worker Service

**職責**：
- 執行背景任務
- 定期處理數據
- 產生系統指標
- 模擬工作負載

**技術細節**：
- 語言：Python 3.11
- 框架：Flask (健康檢查) + Schedule (任務調度)
- Port：8081
- 副本數：1-5 (HPA 控制)

**任務類型**：
- `data_processing` - 數據處理
- `cleanup` - 清理任務
- `health_check` - 健康檢查
- `metrics_collection` - 指標收集

**執行頻率**：每 10 秒執行一次任務

**資源配置**：
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 3. Dashboard

**職責**：
- 提供 Web UI 界面
- 實時顯示系統狀態
- 監控所有服務健康狀況
- 展示服務指標

**技術細節**：
- 語言：Python 3.11
- 框架：Flask + Gunicorn
- 前端：HTML5 + CSS3 + Vanilla JavaScript
- Port：3000
- 副本數：2 (固定)

**功能特性**：
- 自動刷新（每 5 秒）
- 實時健康狀態顯示
- 服務響應時間監控
- 美觀的 UI 設計

**資源配置**：
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 4. Redis

**職責**：
- 提供共享快取層
- 儲存應用狀態
- 任務計數器
- 服務間數據共享

**技術細節**：
- 版本：Redis 7 Alpine
- Port：6379
- 副本數：1
- 持久化：使用 emptyDir（開發環境）

**資源配置**：
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

## 資料流向

### 用戶訪問流程

```
用戶 → Ingress → Dashboard → API Gateway → Redis
                              ↓
                        Worker Service → Redis
```

1. **用戶請求**：通過 Ingress 路由到 Dashboard
2. **Dashboard**：調用 API Gateway 獲取系統狀態
3. **API Gateway**：從 Redis 讀取/寫入數據
4. **Worker Service**：在背景持續處理任務，更新 Redis 中的計數器

### API 調用流程

```
External Client → Ingress (/api/*) → API Gateway → Redis
                                          ↓
                                    Response JSON
```

## Kubernetes 資源

### Namespace

```yaml
名稱: microservices-demo
用途: 隔離所有專案資源
```

### ConfigMap

**配置項**：
- 應用環境變數
- Redis 連接資訊
- 服務發現 URLs
- 日誌級別

### Secrets

**敏感資訊**：
- Redis 密碼
- API 金鑰（預留）

### Services

| Service Name | Type | Port | Target Port |
|-------------|------|------|-------------|
| api-gateway-service | ClusterIP | 8080 | 8080 |
| worker-service | ClusterIP | 8081 | 8081 |
| dashboard-service | ClusterIP | 3000 | 3000 |
| redis-service | ClusterIP | 6379 | 6379 |

### Deployments

所有 Deployments 都配置了：
- **滾動更新策略**：`maxSurge: 1, maxUnavailable: 0`
- **Liveness Probe**：HTTP GET 健康檢查
- **Readiness Probe**：確保服務就緒後才接收流量
- **資源限制**：requests 和 limits
- **環境變數**：從 ConfigMap 和 Secret 注入

### HorizontalPodAutoscaler (HPA)

**API Gateway HPA**：
- Min Replicas: 2
- Max Replicas: 10
- CPU Target: 70%
- Memory Target: 80%

**Worker Service HPA**：
- Min Replicas: 1
- Max Replicas: 5
- CPU Target: 70%
- Memory Target: 80%

**擴展策略**：
- **Scale Up**：快速擴展（立即響應）
- **Scale Down**：穩定 5 分鐘後才縮減（避免抖動）

### Ingress

**路由規則**：
- `/ → Dashboard (3000)`
- `/api/* → API Gateway (8080)`

**Host**: `microservices-demo.local`

**Annotations**：
- `nginx.ingress.kubernetes.io/rewrite-target: /`
- `nginx.ingress.kubernetes.io/ssl-redirect: "false"`

## 健康檢查機制

### Liveness Probe

**用途**：檢測容器是否存活

**配置**：
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: <service-port>
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

**行為**：如果連續 3 次失敗，Kubernetes 會重啟容器

### Readiness Probe

**用途**：檢測服務是否就緒接收流量

**配置**：
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: <service-port>
  initialDelaySeconds: 5-15
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

**行為**：如果失敗，Kubernetes 會將 Pod 從 Service 的 endpoints 中移除

## 可觀測性

### Prometheus Metrics

**API Gateway Metrics**：
- `api_gateway_requests_total` - 總請求數（按 method, endpoint, status）
- `api_gateway_request_duration_seconds` - 請求處理時間
- `api_gateway_requests_in_progress` - 進行中的請求數
- `api_gateway_redis_connection_status` - Redis 連接狀態

**Worker Service Metrics**：
- `worker_tasks_processed_total` - 已處理任務總數（按 task_type, status）
- `worker_tasks_in_progress` - 進行中的任務數
- `worker_redis_connection_status` - Redis 連接狀態
- `worker_last_task_timestamp` - 最後一次任務的時間戳

### 日誌

**格式**：結構化日誌
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**級別**：
- Production: INFO
- Development: DEBUG

## 安全性設計

### 容器安全

1. **Non-root User**：所有容器都使用 `appuser` (UID 1000) 運行
2. **最小化 Base Image**：使用 `python:3.11-slim`
3. **Multi-stage Build**：減少最終 image 大小和攻擊面

### Secrets 管理

- 使用 Kubernetes Secrets 儲存敏感資訊
- Base64 編碼
- 通過環境變數注入

### 網路安全

- 所有服務使用 ClusterIP（內部訪問）
- 僅通過 Ingress 暴露外部訪問
- 可選：Network Policies（進階配置）

## 可擴展性設計

### 水平擴展 (HPA)

- 基於 CPU 和 Memory 使用率自動擴展
- API Gateway 可擴展至 10 個副本
- Worker Service 可擴展至 5 個副本

### 滾動更新

- 零停機部署
- `maxUnavailable: 0` 確保始終有可用實例
- `maxSurge: 1` 允許額外的臨時 Pod

### 資源限制

- 所有容器都設定了 requests 和 limits
- 防止資源耗盡
- 確保 QoS（Quality of Service）

## 災難恢復

### Pod 故障

- **自動重啟**：Liveness probe 失敗會觸發重啟
- **副本替換**：Deployment 會自動創建新的 Pod 替換失敗的

### 節點故障

- **Pod 遷移**：Kubernetes 會在健康節點上重新調度 Pod
- **多副本**：確保服務高可用

### 回滾機制

```bash
# 查看部署歷史
kubectl rollout history deployment/api-gateway -n microservices-demo

# 回滾到上一個版本
kubectl rollout undo deployment/api-gateway -n microservices-demo

# 回滾到特定版本
kubectl rollout undo deployment/api-gateway --to-revision=2 -n microservices-demo
```

## 設計決策

### 為什麼選擇 Python/Flask？

- **簡潔性**：代碼易讀易維護
- **快速開發**：豐富的生態系統
- **面試友好**：容易講解和展示

### 為什麼選擇 Redis？

- **輕量級**：部署簡單
- **高性能**：內存數據庫
- **廣泛應用**：工業標準

### 為什麼使用 HPA？

- **展示自動化**：DevOps 核心能力
- **實際應用**：生產環境必備
- **易於演示**：可以現場壓測展示

### 為什麼選擇 Gunicorn？

- **生產級**：WSGI server
- **性能好**：多 worker 支持
- **穩定性**：廣泛使用

## 未來優化方向

### 監控增強

- 整合 Prometheus + Grafana
- 設置告警規則
- 添加分佈式追蹤（Jaeger）

### 安全增強

- 實施 Network Policies
- 添加 Pod Security Policies
- 使用 Cert-Manager 管理 TLS

### 部署優化

- 使用 Helm Charts
- 實施 GitOps (ArgoCD)
- 多環境管理 (Kustomize)

### 可靠性增強

- 實施 Circuit Breaker
- 添加 Rate Limiting
- 實施 Service Mesh (Istio)
