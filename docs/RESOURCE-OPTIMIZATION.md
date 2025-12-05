# Kubernetes 資源優化文檔

本文檔說明項目的 Kubernetes 資源管理策略、配額設置和優化方法。

## 概覽

我們實施了完整的資源管理策略，確保集群資源的高效利用和公平分配：

1. **ResourceQuota** - 命名空間級別的資源配額
2. **LimitRange** - Pod 和容器的預設資源限制
3. **HorizontalPodAutoscaler (HPA)** - 基於指標的自動擴展
4. **PriorityClass** - 工作負載優先級和搶占策略

## 架構圖

```
┌─────────────────────────────────────────────────────────┐
│              Kubernetes Resource Management              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │           Namespace: microservices-demo            │ │
│  │                                                     │ │
│  │  ResourceQuota:                                    │ │
│  │  • CPU: 8 cores (requests) / 16 cores (limits)    │ │
│  │  • Memory: 16Gi (requests) / 32Gi (limits)        │ │
│  │  • Pods: 50 max                                   │ │
│  │                                                     │ │
│  │  LimitRange (defaults):                            │ │
│  │  • Container CPU: 100m (req) / 500m (limit)       │ │
│  │  • Container Memory: 128Mi (req) / 512Mi (limit)  │ │
│  └─────────────────┬───────────────────────────────────┘ │
│                    │                                      │
│  ┌─────────────────▼───────────────────────────────────┐ │
│  │               Priority Classes                       │ │
│  │  Critical (1000000): API Gateway, Redis            │ │
│  │  High (10000): Dashboard, Prometheus, Grafana      │ │
│  │  Medium (1000): Worker Service (default)           │ │
│  │  Low (100): Batch jobs                             │ │
│  └─────────────────┬───────────────────────────────────┘ │
│                    │                                      │
│  ┌─────────────────▼───────────────────────────────────┐ │
│  │        Horizontal Pod Autoscaler (HPA)             │ │
│  │  API Gateway: 2-10 replicas (CPU 70%, Mem 80%)    │ │
│  │  Worker: 1-5 replicas (CPU 70%, Mem 80%)          │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## ResourceQuota

### 配置文件

[k8s/resource-quota.yaml](../k8s/resource-quota.yaml)

### 配額設置

#### 主要配額 (microservices-quota)

| 資源類型 | 配額 | 說明 |
|---------|------|------|
| **計算資源** | | |
| requests.cpu | 8 cores | 所有 Pod 的 CPU requests 總和 |
| requests.memory | 16Gi | 所有 Pod 的內存 requests 總和 |
| limits.cpu | 16 cores | 所有 Pod 的 CPU limits 總和 |
| limits.memory | 32Gi | 所有 Pod 的內存 limits 總和 |
| **存儲資源** | | |
| requests.storage | 50Gi | 持久卷聲明的存儲總和 |
| persistentvolumeclaims | 10 | PVC 數量上限 |
| **對象數量** | | |
| pods | 50 | Pod 數量上限 |
| services | 20 | Service 數量上限 |
| configmaps | 20 | ConfigMap 數量上限 |
| secrets | 20 | Secret 數量上限 |
| **網絡資源** | | |
| services.loadbalancers | 2 | LoadBalancer 服務數量（成本控制）|
| services.nodeports | 5 | NodePort 服務數量 |

#### 優先級配額 (microservices-priority-quota)

為高優先級工作負載預留資源：

- **Pods**: 20
- **CPU requests**: 4 cores
- **Memory requests**: 8Gi
- **作用範圍**: priorityClass = high-priority 或 critical

### 檢查配額使用情況

```bash
# 查看配額狀態
kubectl describe resourcequota -n microservices-demo

# 查看配額使用情況
kubectl get resourcequota -n microservices-demo -o yaml

# 查看當前資源使用
kubectl top nodes
kubectl top pods -n microservices-demo
```

## LimitRange

### 配置文件

[k8s/limit-range.yaml](../k8s/limit-range.yaml)

### 限制設置

#### 容器級別限制

| 項目 | 值 | 說明 |
|------|-----|------|
| **最大值** | | |
| CPU | 2 cores | 單個容器最大 CPU |
| Memory | 4Gi | 單個容器最大內存 |
| **最小值** | | |
| CPU | 10m | 單個容器最小 CPU |
| Memory | 16Mi | 單個容器最小內存 |
| **預設限制** | | |
| CPU | 500m | 未指定 limits 時的預設值 |
| Memory | 512Mi | 未指定 limits 時的預設值 |
| **預設請求** | | |
| CPU | 100m | 未指定 requests 時的預設值 |
| Memory | 128Mi | 未指定 requests 時的預設值 |
| **Limit/Request 比例** | | |
| CPU | 10:1 | 防止 limit 遠大於 request |
| Memory | 4:1 | 防止資源浪費 |

#### Pod 級別限制

| 項目 | 值 | 說明 |
|------|-----|------|
| 最大 CPU | 4 cores | Pod 所有容器 CPU 總和 |
| 最大 Memory | 8Gi | Pod 所有容器內存總和 |
| 最小 CPU | 10m | Pod 最小 CPU |
| 最小 Memory | 16Mi | Pod 最小內存 |

#### PVC 限制

| 項目 | 值 |
|------|-----|
| 最大存儲 | 10Gi |
| 最小存儲 | 1Gi |

### 為什麼需要 LimitRange？

1. **防止資源濫用**: 限制單個容器/Pod 的資源上限
2. **設置合理預設值**: 為沒有指定資源的 Pod 設置預設值
3. **資源公平性**: 確保所有工作負載公平分享資源
4. **防止配置錯誤**: 防止錯誤配置導致資源浪費

## PriorityClass

### 配置文件

[k8s/priority-classes.yaml](../k8s/priority-classes.yaml)

### 優先級定義

| 優先級類別 | 值 | 用途 | 搶占策略 | 使用服務 |
|-----------|-----|------|---------|---------|
| **critical** | 1000000 | 關鍵服務 | 可以搶占 | API Gateway, Redis |
| **high-priority** | 10000 | 高優先級 | 可以搶占 | Dashboard, Prometheus, Grafana |
| **medium-priority** | 1000 | 中等優先級（預設）| 可以搶占 | Worker Service |
| **low-priority** | 100 | 低優先級 | 可以搶占 | Batch jobs |
| **best-effort** | 1 | 盡力而為 | 不能搶占 | Dev/test workloads |

### 優先級如何工作

1. **調度優先級**: 高優先級 Pod 優先被調度
2. **搶占機制**: 當資源不足時，高優先級 Pod 可以驅逐低優先級 Pod
3. **預設優先級**: medium-priority 為全局預設值

### 服務優先級分配

```yaml
# API Gateway (Critical)
spec:
  template:
    spec:
      priorityClassName: critical

# Dashboard (High)
spec:
  template:
    spec:
      priorityClassName: high-priority

# Worker Service (Medium)
spec:
  template:
    spec:
      priorityClassName: medium-priority
```

### 查看優先級

```bash
# 查看所有 PriorityClass
kubectl get priorityclass

# 查看 Pod 的優先級
kubectl get pods -n microservices-demo -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priorityClassName,PRIORITY-VALUE:.spec.priority
```

## HorizontalPodAutoscaler (HPA)

### 配置文件

- [k8s/api-gateway/hpa.yaml](../k8s/api-gateway/hpa.yaml)
- [k8s/worker-service/hpa.yaml](../k8s/worker-service/hpa.yaml)

### API Gateway HPA

```yaml
minReplicas: 2
maxReplicas: 10
metrics:
  - CPU: 70%
  - Memory: 80%
behavior:
  scaleUp:
    - 每 15 秒最多擴展 100% 或增加 2 個 Pod
    - 立即擴展（穩定窗口 0 秒）
  scaleDown:
    - 每 15 秒最多縮減 50% 或減少 1 個 Pod
    - 等待 5 分鐘穩定後才縮減
```

**設計考量**:
- **快速擴展**: 流量突增時立即響應
- **保守縮減**: 避免頻繁波動，等待 5 分鐘確認負載下降
- **最小副本**: 2 個副本保證高可用

### Worker Service HPA

```yaml
minReplicas: 1
maxReplicas: 5
metrics:
  - CPU: 70%
  - Memory: 80%
behavior:
  scaleUp:
    - 每 15 秒最多擴展 100% 或增加 1 個 Pod
    - 等待 30 秒穩定後擴展
  scaleDown:
    - 每 15 秒最多縮減 25% 或減少 1 個 Pod
    - 等待 10 分鐘穩定後才縮減
```

**設計考量**:
- **更長穩定窗口**: Worker 任務處理時間較長，避免頻繁擴縮容
- **保守縮減**: 25% 縮減比例（vs API Gateway 的 50%）
- **最小副本**: 1 個副本節省成本（非關鍵路徑）

### 自定義指標（需要 Prometheus Adapter）

我們的 HPA 配置包含註釋的自定義指標示例：

**API Gateway**:
- `http_requests_per_second`: 基於請求速率擴展
- `requests_in_progress`: 基於並發請求數擴展

**Worker Service**:
- `worker_tasks_in_progress`: 基於任務隊列長度擴展
- `worker_tasks_rate`: 基於任務處理速率擴展

### 測試 HPA

```bash
# 查看 HPA 狀態
kubectl get hpa -n microservices-demo

# 詳細查看 HPA
kubectl describe hpa api-gateway-hpa -n microservices-demo

# 觀察 HPA 自動擴展（持續監控）
kubectl get hpa -n microservices-demo -w

# 產生負載測試
kubectl run -it --rm load-generator --image=busybox --restart=Never -- /bin/sh
# 在 pod 內執行
while true; do wget -q -O- http://api-gateway-service.microservices-demo.svc.cluster.local:8080/api/status; done
```

## 資源請求與限制最佳實踐

### 當前服務配置

| 服務 | CPU Request | CPU Limit | Memory Request | Memory Limit |
|------|------------|-----------|----------------|--------------|
| API Gateway | 100m | 500m | 128Mi | 512Mi |
| Worker Service | 100m | 500m | 128Mi | 512Mi |
| Dashboard | 50m | 200m | 64Mi | 256Mi |
| Redis | 100m | 500m | 128Mi | 512Mi |
| Prometheus | 250m | 500m | 512Mi | 1Gi |
| Grafana | 100m | 200m | 256Mi | 512Mi |

### Request vs Limit 指南

#### CPU
- **Request**: 保證的 CPU 時間（調度依據）
- **Limit**: 最大 CPU 時間（可以被限流）
- **建議比例**: Limit = 2-5x Request

#### Memory
- **Request**: 保證的內存（調度依據）
- **Limit**: 最大內存（超過會被 OOMKilled）
- **建議比例**: Limit = 1.5-2x Request（避免 OOM）

### QoS 類別

Kubernetes 根據資源配置將 Pod 分為三個 QoS 類別：

1. **Guaranteed** (最高優先級)
   - requests = limits（CPU 和 Memory）
   - 最不容易被驅逐
   - 適用於：關鍵服務（Redis）

2. **Burstable** (中等優先級)
   - requests < limits 或只設置其中之一
   - 可以使用超過 request 的資源
   - 適用於：大多數應用服務

3. **BestEffort** (最低優先級)
   - 沒有設置 requests 和 limits
   - 最容易被驅逐
   - 適用於：臨時任務、測試工作負載

### 我們的 QoS 策略

```yaml
# Critical 服務: Guaranteed QoS
redis:
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"

# 應用服務: Burstable QoS
api-gateway:
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"
```

## 成本優化策略

### 1. 右側調整（Rightsizing）

定期檢查實際資源使用：

```bash
# 查看實際資源使用
kubectl top pods -n microservices-demo

# 查看歷史資源使用（需要 metrics-server）
kubectl top pods -n microservices-demo --containers

# 分析 Prometheus 指標
# 查看 CPU 使用率
container_cpu_usage_seconds_total

# 查看內存使用
container_memory_working_set_bytes
```

**調整原則**:
- Request 設置為 P95 實際使用量
- Limit 設置為 Request 的 2-3 倍（留有 burst 空間）

### 2. 節點自動擴展

配置 Cluster Autoscaler 根據 Pod 需求自動調整節點數量：

```yaml
# 需要在雲提供商配置
# AWS: aws-autoscaling-group
# GCP: instance-group
# Azure: virtual-machine-scale-set
```

### 3. 垂直 Pod 自動擴展（VPA）

VPA 可以自動調整 Pod 的資源請求：

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-gateway-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  updatePolicy:
    updateMode: "Auto"  # 自動應用建議
```

### 4. Spot/Preemptible 實例

對於低優先級工作負載使用 Spot 實例節省成本：

```yaml
# 使用 Node Affinity 將低優先級 Pod 調度到 Spot 節點
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 1
      preference:
        matchExpressions:
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
          - spot
```

## 監控資源使用

### Prometheus 指標

```promql
# CPU 使用率
sum(rate(container_cpu_usage_seconds_total{namespace="microservices-demo"}[5m])) by (pod)

# 內存使用
sum(container_memory_working_set_bytes{namespace="microservices-demo"}) by (pod)

# CPU 限流
sum(rate(container_cpu_cfs_throttled_seconds_total{namespace="microservices-demo"}[5m])) by (pod)

# 資源配額使用率
(kube_resourcequota{namespace="microservices-demo", type="used"} /
 kube_resourcequota{namespace="microservices-demo", type="hard"}) * 100
```

### Grafana 儀表板

在 Grafana 中創建資源使用儀表板：

1. **CPU 使用率**: 實際使用 vs Request vs Limit
2. **內存使用率**: 實際使用 vs Request vs Limit
3. **HPA 狀態**: 當前副本數、目標副本數、指標值
4. **ResourceQuota**: 已用配額 vs 總配額
5. **Pod QoS 分佈**: Guaranteed vs Burstable vs BestEffort

## 故障排查

### 問題 1: Pod 一直處於 Pending 狀態

**原因**: 資源不足

```bash
# 查看 Pod 事件
kubectl describe pod <pod-name> -n microservices-demo

# 常見錯誤信息
# "Insufficient cpu"
# "Insufficient memory"
# "Exceeded quota: microservices-quota"
```

**解決方案**:
1. 調整 ResourceQuota 增加配額
2. 減少 Pod 的資源請求
3. 增加集群節點
4. 刪除不必要的 Pod

### 問題 2: Pod 被 OOMKilled

**原因**: 內存使用超過 limit

```bash
# 查看 Pod 重啟原因
kubectl describe pod <pod-name> -n microservices-demo

# 查看日誌
kubectl logs <pod-name> -n microservices-demo --previous
```

**解決方案**:
1. 增加內存 limit
2. 優化應用內存使用
3. 檢查內存洩漏

### 問題 3: CPU 限流（Throttling）

**症狀**: 應用響應慢，但 CPU 使用未達到 100%

```bash
# 檢查 CPU 限流
kubectl top pods -n microservices-demo

# Prometheus 查詢
rate(container_cpu_cfs_throttled_seconds_total[5m])
```

**解決方案**:
1. 增加 CPU limit
2. 減少 CPU request/limit 比例
3. 考慮使用 CPU 密集型節點

### 問題 4: HPA 不工作

**檢查**:
```bash
# 檢查 metrics-server 是否運行
kubectl get deployment metrics-server -n kube-system

# 檢查 HPA 狀態
kubectl describe hpa <hpa-name> -n microservices-demo

# 檢查指標可用性
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/microservices-demo/pods
```

**解決方案**:
1. 確保 metrics-server 正常運行
2. 檢查 Pod 是否設置了資源請求
3. 驗證目標指標是否可用

## 面試展示要點

在面試中討論資源優化時，可以強調：

1. **完整的資源管理**: ResourceQuota + LimitRange + HPA + PriorityClass
2. **成本意識**: 通過配額和自動擴展控制成本
3. **高可用性**: 通過優先級確保關鍵服務不被驅逐
4. **彈性擴展**: HPA 根據負載自動調整副本數
5. **資源效率**: Request/Limit 設置合理，避免浪費
6. **監控驅動**: 基於實際使用數據優化資源配置
7. **生產級配置**: QoS、優先級、自動擴展行為都經過仔細設計

## 相關資源

- [Kubernetes Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [Limit Ranges](https://kubernetes.io/docs/concepts/policy/limit-range/)
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Pod Priority and Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/)
- [Configure Quality of Service](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/)
