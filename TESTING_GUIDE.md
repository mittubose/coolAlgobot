# 🧪 Testing Guide - Scalping Bot

Comprehensive guide for running tests and ensuring code quality.

---

## 📋 Prerequisites

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Verify installation
pytest --version
```

---

## 🚀 Quick Start

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_encryption.py

# Run specific test function
pytest tests/unit/test_encryption.py::TestSecureTokenStorage::test_encrypt_token_success
```

---

## 📁 Test Structure

```
tests/
├── __init__.py
├── unit/                       # Unit tests (fast, isolated)
│   ├── test_encryption.py     # Token encryption tests
│   ├── test_config_loader.py  # Configuration tests
│   └── ...
├── integration/                # Integration tests (slower, combined)
│   ├── test_api_endpoints.py
│   └── ...
└── security/                   # Security tests (vulnerabilities)
    ├── test_csrf_protection.py
    ├── test_rate_limiting.py
    └── ...
```

---

## 🏷️ Test Markers

Tests are organized with markers for selective running:

```bash
# Run only unit tests
pytest -m unit

# Run only security tests
pytest -m security

# Run only integration tests
pytest -m integration

# Run tests that don't require API
pytest -m "not requires_api"

# Skip slow tests
pytest -m "not slow"
```

**Available Markers:**
- `unit` - Fast, isolated unit tests
- `integration` - Combined component tests
- `security` - Security vulnerability tests
- `slow` - Tests that take >1 second
- `requires_api` - Tests requiring Zerodha API credentials

---

## 📊 Coverage Reports

### Generate HTML Coverage Report

```bash
pytest --cov=src --cov-report=html

# Open report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Requirements

| Component | Target | Priority |
|-----------|--------|----------|
| Trading logic | 90%+ | CRITICAL |
| Security (encryption, CSRF) | 95%+ | CRITICAL |
| Configuration | 80%+ | HIGH |
| API endpoints | 80%+ | HIGH |
| Utilities | 70%+ | MEDIUM |
| UI/Dashboard | 60%+ | MEDIUM |

**Current Coverage:** Run `pytest --cov` to see

---

## 🧪 Test Examples

### Unit Test Example

```python
# tests/unit/test_encryption.py
def test_encrypt_token_success(storage):
    """Test successful token encryption"""
    token = "test_access_token"
    encrypted = storage.encrypt_token(token)

    assert isinstance(encrypted, bytes)
    assert encrypted != token.encode()
```

### Security Test Example

```python
# tests/security/test_csrf_protection.py
def test_post_without_csrf_fails(client):
    """Test that POST without CSRF token fails"""
    response = client.post('/api/start', json={'mode': 'paper'})
    assert response.status_code == 400
```

### Integration Test Example

```python
# tests/integration/test_authentication_flow.py
def test_complete_auth_flow(client):
    """Test complete authentication flow"""
    # 1. Get login URL
    # 2. Mock OAuth callback
    # 3. Verify token saved encrypted
    # 4. Verify session created
```

---

## 🔍 Running Specific Tests

### By File
```bash
pytest tests/unit/test_encryption.py -v
```

### By Class
```bash
pytest tests/unit/test_encryption.py::TestSecureTokenStorage -v
```

### By Function
```bash
pytest tests/unit/test_encryption.py::TestSecureTokenStorage::test_encrypt_token_success -v
```

### By Pattern
```bash
# Run all tests with "csrf" in name
pytest -k csrf -v

# Run all tests with "token" in name
pytest -k token -v
```

---

## 🐛 Debugging Tests

### Show Print Statements
```bash
pytest -s  # or --capture=no
```

### Show Local Variables on Failure
```bash
pytest -l  # or --showlocals
```

### Drop into Debugger on Failure
```bash
pytest --pdb
```

### Verbose Output
```bash
pytest -vv  # Extra verbose
```

---

## ⚡ Performance Tips

### Run Tests in Parallel
```bash
pip install pytest-xdist
pytest -n auto  # Use all CPU cores
```

### Run Only Failed Tests
```bash
# First run
pytest --lf  # --last-failed
```

### Stop on First Failure
```bash
pytest -x  # or --exitfirst
```

---

## 📝 Writing New Tests

### Test Naming Convention

- **Files:** `test_<module_name>.py`
- **Classes:** `Test<ClassName>`
- **Functions:** `test_<what_it_tests>`

### Example Test Template

```python
"""
Unit Tests for Module Name
Brief description of what this tests
"""

import pytest

class TestYourComponent:
    """Test cases for YourComponent"""

    @pytest.fixture
    def component(self):
        """Create component instance for testing"""
        return YourComponent()

    def test_feature_success(self, component):
        """Test successful feature execution"""
        result = component.do_something()
        assert result == expected_value

    def test_feature_failure(self, component):
        """Test feature handles errors correctly"""
        with pytest.raises(ExpectedError):
            component.do_invalid_thing()
```

---

## 🔒 Security Testing Checklist

Before deploying, ensure these tests pass:

- [ ] **CSRF Protection**
  - [ ] All POST/PUT/DELETE endpoints require CSRF token
  - [ ] Invalid tokens are rejected
  - [ ] GET requests work without token

- [ ] **Token Encryption**
  - [ ] Tokens encrypted before saving
  - [ ] Encrypted tokens can be decrypted
  - [ ] Wrong key fails decryption

- [ ] **Rate Limiting**
  - [ ] Endpoints respect rate limits
  - [ ] Limit exceeded returns 429
  - [ ] Rate resets correctly

- [ ] **Input Validation**
  - [ ] Invalid trading mode rejected
  - [ ] Negative quantities rejected
  - [ ] SQL injection prevented

- [ ] **Session Security**
  - [ ] Cookies are HttpOnly
  - [ ] SameSite attribute set
  - [ ] Secret key is strong

---

## 🎯 CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements_test.txt
      - name: Run tests
        run: |
          pytest --cov --cov-fail-under=70
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📊 Test Reports

### JUnit XML (for CI)
```bash
pytest --junitxml=test-results.xml
```

### JSON Report
```bash
pip install pytest-json-report
pytest --json-report --json-report-file=report.json
```

---

## 🚨 Common Issues

### Issue: "ModuleNotFoundError"
```bash
# Solution: Install test dependencies
pip install -r requirements_test.txt
```

### Issue: "CSRF token not found"
```bash
# Solution: Ensure Flask secret key is set
export FLASK_SECRET_KEY="test_secret_key_for_testing"
```

### Issue: Tests timeout
```bash
# Solution: Increase timeout
pytest --timeout=60
```

---

## 📚 Additional Resources

- **Pytest Docs:** https://docs.pytest.org/
- **Coverage.py:** https://coverage.readthedocs.io/
- **Flask Testing:** https://flask.palletsprojects.com/en/latest/testing/

---

## ✅ Pre-Deployment Checklist

Run these commands before deploying:

```bash
# 1. Run all tests
pytest

# 2. Check coverage (must be ≥70%)
pytest --cov --cov-fail-under=70

# 3. Run security tests
pytest -m security

# 4. Check for no warnings
pytest --strict-warnings

# 5. Lint code
flake8 src/
black --check src/
```

**All tests MUST pass before deployment!**

---

*Last Updated: October 24, 2025*
*Coverage Target: 70%+ (Critical: 90%+)*
