# Troubleshooting Guide

常見問題排查和解決方案指南。

## 目錄

- [Pod 相關問題](#pod-相關問題)
- [網路相關問題](#網路相關問題)
- [資源相關問題](#資源相關問題)
- [HPA 相關問題](#hpa-相關問題)
- [Ingress 相關問題](#ingress-相關問題)
- [應用相關問題](#應用相關問題)
- [Debug 工具和命令](#debug-工具和命令)

---

## Pod 相關問題

### 問題：Pod 狀態為 Pending

**症狀**:
```bash
kubectl get pods -n microservices-demo
NAME                           READY   STATUS    RESTARTS   AGE
api-gateway-xxx                0/1     Pending   0          2m
```

**可能原因**:
1. 資源不足（CPU/Memory）
2. PersistentVolumeClaim 未綁定
3. Node 選擇器不匹配

**排查步驟**:

```bash
# 查看詳細事件
kubectl describe pod <pod-name> -n microservices-demo

# 查看 node 資源
kubectl top nodes

# 查看所有 events
kubectl get events -n microservices-demo --sort-by='.lastTimestamp'
```

**解決方案**:

**資源不足**:
```bash
# Minikube - 增加資源
minikube stop
minikube start --cpus=4 --memory=8192

# 或降低資源請求
# 編輯 deployment.yaml，減少 resources.requests
```

**PVC 問題**:
```bash
# 查看 PVC 狀態
kubectl get pvc -n microservices-demo

# 檢查 StorageClass
kubectl get storageclass
```

---

### 問題：Pod 狀態為 CrashLoopBackOff

**症狀**:
```bash
NAME                           READY   STATUS             RESTARTS   AGE
api-gateway-xxx                0/1     CrashLoopBackOff   5          3m
```

**可能原因**:
1. 應用啟動失敗
2. 健康檢查失敗
3. 缺少環境變數或配置
4. 依賴服務不可用（如 Redis）

**排查步驟**:

```bash
# 查看 Pod 日誌
kubectl logs <pod-name> -n microservices-demo

# 查看上一次運行的日誌
kubectl logs <pod-name> -n microservices-demo --previous

# 查看事件
kubectl describe pod <pod-name> -n microservices-demo

# 進入容器 debug（如果還在運行）
kubectl exec -it <pod-name> -n microservices-demo -- /bin/sh
```

**解決方案**:

**應用錯誤**:
```bash
# 檢查日誌中的錯誤訊息
kubectl logs <pod-name> -n microservices-demo | grep -i error

# 常見錯誤：
# - ImportError: 缺少 Python 套件
# - ConnectionError: 無法連接 Redis
# - PermissionError: 文件權限問題
```

**健康檢查太激進**:
```yaml
# 編輯 deployment.yaml，調整探針參數
livenessProbe:
  initialDelaySeconds: 60  # 增加延遲
  periodSeconds: 15        # 增加間隔
  failureThreshold: 5      # 增加容錯次數
```

**環境變數缺失**:
```bash
# 檢查 ConfigMap 和 Secret
kubectl get configmap app-config -n microservices-demo -o yaml
kubectl get secret app-secrets -n microservices-demo -o yaml

# 驗證環境變數是否正確注入
kubectl exec <pod-name> -n microservices-demo -- env | grep -i redis
```

---

### 問題：Pod 狀態為 ImagePullBackOff

**症狀**:
```bash
NAME                           READY   STATUS             RESTARTS   AGE
api-gateway-xxx                0/1     ImagePullBackOff   0          1m
```

**可能原因**:
1. Image 名稱錯誤
2. Image 不存在
3. 私有 registry 認證失敗
4. 網路問題

**排查步驟**:

```bash
# 查看詳細資訊
kubectl describe pod <pod-name> -n microservices-demo

# 查看事件（會顯示具體錯誤）
kubectl get events -n microservices-demo | grep <pod-name>
```

**解決方案**:

**本地開發（Minikube）**:
```bash
# 確保使用 Minikube 的 Docker daemon
eval $(minikube docker-env)

# 重新建置 images
./scripts/build-images.sh

# 驗證 images 存在
docker images | grep -E 'api-gateway|worker-service|dashboard'

# 重啟 deployment
kubectl rollout restart deployment/<deployment-name> -n microservices-demo
```

**生產環境**:
```bash
# 檢查 image 名稱是否正確
kubectl get deployment <deployment-name> -n microservices-demo -o yaml | grep image:

# 確認 Docker Hub 上存在該 image
docker pull <your-username>/api-gateway:v1.0.0

# 如果使用私有 registry，創建 imagePullSecrets
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<username> \
  --docker-password=<password> \
  -n microservices-demo

# 在 deployment 中添加
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
```

---

### 問題：Pod 頻繁重啟

**症狀**:
```bash
NAME                           READY   STATUS    RESTARTS   AGE
api-gateway-xxx                1/1     Running   15         10m
```

**可能原因**:
1. 內存不足（OOMKilled）
2. Liveness probe 失敗
3. 應用內部錯誤

**排查步驟**:

```bash
# 查看重啟原因
kubectl describe pod <pod-name> -n microservices-demo

# 查看資源使用
kubectl top pod <pod-name> -n microservices-demo

# 查看日誌
kubectl logs <pod-name> -n microservices-demo --previous
```

**解決方案**:

**OOMKilled (記憶體不足)**:
```yaml
# 增加 memory limits
resources:
  limits:
    memory: 1024Mi  # 從 512Mi 增加到 1024Mi
```

**Liveness probe 失敗**:
```bash
# 手動測試健康檢查端點
kubectl exec <pod-name> -n microservices-demo -- curl http://localhost:8080/health/live

# 調整 probe 設定
livenessProbe:
  initialDelaySeconds: 60
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 5
```

---

## 網路相關問題

### 問題：無法訪問服務

**症狀**:
- 無法通過 Service 訪問 Pod
- `curl: (7) Failed to connect`

**排查步驟**:

```bash
# 1. 檢查 Service 是否存在
kubectl get svc -n microservices-demo

# 2. 檢查 Service endpoints
kubectl get endpoints -n microservices-demo

# 3. 檢查 Pod 標籤是否匹配
kubectl get pods -n microservices-demo --show-labels

# 4. 測試 Pod IP 直連
POD_IP=$(kubectl get pod <pod-name> -n microservices-demo -o jsonpath='{.status.podIP}')
kubectl run test-pod --image=busybox --rm -it -- wget -O- http://$POD_IP:8080/health/live
```

**解決方案**:

**Service selector 不匹配**:
```bash
# 檢查 Service selector
kubectl get svc api-gateway-service -n microservices-demo -o yaml | grep -A 2 selector

# 檢查 Pod labels
kubectl get pods -n microservices-demo -l app=api-gateway --show-labels

# 確保標籤匹配
```

**Readiness probe 失敗**:
```bash
# Pods 沒有準備好不會加入 endpoints
kubectl describe pod <pod-name> -n microservices-demo | grep -A 5 Readiness

# 修復應用或調整 readiness probe
```

---

### 問題：服務間無法通信

**症狀**:
- Dashboard 無法連接 API Gateway
- API Gateway 無法連接 Redis

**排查步驟**:

```bash
# 從一個 Pod 測試連接另一個服務
kubectl exec -it <dashboard-pod> -n microservices-demo -- sh

# 在 Pod 內測試
curl http://api-gateway-service:8080/health/live
ping redis-service

# 檢查 DNS 解析
nslookup api-gateway-service
nslookup api-gateway-service.microservices-demo.svc.cluster.local
```

**解決方案**:

**DNS 問題**:
```bash
# 檢查 CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 使用完整 DNS 名稱
http://api-gateway-service.microservices-demo.svc.cluster.local:8080
```

**Network Policy 阻擋**:
```bash
# 檢查 Network Policies
kubectl get networkpolicies -n microservices-demo

# 如果有，可能需要調整規則
```

---

## 資源相關問題

### 問題：Node 資源不足

**症狀**:
- Pods 無法調度
- Events 顯示 "Insufficient cpu" 或 "Insufficient memory"

**排查步驟**:

```bash
# 查看 Node 資源
kubectl top nodes

# 查看 Node 詳情
kubectl describe node <node-name>

# 查看資源請求總和
kubectl describe nodes | grep -A 5 "Allocated resources"
```

**解決方案**:

**Minikube**:
```bash
minikube stop
minikube start --cpus=6 --memory=12288
```

**生產環境**:
- 添加更多 Worker nodes
- 優化資源請求和限制
- 使用 Cluster Autoscaler

---

### 問題：磁盤空間不足

**症狀**:
- Pods 無法啟動
- Events 顯示 "disk pressure"

**排查步驟**:

```bash
# Minikube
minikube ssh
df -h

# 查看 Docker 磁盤使用
docker system df
```

**解決方案**:

```bash
# 清理未使用的 images
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的 volumes
docker volume prune

# 清理所有未使用的資源
docker system prune -a --volumes
```

---

## HPA 相關問題

### 問題：HPA 沒有 metrics

**症狀**:
```bash
kubectl get hpa -n microservices-demo
NAME                  REFERENCE                TARGETS         MINPODS   MAXPODS
api-gateway-hpa       Deployment/api-gateway   <unknown>/70%   2         10
```

**可能原因**:
1. Metrics Server 未安裝
2. Metrics Server 未就緒
3. Pod 沒有設定資源請求

**排查步驟**:

```bash
# 檢查 Metrics Server
kubectl get deployment metrics-server -n kube-system

# 檢查 Metrics Server 日誌
kubectl logs -n kube-system -l k8s-app=metrics-server

# 測試 metrics API
kubectl top nodes
kubectl top pods -n microservices-demo
```

**解決方案**:

**Minikube**:
```bash
minikube addons enable metrics-server
```

**其他環境**:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**自簽名證書問題**:
```bash
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

**缺少資源請求**:
```yaml
# 確保 deployment 中有 resources.requests
resources:
  requests:
    cpu: 100m
    memory: 128Mi
```

---

### 問題：HPA 不擴展

**症狀**:
- CPU/Memory 超過目標值
- Pod 數量沒有增加

**排查步驟**:

```bash
# 查看 HPA 詳情
kubectl describe hpa <hpa-name> -n microservices-demo

# 查看 HPA 事件
kubectl get events -n microservices-demo | grep HorizontalPodAutoscaler

# 查看當前 metrics
kubectl get hpa <hpa-name> -n microservices-demo -o yaml
```

**解決方案**:

**已達到 maxReplicas**:
```yaml
# 增加 maxReplicas
spec:
  maxReplicas: 20  # 從 10 增加到 20
```

**資源限制**:
- 確保 cluster 有足夠資源容納新 Pods
- 檢查 ResourceQuotas

---

## Ingress 相關問題

### 問題：Ingress 無法訪問

**症狀**:
- 無法通過 Ingress 訪問應用
- 404 或 503 錯誤

**排查步驟**:

```bash
# 檢查 Ingress
kubectl get ingress -n microservices-demo

# 查看詳情
kubectl describe ingress microservices-ingress -n microservices-demo

# 檢查 Ingress Controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

**解決方案**:

**Ingress Controller 未安裝**:
```bash
# Minikube
minikube addons enable ingress

# 其他環境
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.5/deploy/static/provider/cloud/deploy.yaml
```

**Host 配置問題**:
```bash
# 確認 /etc/hosts 配置
cat /etc/hosts | grep microservices-demo

# 或使用 IP 直接訪問
curl http://<ingress-ip>/api/status
```

**Backend Service 不可用**:
```bash
# 檢查 Service 和 Endpoints
kubectl get endpoints -n microservices-demo
```

---

## 應用相關問題

### 問題：Redis 連接失敗

**症狀**:
- 應用日誌顯示 "ConnectionError: Error connecting to Redis"
- Readiness probe 失敗

**排查步驟**:

```bash
# 檢查 Redis Pod
kubectl get pods -n microservices-demo -l app=redis

# 測試 Redis 連接
kubectl exec -it <redis-pod> -n microservices-demo -- redis-cli ping

# 從應用 Pod 測試
kubectl exec -it <api-gateway-pod> -n microservices-demo -- sh
# 在 Pod 內
ping redis-service
nc -zv redis-service 6379
```

**解決方案**:

**Redis 未就緒**:
```bash
# 查看 Redis 日誌
kubectl logs -l app=redis -n microservices-demo

# 重啟 Redis
kubectl rollout restart deployment/redis -n microservices-demo
```

**配置錯誤**:
```bash
# 檢查 ConfigMap 中的 Redis 配置
kubectl get configmap app-config -n microservices-demo -o yaml | grep REDIS

# 應該是：
# REDIS_HOST: redis-service
# REDIS_PORT: "6379"
```

---

### 問題：Dashboard 顯示服務不可達

**症狀**:
- Dashboard 顯示所有服務為 "unreachable"
- 瀏覽器控制台顯示網路錯誤

**排查步驟**:

```bash
# 從 Dashboard Pod 測試
kubectl exec -it <dashboard-pod> -n microservices-demo -- sh

# 測試 API Gateway 連接
curl http://api-gateway-service:8080/health/live
curl http://api-gateway-service:8080/api/status
```

**解決方案**:

**Service URL 配置錯誤**:
```bash
# 檢查 ConfigMap
kubectl get configmap app-config -n microservices-demo -o yaml

# 確保：
# API_GATEWAY_URL: "http://api-gateway-service:8080"
# WORKER_SERVICE_URL: "http://worker-service:8081"
```

**CORS 問題**（如果從瀏覽器直接訪問）:
- 這個專案不應該有 CORS 問題，因為都是後端調用
- 如果有，需要在 API Gateway 添加 CORS headers

---

## Debug 工具和命令

### 基本診斷命令

```bash
# 查看所有資源
kubectl get all -n microservices-demo

# 查看事件（按時間排序）
kubectl get events -n microservices-demo --sort-by='.lastTimestamp'

# 查看特定資源的詳細資訊
kubectl describe pod/<pod-name> -n microservices-demo
kubectl describe svc/<service-name> -n microservices-demo
kubectl describe deployment/<deployment-name> -n microservices-demo

# 查看日誌
kubectl logs <pod-name> -n microservices-demo
kubectl logs <pod-name> -n microservices-demo --previous  # 上一次運行
kubectl logs -f <pod-name> -n microservices-demo  # 即時追蹤

# 多個 Pod 的日誌
kubectl logs -l app=api-gateway -n microservices-demo --tail=100
```

### 進入 Pod Debug

```bash
# 進入運行中的 Pod
kubectl exec -it <pod-name> -n microservices-demo -- /bin/sh

# 執行單一命令
kubectl exec <pod-name> -n microservices-demo -- env
kubectl exec <pod-name> -n microservices-demo -- ls -la
kubectl exec <pod-name> -n microservices-demo -- cat /etc/hosts

# 測試網路連接
kubectl exec <pod-name> -n microservices-demo -- ping google.com
kubectl exec <pod-name> -n microservices-demo -- wget -O- http://api-gateway-service:8080/health/live
```

### 臨時 Debug Pod

```bash
# 創建臨時 debug pod
kubectl run debug-pod --image=nicolaka/netshoot --rm -it -n microservices-demo -- /bin/bash

# 在 debug pod 內可以使用各種網路工具
# curl, wget, nslookup, dig, ping, traceroute, netstat 等
```

### Port Forward

```bash
# 本地端口轉發（用於測試）
kubectl port-forward -n microservices-demo svc/api-gateway-service 8080:8080
kubectl port-forward -n microservices-demo pod/<pod-name> 8080:8080

# 然後在本地訪問
curl http://localhost:8080/health/live
```

### 資源監控

```bash
# 即時查看資源使用
kubectl top nodes
kubectl top pods -n microservices-demo

# 持續監控
watch kubectl top pods -n microservices-demo

# 監控特定 deployment
watch kubectl get pods -n microservices-demo -l app=api-gateway
```

### 配置驗證

```bash
# 驗證 YAML 語法（不實際部署）
kubectl apply -f k8s/api-gateway/deployment.yaml --dry-run=client

# 查看實際應用的配置
kubectl get deployment api-gateway -n microservices-demo -o yaml

# 比較本地文件和集群中的配置
kubectl diff -f k8s/api-gateway/deployment.yaml
```

### 回滾部署

```bash
# 查看部署歷史
kubectl rollout history deployment/api-gateway -n microservices-demo

# 回滾到上一個版本
kubectl rollout undo deployment/api-gateway -n microservices-demo

# 回滾到特定版本
kubectl rollout undo deployment/api-gateway --to-revision=2 -n microservices-demo

# 暫停和恢復部署
kubectl rollout pause deployment/api-gateway -n microservices-demo
kubectl rollout resume deployment/api-gateway -n microservices-demo
```

### 清理和重啟

```bash
# 重啟 deployment（重新創建所有 Pods）
kubectl rollout restart deployment/api-gateway -n microservices-demo

# 刪除並重新創建 Pod
kubectl delete pod <pod-name> -n microservices-demo

# 強制刪除卡住的 Pod
kubectl delete pod <pod-name> -n microservices-demo --force --grace-period=0

# 清理失敗的 Pods
kubectl delete pods --field-selector status.phase=Failed -n microservices-demo
```

## 獲取幫助

如果問題仍未解決：

1. **查看官方文檔**:
   - [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug/)
   - [Pod Debug](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)

2. **社區支持**:
   - Stack Overflow（標籤：kubernetes）
   - Kubernetes Slack

3. **查看專案 Issues**:
   - GitHub Issues: https://github.com/your-repo/issues

4. **啟用詳細日誌**:
   ```bash
   # 修改 ConfigMap 設定日誌級別為 DEBUG
   kubectl edit configmap app-config -n microservices-demo
   # 修改 LOG_LEVEL: "DEBUG"

   # 重啟 pods 使設定生效
   kubectl rollout restart deployment/<deployment-name> -n microservices-demo
   ```
