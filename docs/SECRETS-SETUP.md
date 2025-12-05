# GitHub Secrets 配置指南

這份文檔說明了 CI/CD Pipeline 所需的 GitHub Secrets 配置。

## 概述

我們的 CI/CD workflow 需要以下 secrets 才能正常運行：

| Secret 名稱 | 用途 | 必需 | 使用位置 |
|------------|------|------|---------|
| `DOCKER_HUB_USERNAME` | Docker Hub 用戶名 | ✅ 是 | ci.yml, cd.yml |
| `DOCKER_HUB_TOKEN` | Docker Hub 訪問令牌 | ✅ 是 | ci.yml |
| `KUBE_CONFIG` | Kubernetes 集群配置（base64 編碼） | ✅ 是 | cd.yml |

---

## 配置步驟

### 1. Docker Hub Secrets

#### 獲取 Docker Hub Token

1. 登錄 [Docker Hub](https://hub.docker.com/)
2. 點擊右上角頭像 → **Account Settings**
3. 選擇 **Security** 標籤
4. 點擊 **New Access Token**
5. 輸入描述（如 "GitHub Actions CI/CD"）
6. 選擇權限：**Read, Write, Delete**
7. 點擊 **Generate**
8. **立即複製 token**（只會顯示一次！）

#### 配置到 GitHub

1. 進入您的 GitHub repository
2. 點擊 **Settings** → **Secrets and variables** → **Actions**
3. 點擊 **New repository secret**
4. 添加以下 secrets：

**DOCKER_HUB_USERNAME**:
- Name: `DOCKER_HUB_USERNAME`
- Secret: 您的 Docker Hub 用戶名（如 `myusername`）

**DOCKER_HUB_TOKEN**:
- Name: `DOCKER_HUB_TOKEN`
- Secret: 剛才生成的 access token

---

### 2. Kubernetes Config Secret

#### 獲取 kubeconfig

```bash
# 方法 1：使用當前的 kubeconfig
cat ~/.kube/config | base64

# 方法 2：從雲服務提供商獲取
# AWS EKS:
aws eks update-kubeconfig --name your-cluster-name --region your-region
cat ~/.kube/config | base64

# GCP GKE:
gcloud container clusters get-credentials your-cluster-name --zone your-zone
cat ~/.kube/config | base64

# Azure AKS:
az aks get-credentials --resource-group your-rg --name your-cluster-name
cat ~/.kube/config | base64
```

#### 配置到 GitHub

1. 進入 **Settings** → **Secrets and variables** → **Actions**
2. 點擊 **New repository secret**
3. 添加：

**KUBE_CONFIG**:
- Name: `KUBE_CONFIG`
- Secret: base64 編碼的 kubeconfig 內容

---

## 驗證配置

### 檢查 Secrets 是否配置

1. 進入 repository **Settings** → **Secrets and variables** → **Actions**
2. 確認以下 secrets 存在：
   - ✅ DOCKER_HUB_USERNAME
   - ✅ DOCKER_HUB_TOKEN
   - ✅ KUBE_CONFIG

### 測試 CI/CD Pipeline

1. 推送一個小的變更到 repository
2. 檢查 **Actions** 標籤
3. 查看 workflow 運行狀態

**CI Pipeline** 應該：
- ✅ 運行測試
- ✅ 構建 Docker 鏡像
- ✅ 推送到 Docker Hub

**CD Pipeline** 應該：
- ✅ 部署到 Kubernetes 集群

---

## 安全最佳實踐

### 1. Secrets 輪換

定期更換 secrets（建議每 90 天）：
- Docker Hub Token：在 Docker Hub 中撤銷舊 token，生成新 token
- Kubeconfig：如果使用服務賬戶，定期輪換 token

### 2. 最小權限原則

**Docker Hub Token**:
- 只授予必要的權限（Read, Write）
- 不要使用個人密碼

**Kubernetes Config**:
- 使用專用的服務賬戶（不要使用管理員權限）
- 只授予部署到特定 namespace 的權限

### 3. 創建專用的 Kubernetes 服務賬戶

```bash
# 創建服務賬戶
kubectl create serviceaccount github-actions -n microservices-demo

# 創建 Role（只允許部署相關操作）
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployment-manager
  namespace: microservices-demo
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update", "patch"]
- apiGroups: [""]
  resources: ["services", "pods"]
  verbs: ["get", "list"]
EOF

# 綁定 Role 到服務賬戶
kubectl create rolebinding github-actions-binding \
  --role=deployment-manager \
  --serviceaccount=microservices-demo:github-actions \
  -n microservices-demo

# 獲取服務賬戶 token
kubectl create token github-actions -n microservices-demo --duration=8760h
```

---

## 故障排查

### 問題 1: "Error: Invalid username or password"

**原因**: Docker Hub credentials 不正確

**解決方案**:
1. 驗證 `DOCKER_HUB_USERNAME` 是否正確
2. 重新生成 `DOCKER_HUB_TOKEN`
3. 確保使用的是 access token，不是密碼

### 問題 2: "Error: Unable to connect to the server"

**原因**: Kubernetes config 不正確或已過期

**解決方案**:
1. 驗證 kubeconfig 是否有效：
   ```bash
   echo "$KUBE_CONFIG" | base64 -d > /tmp/config
   kubectl --kubeconfig=/tmp/config get nodes
   ```
2. 檢查證書是否過期
3. 重新生成並更新 `KUBE_CONFIG` secret

### 問題 3: IDE 顯示 "Context access might be invalid"

**原因**: 這是 IDE 的正常警告，因為它無法驗證 secrets 是否存在

**解決方案**:
- ✅ 這不是錯誤，可以忽略
- IDE 只是提醒您需要在 GitHub 中配置這些 secrets
- 只要在 GitHub repository settings 中正確配置了 secrets，workflow 就能正常運行

---

## 面試展示要點

當討論 CI/CD 安全時，可以強調：

1. **Secrets 管理**:
   - 使用 GitHub Secrets 安全存儲敏感信息
   - 永不在代碼中硬編碼 credentials
   - 使用 access tokens 而非密碼

2. **權限控制**:
   - Kubernetes RBAC 最小權限原則
   - 服務賬戶隔離
   - Token 輪換策略

3. **安全審計**:
   - 所有 secret 訪問都有日誌記錄
   - 定期審查 secret 使用情況
   - 過期 token 自動失效

---

## 相關文檔

- [GitHub Actions Secrets 文檔](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Docker Hub Access Tokens](https://docs.docker.com/docker-hub/access-tokens/)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [服務賬戶最佳實踐](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)
