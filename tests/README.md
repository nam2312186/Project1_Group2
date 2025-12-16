# 🧪 Test Suite Documentation

## 📋 Tổng quan

Test suite này bao gồm **50 test cases** phủ toàn bộ dự án Spotify Analytics, từ data collection đến dashboard và chatbot.

## 🗂️ Cấu trúc Test Cases

### 1. **test_data_collection.py** (Test cases 2-6)
Kiểm thử module thu thập dữ liệu:
- ✅ TC2: Spotify track search
- ✅ TC3: Audio features extraction
- ✅ TC4: Data enrichment pipeline
- ✅ TC5: Missing data handling
- ✅ TC6: Output file creation

### 2. **test_data_analysis.py** (Test cases 7-19)
Kiểm thử các bước phân tích và xử lý dữ liệu:

**Data Analysis (Step 1):**
- ✅ TC7: Schema validation
- ✅ TC8: Data types validation
- ✅ TC9: Summary statistics

**Data Cleaning (Step 2):**
- ✅ TC10: Remove duplicates
- ✅ TC11: Handle missing values
- ✅ TC12: Outlier detection
- ✅ TC13: Data normalization

**Feature Engineering (Step 3):**
- ✅ TC14: Create derived features
- ✅ TC15: Categorical encoding
- ✅ TC16: Temporal features

**Advanced Analysis (Step 4):**
- ✅ TC17: Correlation analysis
- ✅ TC18: Trend analysis
- ✅ TC19: Aggregation functions

### 3. **test_streamlit_app.py** (Test cases 21-30)
Kiểm thử Streamlit dashboard và chatbot:

**Dashboard:**
- ✅ TC21: MongoDB connection
- ✅ TC22: Data loading from DB
- ✅ TC23: Country filtering
- ✅ TC24: Visualization data prep

**Chatbot Agent:**
- ✅ TC27: MongoDB toolkit integration
- ✅ TC28: Conversation memory
- ✅ TC29: Error handling
- ✅ TC30: Response formatting

### 4. **test_mongodb_integration.py** (Test cases 31-42)
Kiểm thử MongoDB operations:
- ✅ TC31: Connection string
- ✅ TC32: Database creation
- ✅ TC33: Collection creation
- ✅ TC34: Insert single document
- ✅ TC35: Insert multiple documents
- ✅ TC36: Query documents
- ✅ TC37: Update document
- ✅ TC38: Delete document
- ✅ TC39: Aggregation pipeline
- ✅ TC40: Index creation
- ✅ TC41: Data validation
- ✅ TC42: CSV to MongoDB import

### 5. **test_integration.py** (Test cases 43-50)
Kiểm thử integration và performance:

**End-to-End:**
- ✅ TC43: Complete data pipeline
- ✅ TC44: App ↔ Database integration
- ✅ TC45: Chatbot ↔ Database query
- ✅ TC46: Data consistency
- ✅ TC47: Error propagation

**Performance:**
- ✅ TC48: Large dataset processing
- ✅ TC49: Query performance
- ✅ TC50: Concurrent requests

## 🚀 Cách chạy tests

### Cài đặt dependencies:
```bash
pip install -r tests/requirements-test.txt
```

### Chạy tất cả tests:
```bash
pytest tests/
```

### Chạy tests với coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

### Chạy specific test file:
```bash
pytest tests/test_data_collection.py
```

### Chạy specific test case:
```bash
pytest tests/test_data_collection.py::TestDataCollection::test_spotify_search_track
```

### Chạy tests theo marker:
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## 📊 Coverage Report

Sau khi chạy tests với coverage, xem report tại:
```
htmlcov/index.html
```

## 🏷️ Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.mongodb` - Tests cần MongoDB
- `@pytest.mark.api` - Tests cần external APIs

## 📝 Viết thêm test cases mới

Template cho test case mới:

```python
def test_new_feature(self, fixture_name):
    """
    Test case X: Mô tả test case
    Expected: Kết quả mong đợi
    """
    # Arrange
    data = fixture_name
    
    # Act
    result = function_to_test(data)
    
    # Assert
    assert result == expected_value
```

## 🐛 Debugging Tests

Chạy test với verbose output:
```bash
pytest -vv tests/test_file.py
```

Chạy test và dừng ở test đầu tiên fail:
```bash
pytest -x tests/
```

Chạy test với pdb debugger:
```bash
pytest --pdb tests/
```

## ✅ Best Practices

1. **Tên test rõ ràng**: `test_function_name_expected_behavior`
2. **Arrange-Act-Assert**: Tổ chức code theo 3 phần
3. **Independent tests**: Mỗi test độc lập, không phụ thuộc lẫn nhau
4. **Use fixtures**: Tái sử dụng setup code với fixtures
5. **Mock external dependencies**: Dùng mock cho APIs, databases
6. **Test edge cases**: Test cả cases bình thường và bất thường

## 📈 Continuous Integration

Tích hợp với CI/CD pipeline:

```yaml
# .github/workflows/tests.yml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r tests/requirements-test.txt
          pytest tests/ --cov=.
```

## 🔧 Troubleshooting

**Lỗi import modules:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Lỗi MongoDB connection:**
- Kiểm tra MongoDB đang chạy
- Hoặc dùng mock trong tests

**Lỗi API rate limit:**
- Dùng mock cho external APIs
- Thêm retry logic

## 📞 Liên hệ

Có câu hỏi về tests? Liên hệ team QA.
