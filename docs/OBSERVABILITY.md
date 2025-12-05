# 可觀測性文檔

本文檔說明項目的可觀測性策略、監控架構和告警配置。

## 概覽

我們實施了完整的三支柱可觀測性（Three Pillars of Observability）：

1. **指標 (Metrics)** - Prometheus + Grafana
2. **日誌 (Logs)** - 結構化 JSON 日誌
3. **追蹤 (Traces)** - 分散式追蹤 with trace_id

## 架構圖

```
┌─────────────────────────────────────────────────────────┐
│                    Observability Stack                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐      ┌────────────┐      ┌──────────┐ │
│  │ Prometheus │─────▶│  Grafana   │◀────▶│  Alerts  │ │
│  │ (Metrics)  │      │(Dashboards)│      │(Manager) │ │
│  └─────┬──────┘      └────────────┘      └──────────┘ │
│        │                                                │
│        │ /metrics                                       │
│        │                                                │
│  ┌─────▼─────────────────────────────────────┐        │
│  │         Microservices Layer               │        │
│  ├───────────────────────────────────────────┤        │
│  │  API Gateway  │  Worker  │  Dashboard     │        │
│  │  • Counters   │• Gauges  │  • Histograms │        │
│  │  • Histograms │• Counters│  • Gauges     │        │
│  └───┬───────────────┬──────────────┬────────┘        │
│      │               │              │                  │
│      │ JSON logs     │              │                  │
│      ▼               ▼              ▼                  │
│  ┌────────────────────────────────────┐               │
│  │      Structured Logging            │               │
│  │  (ELK Stack / CloudWatch / Loki)   │               │
│  └────────────────────────────────────┘               │
└──────────────────────────────────────────────────────┘
```

## 指標 (Metrics)

### Prometheus 配置

Prometheus 部署在 `microservices-demo` 命名空間，自動發現和抓取所有服務的指標。

**配置文件**:
- [prometheus-config.yaml](../k8s/monitoring/prometheus-config.yaml) - 主配置
- [prometheus-deployment.yaml](../k8s/monitoring/prometheus-deployment.yaml) - 部署配置
- [prometheus-rules.yaml](../k8s/monitoring/prometheus-rules.yaml) - 告警規則

**抓取間隔**: 15 秒
**數據保留**: 7 天
**評估間隔**: 15 秒

### 收集的指標

#### API Gateway 指標

| 指標名稱 | 類型 | 說明 |
|---------|------|------|
| `api_gateway_requests_total` | Counter | 請求總數（按 method, endpoint, status 分組）|
| `api_gateway_request_duration_seconds` | Histogram | 請求延遲（按 method, endpoint 分組）|
| `api_gateway_requests_in_progress` | Gauge | 進行中的請求數 |
| `api_gateway_redis_connection_status` | Gauge | Redis 連接狀態（1=連接，0=斷線）|
| `api_gateway_redis_pool_connections_available` | Gauge | 可用連接數 |
| `api_gateway_redis_pool_connections_in_use` | Gauge | 使用中連接數 |
| `api_gateway_redis_pool_connections_max` | Gauge | 最大連接數 |

#### Worker Service 指標

| 指標名稱 | 類型 | 說明 |
|---------|------|------|
| `worker_tasks_processed_total` | Counter | 處理的任務總數（按 task_type, status）|
| `worker_tasks_in_progress` | Gauge | 進行中的任務數 |
| `worker_redis_connection_status` | Gauge | Redis 連接狀態 |
| `worker_last_task_timestamp` | Gauge | 最後任務時間戳 |
| `worker_redis_pool_*` | Gauge | Redis 連接池統計 |

### RED 方法

我們的指標遵循 RED 方法（Rate, Errors, Duration）：

- **Rate (速率)**: `rate(api_gateway_requests_total[5m])`
- **Errors (錯誤)**: `rate(api_gateway_requests_total{status=~"5.."}[5m])`
- **Duration (延遲)**: `histogram_quantile(0.95, api_gateway_request_duration_seconds_bucket)`

### 部署 Prometheus

```bash
# 應用配置
kubectl apply -f k8s/monitoring/prometheus-config.yaml
kubectl apply -f k8s/monitoring/prometheus-rules.yaml
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml

# 檢查狀態
kubectl get pods -n microservices-demo -l app=prometheus

# 訪問 Prometheus UI (Port Forward)
kubectl port-forward -n microservices-demo svc/prometheus 9090:9090
# 訪問 http://localhost:9090
```

## 告警 (Alerting)

### 告警規則

我們配置了以下告警規則：

#### 1. **HighErrorRate** (嚴重)
- **條件**: 錯誤率 > 5%（5 分鐘內）
- **動作**: 立即通知平台團隊
- **處理**: 檢查服務日誌，回滾最近部署

#### 2. **HighLatency** (警告)
- **條件**: P95 延遲 > 1 秒（5 分鐘內）
- **動作**: 通知平台團隊
- **處理**: 檢查性能瓶頸，考慮擴容

#### 3. **ServiceDown** (嚴重)
- **條件**: 服務停機 > 2 分鐘
- **動作**: 立即通知平台團隊
- **處理**: 檢查 Pod 狀態，查看崩潰日誌

#### 4. **RedisConnectionDown** (嚴重)
- **條件**: Redis 連接斷開 > 1 分鐘
- **動作**: 立即通知平台團隊
- **處理**: 檢查 Redis 服務，檢查網絡策略

#### 5. **RedisConnectionPoolExhausted** (警告)
- **條件**: 連接池使用率 > 90%（5 分鐘內）
- **動作**: 通知平台團隊
- **處理**: 增加連接池大小或擴容服務

#### 6. **HighMemoryUsage** (警告)
- **條件**: 內存使用 > 90%（5 分鐘內）
- **動作**: 通知平台團隊
- **處理**: 檢查內存洩漏，考慮擴容

#### 7. **HighCPUUsage** (警告)
- **條件**: CPU 使用 > 90%（5 分鐘內）
- **動作**: 通知平台團隊
- **處理**: 檢查性能問題，考慮擴容

### 告警嚴重性級別

- **Critical (嚴重)**: 需要立即響應，影響用戶
- **Warning (警告)**: 需要關注，可能影響性能
- **Info (信息)**: 信息性通知，無需立即響應

### 告警通知渠道

告警可以配置發送到：
- Slack
- Email
- PagerDuty
- OpsGenie
- Webhook

## 儀表板 (Dashboards)

### Grafana 配置

**配置文件**:
- [grafana-deployment.yaml](../k8s/monitoring/grafana-deployment.yaml) - Grafana 部署
- [grafana-dashboards.yaml](../k8s/monitoring/grafana-dashboards.yaml) - 儀表板配置

### 部署 Grafana

```bash
# 部署 Grafana
kubectl apply -f k8s/monitoring/grafana-deployment.yaml
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml

# 檢查狀態
kubectl get pods -n microservices-demo -l app=grafana

# 訪問 Grafana UI (Port Forward)
kubectl port-forward -n microservices-demo svc/grafana 3000:3000
# 訪問 http://localhost:3000
# 默認用戶名: admin
# 默認密碼: admin123
```

### 預配置儀表板

#### Microservices Overview Dashboard

包含以下面板：

1. **Request Rate** - 每秒請求數
2. **Error Rate** - 錯誤率趨勢
3. **Request Duration (p95)** - P95 延遲
4. **Requests In Progress** - 並發請求數
5. **Redis Connection Status** - Redis 連接狀態
6. **Redis Pool Usage** - 連接池使用率
7. **Worker Tasks Processed** - Worker 任務處理量

### 創建自定義儀表板

1. 訪問 Grafana UI
2. 點擊 "+" → "Dashboard"
3. 添加面板，選擇 Prometheus 數據源
4. 使用 PromQL 查詢指標
5. 保存儀表板

**PromQL 查詢示例**:

```promql
# 請求速率
sum(rate(api_gateway_requests_total[5m])) by (service)

# 錯誤率
sum(rate(api_gateway_requests_total{status=~"5.."}[5m])) / sum(rate(api_gateway_requests_total[5m]))

# P95 延遲
histogram_quantile(0.95, sum(rate(api_gateway_request_duration_seconds_bucket[5m])) by (le))

# Redis 連接池使用率
api_gateway_redis_pool_connections_in_use / api_gateway_redis_pool_connections_max
```

## 日誌 (Logging)

### 結構化日誌

所有服務輸出 JSON 格式的結構化日誌，包含：

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "service": "api-gateway",
  "logger": "app",
  "message": "GET /api/status 200",
  "trace_id": "abc123-def456-ghi789",
  "request_method": "GET",
  "request_path": "/api/status",
  "status_code": 200,
  "request_duration_ms": 45.67
}
```

### 日誌聚合

推薦使用以下日誌聚合方案：

#### 選項 1: ELK Stack
- **Elasticsearch**: 存儲和索引
- **Logstash**: 日誌處理
- **Kibana**: 可視化

#### 選項 2: Loki
- **Loki**: 日誌聚合（Grafana 原生）
- **Promtail**: 日誌收集
- **Grafana**: 可視化

#### 選項 3: 雲服務
- **AWS CloudWatch Logs**
- **Google Cloud Logging**
- **Azure Monitor Logs**

### 日誌查詢

**按 trace_id 查詢**:
```
{service="api-gateway"} | json | trace_id="abc123-def456-ghi789"
```

**查詢錯誤日誌**:
```
{service="api-gateway"} | json | level="ERROR"
```

**查詢慢請求**:
```
{service="api-gateway"} | json | request_duration_ms > 1000
```

## 追蹤 (Tracing)

### 分散式追蹤

每個請求自動分配一個唯一的 `trace_id`：

- 從 HTTP 頭 `X-Trace-ID` 或 `X-Request-ID` 提取
- 如果不存在，自動生成 UUID
- 在響應中返回 `X-Trace-ID` 頭
- 包含在所有日誌中

### 追蹤流程

```
Client Request
    │
    ├─> API Gateway (trace_id: abc123)
    │       ├─> Log: "Received request"
    │       ├─> Call Worker Service (propagate trace_id)
    │       └─> Log: "Request completed"
    │
    └─> Worker Service (trace_id: abc123)
            ├─> Log: "Processing task"
            └─> Log: "Task completed"
```

### 使用 trace_id 調試

1. 從用戶報告或監控獲取 trace_id
2. 在日誌中搜索該 trace_id
3. 查看完整的請求鏈路
4. 識別性能瓶頸或錯誤點

## SLI/SLO

### Service Level Indicators (SLIs)

- **可用性**: `(成功請求 / 總請求) * 100%`
- **延遲**: `P95 < 1 秒`
- **錯誤率**: `錯誤請求 / 總請求 < 1%`

### Service Level Objectives (SLOs)

| 指標 | 目標 | 測量窗口 |
|------|------|---------|
| 可用性 | 99.9% | 30 天 |
| P95 延遲 | < 1 秒 | 5 分鐘 |
| 錯誤率 | < 1% | 5 分鐘 |

### 錯誤預算

- **SLO**: 99.9% 可用性 = 0.1% 錯誤預算
- **30 天**: 43.2 分鐘停機時間
- **監控**: 實時追蹤錯誤預算消耗

## 最佳實踐

### 1. 指標命名

- 使用有意義的前綴（`api_gateway_`, `worker_`）
- 包含單位（`_seconds`, `_bytes`, `_total`）
- 使用標籤區分維度

### 2. 告警設計

- 避免告警疲勞：只告警可操作的問題
- 設置適當的閾值和時間窗口
- 包含清晰的處理步驟

### 3. 儀表板設計

- 使用 RED 方法組織面板
- 包含時間範圍選擇器
- 使用適當的可視化類型

### 4. 日誌管理

- 始終包含 trace_id
- 使用適當的日誌級別
- 不記錄敏感信息

## 故障排查

### 問題 1: Prometheus 無法抓取指標

**檢查**:
```bash
# 檢查 Prometheus Pod 狀態
kubectl get pods -n microservices-demo -l app=prometheus

# 檢查服務端點
kubectl get endpoints -n microservices-demo

# 查看 Prometheus 日誌
kubectl logs -n microservices-demo -l app=prometheus
```

### 問題 2: Grafana 無法連接 Prometheus

**檢查**:
- 驗證 Prometheus 服務 DNS: `prometheus.microservices-demo.svc.cluster.local`
- 檢查網絡策略是否允許連接
- 在 Grafana UI 測試數據源

### 問題 3: 告警未觸發

**檢查**:
- 驗證告警規則語法
- 檢查 Alertmanager 配置
- 查看 Prometheus 告警狀態

## 面試展示要點

在面試中討論可觀測性時，可以強調：

1. **完整的三支柱**: 指標、日誌、追蹤全覆蓋
2. **生產級監控**: Prometheus + Grafana + 告警
3. **結構化日誌**: JSON 格式，易於聚合分析
4. **分散式追蹤**: trace_id 貫穿整個請求鏈路
5. **SLI/SLO**: 明確的服務水平指標和目標
6. **告警策略**: 可操作的告警，避免告警疲勞
7. **RED 方法**: 業界最佳實踐

## 相關資源

- [Prometheus 文檔](https://prometheus.io/docs/)
- [Grafana 文檔](https://grafana.com/docs/)
- [RED Method](https://www.weave.works/blog/the-red-method-key-metrics-for-microservices-architecture/)
- [SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
