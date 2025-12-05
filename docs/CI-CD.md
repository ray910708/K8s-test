# CI/CD Pipeline 文檔

本文檔詳細說明項目的 CI/CD pipeline 架構、工作流程和最佳實踐。

## 概覽

我們使用 GitHub Actions 實現完整的 CI/CD pipeline，包括測試、構建、安全掃描和部署。

### Pipeline 階段

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌────────────┐
│   Test      │───▶│   Security   │───▶│    Build    │───▶│    Push    │
│   Stage     │    │    Scan      │    │   Stage     │    │   Stage    │
└─────────────┘    └──────────────┘    └─────────────┘    └────────────┘
```

## 工作流程

### 1. Test Stage (測試階段)

**觸發條件**: 所有 push 和 pull request

**執行內容**:
- 運行所有服務的單元測試
- 執行代碼質量檢查 (flake8)
- 生成測試覆蓋率報告
- 上傳覆蓋率到 Codecov

**矩陣策略**:
```yaml
strategy:
  matrix:
    service: [api-gateway, worker-service, dashboard]
```

**步驟**:
1. Checkout 代碼
2. 設置 Python 3.11
3. 緩存 pip 依賴
4. 安裝依賴 (requirements.txt + requirements-test.txt)
5. Lint 檢查 (flake8)
6. 運行 pytest 測試
7. 上傳覆蓋率報告

**測試要求**:
- ✅ 所有測試必須通過
- ✅ 代碼覆蓋率 >70%
- ✅ Lint 檢查無錯誤

### 2. Security Scan Stage (安全掃描階段)

**觸發條件**: 所有 push 和 pull request（與測試並行）

**執行內容**:
- 依賴漏洞掃描 (Safety)
- 代碼安全掃描 (Bandit)
- 生成安全報告

**工具**:

#### Safety
檢查 Python 依賴包的已知漏洞

```bash
safety check --file=requirements.txt
```

#### Bandit
Python 代碼安全性靜態分析

```bash
bandit -r . -f json -o bandit-report.json
```

**輸出**:
- Bandit JSON 報告（上傳為 artifact）
- 控制台安全摘要

### 3. Build Stage (構建階段)

**觸發條件**: 測試和安全掃描通過後

**執行內容**:
- 構建 Docker 鏡像
- Docker 鏡像安全掃描 (Trivy)
- 生成掃描報告

**Docker 構建優化**:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

- 使用 GitHub Actions cache 加速構建
- Layer caching 減少構建時間
- Multi-stage builds 優化鏡像大小

**Trivy 掃描**:
- 掃描漏洞等級：CRITICAL, HIGH
- 生成 SARIF 格式報告
- 上傳到 GitHub Security
- 生成詳細表格報告

**輸出**:
- Docker 鏡像 (tagged with SHA)
- Trivy SARIF 報告
- Trivy 詳細報告（artifact）

### 4. Push Stage (推送階段)

**觸發條件**:
- 僅在 main 分支的 push 事件
- 前面所有階段成功

**執行內容**:
- 登錄 Docker Hub
- 構建並推送鏡像
- 生成多種標籤

**鏡像標籤策略**:
```yaml
tags:
  - type=ref,event=branch          # main
  - type=sha,prefix={{branch}}-    # main-abc1234
  - type=semver,pattern={{version}} # 1.2.3
  - type=raw,value=latest          # latest
```

## CI/CD 配置文件

### 主要配置文件

#### `.github/workflows/ci.yml`
主 CI/CD pipeline 配置

#### `.flake8`
Flake8 linter 配置
- Max line length: 127
- Max complexity: 10
- 排除目錄：venv, __pycache__, .git

#### `.github/labeler.yml`
自動 PR 標籤配置

#### `.github/pull_request_template.md`
PR 模板，確保一致的 PR 質量

#### `.github/ISSUE_TEMPLATE/`
Issue 模板（bug report, feature request）

## 使用的 GitHub Actions

### 核心 Actions

| Action | 用途 | 版本 |
|--------|------|------|
| `actions/checkout@v4` | 檢出代碼 | v4 |
| `actions/setup-python@v4` | 設置 Python | v4 |
| `actions/cache@v3` | 緩存依賴 | v3 |
| `docker/setup-buildx-action@v3` | 設置 Docker Buildx | v3 |
| `docker/login-action@v3` | Docker Hub 登錄 | v3 |
| `docker/build-push-action@v5` | 構建/推送鏡像 | v5 |
| `docker/metadata-action@v5` | 生成鏡像元數據 | v5 |
| `aquasecurity/trivy-action@master` | 安全掃描 | master |
| `codecov/codecov-action@v3` | 上傳覆蓋率 | v3 |
| `github/codeql-action/upload-sarif@v2` | 上傳安全報告 | v2 |
| `actions/labeler@v4` | 自動標籤 | v4 |

## Secrets 配置

### 必需的 Secrets

在 GitHub Repository Settings → Secrets 中配置：

1. **DOCKER_HUB_USERNAME**
   - Docker Hub 用戶名
   - 用於推送鏡像

2. **DOCKER_HUB_TOKEN**
   - Docker Hub 訪問令牌
   - 在 Docker Hub → Account Settings → Security 生成

3. **KUBE_CONFIG** (可選)
   - Kubernetes 集群配置
   - 用於自動部署

詳細配置見 [SECRETS-SETUP.md](SECRETS-SETUP.md)

## 本地測試 CI

### 運行測試

```bash
# 單個服務
cd services/api-gateway
bash run_tests.sh

# 所有服務
./scripts/run_all_tests.sh
```

### Lint 檢查

```bash
flake8 services/api-gateway
```

### 安全掃描

```bash
# Bandit
bandit -r services/api-gateway

# Safety
safety check --file services/api-gateway/requirements.txt
```

### Docker 構建

```bash
cd services/api-gateway
docker build -t api-gateway:test .
```

### Trivy 掃描

```bash
trivy image api-gateway:test
```

## CI/CD 優化

### 1. 緩存策略

**Pip 依賴緩存**:
```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
```

**Docker Layer 緩存**:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

### 2. 矩陣構建

並行執行多個服務的測試和構建：
```yaml
strategy:
  matrix:
    service: [api-gateway, worker-service, dashboard]
```

### 3. 條件執行

僅在 main 分支推送鏡像：
```yaml
if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

## 故障排查

### 常見問題

#### 1. 測試失敗

**問題**: pytest 找不到模組
```bash
ModuleNotFoundError: No module named 'app'
```

**解決方案**:
```bash
# 確保 PYTHONPATH 設置正確
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

#### 2. Docker 構建失敗

**問題**: 緩存問題導致構建失敗

**解決方案**:
```bash
# 清除緩存重新構建
docker build --no-cache -t service:tag .
```

#### 3. Secrets 未配置

**問題**: `DOCKER_HUB_USERNAME` 未定義

**解決方案**:
- 在 GitHub Repository Settings → Secrets → Actions 中添加 Secret
- 檢查 Secret 名稱拼寫

#### 4. 覆蓋率不足

**問題**: 測試覆蓋率 <70%

**解決方案**:
```bash
# 查看未覆蓋的代碼
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## 監控與報告

### GitHub Actions UI

- **Actions 標籤**: 查看所有工作流運行
- **Checks**: PR 中查看檢查狀態
- **Security**: 查看 Trivy 掃描結果

### Codecov

- 訪問 https://codecov.io/gh/OWNER/K8s-test
- 查看覆蓋率趨勢
- PR 中自動評論覆蓋率變化

### Artifacts

以下內容作為 artifacts 保存 90 天：
- Bandit 安全報告
- Trivy 掃描報告
- 測試覆蓋率報告

## 最佳實踐

### 1. Commit 規範

使用 Conventional Commits：
```
feat(api-gateway): add rate limiting
fix(worker): resolve thread safety issue
docs: update CI/CD documentation
```

### 2. PR 流程

1. 創建 feature branch
2. 提交代碼並推送
3. 創建 PR（使用模板）
4. 等待 CI 檢查通過
5. 請求 code review
6. 合併到 main

### 3. 版本管理

- 使用 semantic versioning (v1.2.3)
- Tag releases in main branch
- 更新 CHANGELOG.md

### 4. 安全實踐

- 定期更新依賴
- 審查 Bandit 和 Trivy 報告
- 不在代碼中硬編碼密鑰
- 使用 Secrets 管理敏感信息

## 性能指標

### CI Pipeline 執行時間

| Stage | 平均時間 | 並行 |
|-------|---------|------|
| Test | ~2-3 分鐘 | ✅ |
| Security Scan | ~1-2 分鐘 | ✅ |
| Build | ~3-5 分鐘 | ✅ |
| Push | ~2-3 分鐘 | ❌ |
| **總計** | **~8-13 分鐘** | |

### 優化建議

- ✅ 使用緩存減少依賴安裝時間
- ✅ 並行運行多個服務的任務
- ✅ Docker layer caching
- ⏳ 考慮使用 self-hosted runners (更快的網絡)

## 面試展示要點

在面試中討論 CI/CD 時，可以強調：

1. **完整的 Pipeline**: 測試 → 安全掃描 → 構建 → 推送
2. **安全第一**: Trivy, Bandit, Safety 多層掃描
3. **自動化**: PR 自動標籤、測試、部署
4. **質量保證**: >70% 測試覆蓋率，Lint 檢查
5. **效能優化**: 緩存策略，並行執行
6. **可觀測性**: Codecov 集成，詳細報告
7. **最佳實踐**: PR 模板，Issue 模板，CONTRIBUTING 指南

## 相關資源

- [GitHub Actions 文檔](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Trivy 文檔](https://aquasecurity.github.io/trivy/)
- [Codecov 文檔](https://docs.codecov.com/)
