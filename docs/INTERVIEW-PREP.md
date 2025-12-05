# 面試準備指南

這份文檔幫助你在技術面試中有效展示這個 Kubernetes 微服務專案。

## 目錄

- [專案總覽](#專案總覽)
- [技術亮點](#技術亮點)
- [面試Demo流程](#面試demo流程)
- [常見問題與回答](#常見問題與回答)
- [深入技術話題](#深入技術話題)
- [故障場景演示](#故障場景演示)

## 專案總覽

### 電梯簡報（30秒版本）

> "這是一個生產級的 Kubernetes 微服務專案，展示了完整的 DevOps/SRE 最佳實踐。包含三個微服務：API Gateway、Worker Service 和 Dashboard，使用 Redis 作為共享狀態存儲。我實施了完整的安全策略（NetworkPolicy、PodSecurityContext）、可觀測性（Prometheus + Grafana + 結構化日誌）、自動化測試（64+ 單元測試，>70% 覆蓋率）、和 CI/CD pipeline（4 階段，包含安全掃描）。整個專案有 20+ Kubernetes manifests，10+ 文檔頁面，是一個可以直接部署到生產環境的解決方案。"

### 核心指標

- **代碼覆蓋率**: >70%
- **測試數量**: 64+ 單元測試
- **服務數量**: 3 個微服務 + Redis + Prometheus + Grafana
- **Kubernetes資源**: 20+ manifests
- **CI/CD階段**: 4 階段 (Test → Security → Build → Push)
- **安全掃描**: 3 層 (Trivy, Bandit, Safety)
- **文檔頁面**: 10+ 完整文檔

## 技術亮點

### 1. 🏗 Kubernetes 生產級配置

**展示重點**:
- ✅ Pod 安全上下文（非 root 運行，只讀根文件系統）
- ✅ NetworkPolicy 零信任網絡模型
- ✅ PodDisruptionBudget 確保高可用
- ✅ Pod Anti-Affinity 分散副本
- ✅ HPA 自動擴展
- ✅ PriorityClass 工作負載優先級

**面試話術**:
> "我實施了完整的 Pod 安全策略。所有容器都以非 root 用戶運行，根文件系統設置為只讀，並且 drop 了所有 capabilities。這遵循了最小權限原則，即使容器被入侵，攻擊者也無法在容器內安裝工具或修改文件。"

**文件位置**:
- [k8s/api-gateway/deployment.yaml](../k8s/api-gateway/deployment.yaml:23-31) - securityContext
- [k8s/network-policies/](../k8s/network-policies/) - NetworkPolicy
- [k8s/api-gateway/pdb.yaml](../k8s/api-gateway/pdb.yaml) - PodDisruptionBudget

### 2. 🔒 三層安全掃描

**展示重點**:
- ✅ **Trivy**: 容器鏡像漏洞掃描（CVE 檢測）
- ✅ **Bandit**: Python 代碼安全問題掃描
- ✅ **Safety**: Python 依賴漏洞掃描

**面試話術**:
> "我實施了三層安全掃描策略。Trivy 掃描 Docker 鏡像的 OS 和應用層漏洞；Bandit 檢查代碼中的安全反模式，如硬編碼密碼或不安全的隨機數生成；Safety 檢查 Python 依賴是否有已知漏洞。所有掃描都集成在 CI pipeline 中，發現高危漏洞會阻止部署。"

**文件位置**:
- [.github/workflows/ci.yml](../.github/workflows/ci.yml:89-151) - Security scan jobs

### 3. 💎 應用代碼質量

**展示重點**:
- ✅ **Redis 連接池**: 健康檢查、自動重連、電路斷路器
- ✅ **結構化日誌**: JSON 格式，支持 ELK/CloudWatch
- ✅ **分散式追蹤**: trace_id 自動生成和傳播
- ✅ **輸入驗證**: marshmallow schema 驗證
- ✅ **速率限制**: Redis-based 滑動窗口算法

**面試話術**:
> "我實現了生產級的 Redis 連接池管理。連接池包含健康檢查（每 30 秒），自動重連機制，以及電路斷路器模式（3 次失敗後開啟）。這確保了即使 Redis 暫時不可用，應用也能優雅降級而不是立即崩潰。所有日誌都是 JSON 格式的結構化日誌，包含 trace_id、timestamp、service name 等字段，可以直接導入 ELK Stack 或 CloudWatch 進行聚合分析。"

**文件位置**:
- [services/api-gateway/redis_client.py](../services/api-gateway/redis_client.py) - 連接池實現
- [services/api-gateway/structured_logger.py](../services/api-gateway/structured_logger.py) - JSON 日誌
- [services/api-gateway/rate_limiter.py](../services/api-gateway/rate_limiter.py) - 速率限制

### 4. 🧪 測試覆蓋

**展示重點**:
- ✅ **64+ 單元測試**, >70% 覆蓋率
- ✅ **Mock 策略**: fakeredis, unittest.mock
- ✅ **測試隔離**: 每個測試獨立的 Redis 實例
- ✅ **CI 集成**: 每次 PR/push 自動運行

**面試話術**:
> "我實施了完整的測試策略。使用 fakeredis 來隔離 Redis 依賴，確保測試不需要真實的 Redis 服務器。每個測試都有獨立的 fixture，避免測試間的污染。測試覆蓋了健康檢查、速率限制、連接池管理、異常處理等關鍵路徑。在 CI 中，測試失敗會阻止合並，確保代碼質量。"

**文件位置**:
- [services/api-gateway/tests/](../services/api-gateway/tests/) - 測試套件
- [docs/TESTING.md](../docs/TESTING.md) - 測試文檔

### 5. 📊 可觀測性（Three Pillars）

**展示重點**:
- ✅ **指標**: Prometheus 收集，Grafana 可視化
- ✅ **日誌**: 結構化 JSON，包含 trace_id
- ✅ **追蹤**: 分散式追蹤，X-Trace-ID 傳播
- ✅ **告警**: 11 條告警規則（高錯誤率、高延遲、服務宕機等）

**面試話術**:
> "我實施了完整的三支柱可觀測性。指標方面，使用 Prometheus 收集 RED 指標（Rate, Errors, Duration），Grafana 展示儀表板。日誌方面，所有服務輸出 JSON 格式的結構化日誌，包含 trace_id、請求方法、狀態碼等字段。追蹤方面，每個請求自動分配或從 HTTP 頭提取 trace_id，並在服務間傳播，可以追蹤完整的請求鏈路。我還配置了 11 條告警規則，覆蓋錯誤率、延遲、服務健康、資源使用等關鍵指標。"

**文件位置**:
- [k8s/monitoring/prometheus-config.yaml](../k8s/monitoring/prometheus-config.yaml) - Prometheus 配置
- [k8s/monitoring/prometheus-rules.yaml](../k8s/monitoring/prometheus-rules.yaml) - 告警規則
- [k8s/monitoring/grafana-dashboards.yaml](../k8s/monitoring/grafana-dashboards.yaml) - Grafana 儀表板
- [docs/OBSERVABILITY.md](../docs/OBSERVABILITY.md) - 可觀測性文檔

### 6. 🚀 CI/CD Pipeline

**展示重點**:
- ✅ **4 階段 Pipeline**: Test → Security → Build → Push
- ✅ **並行執行**: 3 個服務同時測試和構建
- ✅ **緩存優化**: pip 依賴緩存，Docker layer 緩存
- ✅ **Codecov 集成**: 自動上傳覆蓋率報告

**面試話術**:
> "我設計了一個 4 階段的 CI/CD pipeline。第一階段運行所有服務的測試並生成覆蓋率報告；第二階段並行執行三種安全掃描；第三階段構建 Docker 鏡像；第四階段推送到 Docker Hub。整個 pipeline 使用 matrix strategy 並行處理三個服務，配合 pip 和 Docker layer 緩存，平均執行時間控制在 8-13 分鐘。"

**文件位置**:
- [.github/workflows/ci.yml](../.github/workflows/ci.yml) - CI Pipeline
- [docs/CI-CD.md](../docs/CI-CD.md) - CI/CD 文檔

### 7. 🎛 資源管理與優化

**展示重點**:
- ✅ **ResourceQuota**: 命名空間級別資源配額
- ✅ **LimitRange**: 預設資源限制
- ✅ **HPA**: 自動擴展（CPU 70%, Memory 80%）
- ✅ **PriorityClass**: 關鍵服務優先級

**面試話術**:
> "我實施了完整的資源管理策略。ResourceQuota 限制整個命名空間的資源使用（8 cores CPU requests, 16Gi memory）。LimitRange 為沒有指定資源的 Pod 設置預設值。HPA 根據 CPU（70%）和 Memory（80%）自動擴展，API Gateway 可以從 2 擴展到 10 個副本。PriorityClass 確保關鍵服務（API Gateway、Redis）在資源不足時不會被搶占。"

**文件位置**:
- [k8s/resource-quota.yaml](../k8s/resource-quota.yaml) - ResourceQuota
- [k8s/limit-range.yaml](../k8s/limit-range.yaml) - LimitRange
- [k8s/priority-classes.yaml](../k8s/priority-classes.yaml) - PriorityClass
- [docs/RESOURCE-OPTIMIZATION.md](../docs/RESOURCE-OPTIMIZATION.md) - 資源優化文檔

## 面試 Demo 流程

### Demo 1: 快速部署（5 分鐘）

```bash
# 1. 啟動 Minikube
minikube start --cpus=4 --memory=8192
minikube addons enable ingress metrics-server

# 2. 配置 Docker 環境
eval $(minikube docker-env)

# 3. 構建鏡像
./scripts/build-images.sh

# 4. 部署到 Kubernetes
./scripts/deploy.sh

# 5. 查看部署狀態
kubectl get pods -n microservices-demo
kubectl get svc -n microservices-demo
kubectl get hpa -n microservices-demo

# 6. 訪問服務
minikube service dashboard-service -n microservices-demo
```

**講解要點**:
- 自動化腳本簡化部署流程
- 所有 Pod 運行正常
- HPA 已配置並監控中
- 服務可以通過 LoadBalancer 訪問

### Demo 2: 健康檢查與監控（3 分鐘）

```bash
# 1. 測試健康檢查
kubectl port-forward -n microservices-demo svc/api-gateway-service 8080:8080
curl http://localhost:8080/health/live    # Liveness probe
curl http://localhost:8080/health/ready   # Readiness probe (含依賴檢查)

# 2. 查看 Prometheus 指標
curl http://localhost:8080/metrics | grep api_gateway

# 3. 訪問 Prometheus UI
kubectl port-forward -n microservices-demo svc/prometheus 9090:9090
# 訪問 http://localhost:9090
# 查詢: rate(api_gateway_requests_total[5m])

# 4. 訪問 Grafana
kubectl port-forward -n microservices-demo svc/grafana 3000:3000
# 訪問 http://localhost:3000 (admin/admin123)
# 查看 "Microservices Overview" 儀表板
```

**講解要點**:
- Readiness probe 檢查 Redis 連接狀態
- Prometheus 收集自定義指標
- Grafana 儀表板實時顯示 RED 指標

### Demo 3: 分散式追蹤（2 分鐘）

```bash
# 1. 發送帶 trace_id 的請求
curl -H "X-Trace-ID: demo-trace-12345" http://localhost:8080/api/status

# 2. 查看日誌中的 trace_id
kubectl logs -n microservices-demo -l app=api-gateway --tail=20 | grep demo-trace-12345

# 3. 查看響應頭
curl -v -H "X-Trace-ID: demo-trace-12345" http://localhost:8080/api/status
# 查看響應頭中的 X-Trace-ID
```

**講解要點**:
- trace_id 自動生成或從請求頭提取
- 在所有日誌中包含 trace_id
- 在響應中返回 trace_id

### Demo 4: 速率限制（2 分鐘）

```bash
# 1. 快速發送多個請求（超過限制）
for i in {1..70}; do
  curl -w "\n%{http_code}\n" http://localhost:8080/api/status
done

# 應該看到前 60 個請求返回 200，後面返回 429 Too Many Requests

# 2. 查看速率限制頭
curl -v http://localhost:8080/api/status
# 查看 X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
```

**講解要點**:
- Redis-based 滑動窗口算法
- 每分鐘 60 個請求限制
- 響應頭包含限制信息

### Demo 5: 自動擴展（5 分鐘）

```bash
# 1. 查看當前 HPA 狀態
kubectl get hpa -n microservices-demo

# 2. 產生負載
kubectl run -it --rm load-generator --image=busybox --restart=Never -- /bin/sh
# 在 pod 內執行
while true; do wget -q -O- http://api-gateway-service.microservices-demo.svc.cluster.local:8080/api/status; done

# 3. 在另一個終端觀察自動擴展
watch kubectl get hpa -n microservices-demo
watch kubectl get pods -n microservices-demo -l app=api-gateway

# 4. 查看 HPA 事件
kubectl describe hpa api-gateway-hpa -n microservices-demo
```

**講解要點**:
- HPA 根據 CPU 和 Memory 自動擴展
- 擴展行為配置（快速擴展，保守縮減）
- 最小 2 副本，最大 10 副本

### Demo 6: 安全配置（3 分鐘）

```bash
# 1. 查看 Pod 安全上下文
kubectl get pod -n microservices-demo -l app=api-gateway -o jsonpath='{.items[0].spec.securityContext}'

# 2. 驗證非 root 運行
kubectl exec -n microservices-demo -it deployment/api-gateway -- id
# 應該看到 uid=1000 而不是 uid=0

# 3. 查看 NetworkPolicy
kubectl get networkpolicy -n microservices-demo
kubectl describe networkpolicy api-gateway-allow -n microservices-demo

# 4. 測試網絡隔離
kubectl run test-pod --image=busybox --restart=Never -it --rm -- wget -T 5 http://api-gateway-service.microservices-demo.svc.cluster.local:8080
# 應該超時（因為不在白名單中）
```

**講解要點**:
- 所有容器以非 root 用戶運行
- NetworkPolicy 實施零信任網絡模型
- 只有白名單內的 Pod 可以訪問服務

## 常見問題與回答

### Q1: 為什麼選擇 Python/Flask？

**回答**:
> "我選擇 Python 和 Flask 因為它們適合快速原型開發和微服務架構。Python 有豐富的庫生態（Redis 客戶端、Prometheus 客戶端、測試框架），Flask 輕量且易於擴展。在生產環境中，我會考慮使用 FastAPI（更好的性能和類型檢查）或 Go（更低的資源佔用）。"

### Q2: 如何處理 Redis 故障？

**回答**:
> "我實施了多層保護：1) 連接池包含健康檢查和自動重連；2) 電路斷路器模式，3 次失敗後開啟，避免雪崩；3) 速率限制使用 fail-open 設計，Redis 不可用時允許所有請求通過；4) Readiness probe 檢查 Redis 狀態，不健康的 Pod 會被從負載均衡中移除。在生產環境中，會使用 AWS ElastiCache 或 GCP Memorystore 等託管服務，並配置主從複製和自動故障轉移。"

### Q3: 如何保證零停機部署？

**回答**:
> "我使用了多種策略：1) Deployment 配置滾動更新，maxSurge=1, maxUnavailable=0，確保始終有足夠的副本；2) Readiness probe 確保新 Pod 完全就緒後才接收流量；3) PodDisruptionBudget 確保維護時至少保留 1 個副本；4) PreStop hook 給予容器 30 秒優雅關閉時間。整個更新過程中，用戶不會感受到任何中斷。"

### Q4: 測試覆蓋率只有 70%，為什麼不是 100%？

**回答**:
> "我遵循實用的測試策略。70% 覆蓋率已經覆蓋了所有關鍵路徑和業務邏輯。未覆蓋的部分主要是：1) 框架樣板代碼（Flask app 初始化）；2) 錯誤處理的邊緣情況；3) 日誌和指標收集代碼。追求 100% 覆蓋率的邊際收益很低，反而會增加維護成本。我專注於高價值的測試，確保核心功能的正確性。"

### Q5: 如何監控和調試生產問題？

**回答**:
> "我實施了完整的可觀測性策略：1) 通過 Prometheus 監控 RED 指標，Grafana 可視化；2) 結構化 JSON 日誌可以導入 ELK Stack，按 trace_id 查詢完整請求鏈路；3) 11 條告警規則覆蓋關鍵指標，Slack/PagerDuty 通知；4) 健康檢查端點顯示依賴狀態；5) 每個請求都有唯一的 trace_id，可以從用戶報告追蹤到具體的日誌行。"

### Q6: 如何處理敏感信息（密碼、API 密鑰）？

**回答**:
> "我使用 Kubernetes Secrets 存儲敏感信息，並遵循最佳實踐：1) 永不硬編碼或提交到 Git；2) 使用環境變量或掛載文件注入容器；3) RBAC 限制誰可以讀取 Secrets；4) 在生產環境中，會使用 AWS Secrets Manager、HashiCorp Vault 等專業密鑰管理服務；5) 定期輪換密鑰；6) 所有敏感日誌都被過濾或脫敏。"

### Q7: 如何進行容量規劃？

**回答**:
> "我使用數據驅動的方法：1) Prometheus 收集實際資源使用數據（CPU、內存、請求速率）；2) 分析 P95/P99 使用量，設置 requests 為 P95，limits 為 P95 的 2-3 倍；3) 負載測試驗證擴展策略；4) HPA 根據實際負載自動調整副本數；5) ResourceQuota 防止資源耗盡；6) 定期 review 實際使用情況，調整配置。"

## 深入技術話題

### 話題 1: RED 方法實施

**準備內容**:
- Rate: `rate(api_gateway_requests_total[5m])`
- Errors: `rate(api_gateway_requests_total{status=~"5.."}[5m])`
- Duration: `histogram_quantile(0.95, api_gateway_request_duration_seconds_bucket)`

**Demo 代碼**:
```python
# services/api-gateway/app.py
REQUEST_COUNT = Counter(
    'api_gateway_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'api_gateway_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)
```

### 話題 2: 電路斷路器模式

**準備內容**:
電路斷路器的三個狀態：Closed → Open → Half-Open

**Demo 代碼**:
```python
# services/api-gateway/redis_client.py:78-105
if self.circuit_breaker_state == "open":
    # 檢查是否可以嘗試恢復
    if time.time() - self.circuit_breaker_opened_at > self.circuit_breaker_timeout:
        self.circuit_breaker_state = "half-open"
```

### 話題 3: 滑動窗口速率限制

**準備內容**:
使用 Redis Sorted Set 實現滑動窗口，比固定窗口更精確

**Demo 代碼**:
```python
# services/api-gateway/rate_limiter.py:35-50
# 移除過期條目
self.redis_client._client.zremrangebyscore(redis_key, 0, window_start)
# 檢查當前計數
current_count = self.redis_client._client.zcard(redis_key)
if current_count < limit:
    # 添加當前時間戳
    self.redis_client._client.zadd(redis_key, {str(current_time): current_time})
```

## 故障場景演示

### 場景 1: Redis 宕機

```bash
# 1. 模擬 Redis 宕機
kubectl scale deployment/redis --replicas=0 -n microservices-demo

# 2. 查看 API Gateway 行為
curl http://localhost:8080/health/ready
# 應該返回 503，dependencies.redis.healthy = false

curl http://localhost:8080/api/status
# 速率限制 fail-open，請求仍然成功

# 3. 查看日誌
kubectl logs -n microservices-demo -l app=api-gateway --tail=20
# 應該看到 Redis 連接錯誤日誌

# 4. 恢復 Redis
kubectl scale deployment/redis --replicas=1 -n microservices-demo

# 5. 驗證自動恢復
curl http://localhost:8080/health/ready
# 應該返回 200，Redis 自動重連
```

**講解要點**:
- Readiness probe 檢測到 Redis 故障
- 速率限制 fail-open 保證可用性
- 自動重連機制生效

### 場景 2: Pod 被驅逐

```bash
# 1. 模擬節點維護
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 2. 觀察 Pod 重新調度
watch kubectl get pods -n microservices-demo -o wide

# 3. 驗證 PodDisruptionBudget
kubectl get pdb -n microservices-demo
# available 應該始終 >= 1

# 4. 驗證服務可用性
while true; do curl http://localhost:8080/api/status; sleep 1; done
# 應該沒有中斷
```

**講解要點**:
- PodDisruptionBudget 保證最小副本數
- Pod Anti-Affinity 確保副本分散
- 滾動更新策略保證零停機

### 場景 3: 資源耗盡

```bash
# 1. 創建資源密集型 Pod
kubectl run resource-hog --image=progrium/stress \
  --namespace=microservices-demo \
  --requests='cpu=2,memory=4Gi' \
  -- --cpu 2 --vm 1 --vm-bytes 3G

# 2. 觀察調度失敗
kubectl describe pod resource-hog -n microservices-demo
# 應該看到 "Insufficient cpu" 或 "Exceeded quota"

# 3. 驗證 ResourceQuota 保護
kubectl describe resourcequota -n microservices-demo
# 應該接近限制但未超過

# 4. 清理
kubectl delete pod resource-hog -n microservices-demo
```

**講解要點**:
- ResourceQuota 防止資源耗盡
- LimitRange 設置預設限制
- 資源管理保護關鍵服務

## 項目改進方向（展示思考深度）

### 短期改進
1. **實施 Prometheus Adapter** - 基於自定義指標（請求速率、隊列長度）自動擴展
2. **添加 E2E 測試** - 使用 pytest-bdd 或 Robot Framework
3. **實施 Jaeger** - 完整的分散式追蹤可視化
4. **配置 Alertmanager** - 告警路由、抑制、分組

### 中期改進
1. **服務網格（Istio/Linkerd）** - mTLS、流量管理、金絲雀發布
2. **GitOps（ArgoCD）** - 聲明式部署、自動同步
3. **Chaos Engineering** - 使用 Chaos Mesh 測試彈性
4. **多集群部署** - 跨區域高可用

### 長期改進
1. **事件驅動架構** - 引入 Kafka/NATS 實現異步通信
2. **API Gateway 升級** - 使用 Kong/Envoy 替代自定義網關
3. **可觀測性升級** - OpenTelemetry 統一遙測數據
4. **成本優化** - FinOps 實踐、Spot 實例、資源右側調整

## 最後建議

### Demo 前檢查清單

- [ ] Minikube 正常運行
- [ ] 所有腳本可執行權限
- [ ] 熟悉所有 Demo 命令
- [ ] 準備好文檔鏈接
- [ ] 網絡連接穩定
- [ ] 瀏覽器標籤頁準備好

### 時間分配建議

- **5 分鐘**: 專案總覽和架構
- **10 分鐘**: 現場 Demo（部署、監控、追蹤）
- **10 分鐘**: 代碼走查（重點模塊）
- **5 分鐘**: 回答問題

### 面試心態

- ✅ 自信但不傲慢
- ✅ 承認不足，展示學習能力
- ✅ 實事求是，不過度誇大
- ✅ 主動提出改進方向
- ✅ 關注業務價值，不只是技術

祝你面試順利！
