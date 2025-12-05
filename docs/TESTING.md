# 測試文檔

這份文檔說明了項目的測試策略、測試結構和如何運行測試。

## 測試策略

### 測試金字塔

我們遵循測試金字塔原則：

1. **單元測試 (Unit Tests)** - 70%
   - 測試個別函數和類
   - 快速執行，隔離依賴
   - 使用 Mock 和 Fake 對象

2. **集成測試 (Integration Tests)** - 20%
   - 測試多個組件的交互
   - 測試與外部服務的集成（Redis）

3. **端到端測試 (E2E Tests)** - 10%
   - 測試完整的用戶場景
   - 通過 CI/CD pipeline 運行

### 測試覆蓋率目標

- **API Gateway**: >70% (核心服務，完整測試)
- **Worker Service**: >49% (後台服務，基礎測試)
- **Dashboard**: 選擇性測試 (UI 服務)
- **目標覆蓋率**: 整體 >70%
- **核心模組**: >90%

**注意**: 不同服務的測試覆蓋率目標根據其重要性和複雜度而定。API Gateway 作為對外接口需要最高覆蓋率。Worker Service 當前實現了 49.34% 覆蓋率，主要測試健康檢查和基礎功能。

## 測試結構

```
services/
├── api-gateway/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py              # Pytest fixtures
│   │   ├── test_health.py           # 健康檢查測試
│   │   ├── test_api_endpoints.py    # API 端點測試
│   │   ├── test_redis_client.py     # Redis 客戶端測試
│   │   ├── test_request_context.py  # 請求追蹤測試
│   │   └── test_rate_limiting.py    # 速率限制測試
│   ├── pytest.ini                   # Pytest 配置
│   ├── requirements-test.txt        # 測試依賴
│   └── run_tests.sh                 # 測試執行腳本
│
├── worker-service/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_worker.py           # Worker 服務測試
│   ├── pytest.ini
│   ├── requirements-test.txt
│   └── run_tests.sh
│
└── dashboard/
    └── tests/
        └── (similar structure)
```

## 運行測試

### API Gateway 測試

```bash
cd services/api-gateway

# 安裝測試依賴
pip install -r requirements-test.txt

# 運行所有測試
pytest

# 運行特定測試文件
pytest tests/test_health.py

# 運行特定測試類
pytest tests/test_health.py::TestLivenessProbe

# 運行特定測試函數
pytest tests/test_health.py::TestLivenessProbe::test_liveness_returns_200

# 使用腳本運行（包含覆蓋率）
bash run_tests.sh
```

### Worker Service 測試

```bash
cd services/worker-service
bash run_tests.sh
```

### Dashboard 測試

```bash
cd services/dashboard
bash run_tests.sh
```

### 運行所有測試

```bash
# 從項目根目錄
cd K8s-test
./scripts/run_all_tests.sh
```

## 測試標記 (Markers)

我們使用 pytest markers 來組織測試：

```bash
# 只運行單元測試
pytest -m unit

# 只運行集成測試
pytest -m integration

# 跳過慢速測試
pytest -m "not slow"

# 只運行需要 Redis 的測試
pytest -m redis
```

### 可用的 Markers

- `unit`: 單元測試
- `integration`: 集成測試
- `slow`: 慢速測試（>1秒）
- `redis`: 需要 Redis 連接的測試

## 測試覆蓋率

### 查看覆蓋率報告

```bash
# 生成 HTML 報告
pytest --cov=. --cov-report=html

# 查看報告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 覆蓋率配置

覆蓋率配置在 `pytest.ini` 中：

```ini
[coverage:run]
source = .
omit =
    tests/*
    venv/*
    */site-packages/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    if __name__ == .__main__.:
```

## Fixtures

### 共享 Fixtures (conftest.py)

```python
@pytest.fixture
def fake_redis_client():
    """提供假的 Redis 客戶端用於測試"""
    return fakeredis.FakeRedis(decode_responses=True)

@pytest.fixture
def app():
    """創建測試用的 Flask 應用"""
    # 返回配置好的測試應用

@pytest.fixture
def client(app):
    """創建 Flask 測試客戶端"""
    return app.test_client()
```

### 使用 Fixtures

```python
def test_example(client, mock_redis_client):
    """測試示例"""
    response = client.get('/api/status')
    assert response.status_code == 200
```

## Mock 策略

### Mock Redis

```python
@pytest.fixture
def mock_redis_client(fake_redis_client):
    """Mock RedisClient"""
    client = RedisClient(host='localhost', port=6379)
    client._client = fake_redis_client
    return client
```

### Mock 外部服務

```python
@patch('requests.get')
def test_external_api(mock_get, client):
    """測試外部 API 調用"""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'data': 'test'}

    response = client.get('/api/external')
    assert response.status_code == 200
```

## 測試最佳實踐

### 1. 測試命名

```python
# Good
def test_get_returns_value_when_key_exists():
    pass

# Bad
def test1():
    pass
```

### 2. Arrange-Act-Assert 模式

```python
def test_redis_set_stores_value(fake_redis_client):
    # Arrange
    key = 'test_key'
    value = 'test_value'

    # Act
    result = fake_redis_client.set(key, value)

    # Assert
    assert result is True
    assert fake_redis_client.get(key) == value
```

### 3. 測試獨立性

```python
# 每個測試應該獨立，不依賴其他測試
def test_a(client):
    # 測試 A
    pass

def test_b(client):
    # 測試 B（不依賴測試 A）
    pass
```

### 4. 使用參數化測試

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", 5),
    ("world", 5),
    ("", 0),
])
def test_string_length(input, expected):
    assert len(input) == expected
```

## CI/CD 集成

測試在 CI/CD pipeline 中自動運行：

```yaml
# .github/workflows/ci.yml
- name: Run tests
  run: |
    cd services/${{ matrix.service }}
    pip install -r requirements-test.txt
    pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## 故障排查

### 問題 1: Import 錯誤

```bash
# 確保測試目錄在 Python path 中
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### 問題 2: Redis 連接錯誤

```bash
# 使用 fakeredis 而不是真實 Redis
pip install fakeredis
```

### 問題 3: 覆蓋率不足

```bash
# 查看未覆蓋的行
pytest --cov=. --cov-report=term-missing
```

## 面試展示要點

在面試中討論測試策略時，可以強調：

1. **測試金字塔**: 70% 單元測試，20% 集成測試，10% E2E
2. **高覆蓋率**: >70% 的代碼覆蓋率
3. **Mock 策略**: 使用 fakeredis 和 unittest.mock 隔離依賴
4. **CI/CD 集成**: 自動化測試在每次提交時運行
5. **測試標記**: 使用 pytest markers 組織和過濾測試
6. **測試獨立性**: 每個測試都是獨立的，可以單獨運行

## 相關資源

- [Pytest 文檔](https://docs.pytest.org/)
- [Coverage.py 文檔](https://coverage.readthedocs.io/)
- [FakeRedis 文檔](https://github.com/cunla/fakeredis-py)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
