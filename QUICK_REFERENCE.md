# 🚀 Quick Reference - Security Fixes

One-page reference for the security enhancements.

---

## 📦 Installation (1 minute)

```bash
pip install -r requirements_security.txt
python setup_security.py
nano config/secrets.env  # Add your Zerodha API credentials
python run_dashboard.py
```

---

## 🔑 Generate Secrets

```bash
# Flask Secret (64 chars)
python -c "import secrets; print(secrets.token_hex(32))"

# Encryption Key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 📝 config/secrets.env Template

```env
KITE_API_KEY=your_zerodha_api_key
KITE_API_SECRET=your_zerodha_api_secret
FLASK_SECRET_KEY=<generated_64_char_hex>
ENCRYPTION_KEY=<generated_fernet_key>
```

---

## 🌐 Frontend - CSRF Token Usage

```javascript
// Get CSRF token
const csrf = document.querySelector('meta[name="csrf-token"]').content;

// Use in fetch
fetch('/api/start', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
    },
    body: JSON.stringify({mode: 'paper'})
})
```

---

## 🐍 Backend - Config Loading

```python
from src.utils.config_loader import get_config

# Load config (singleton)
config = get_config()

# Access values
api_key = config.get('broker.api_key')
trading_mode = config.get('trading.mode', 'paper')
```

---

## 🔐 Token Encryption

```python
from src.utils.encryption import SecureTokenStorage

# Initialize
storage = SecureTokenStorage()

# Save encrypted token
storage.save_token("my_access_token", Path("config/.access_token"))

# Load decrypted token
token = storage.load_token(Path("config/.access_token"))
```

---

## 🚦 Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/api/start` | 5/minute |
| `/api/emergency-stop` | 10/minute |
| All others | 50/hour, 200/day |

---

## 📊 File Changes Summary

### New Files
- `src/utils/encryption.py` - Token encryption
- `src/dashboard/static/js/csrf.js` - CSRF helpers
- `setup_security.py` - Automated setup
- `requirements_security.txt` - Dependencies
- `SECURITY_FIXES_IMPLEMENTED.md` - Technical docs
- `SETUP_GUIDE.md` - Setup instructions

### Modified Files
- `src/auth/zerodha_auth.py` - Encrypted token storage
- `src/utils/config_loader.py` - Env var substitution
- `src/dashboard/app.py` - CSRF + rate limiting
- `config/config.yaml` - Use ${VAR} syntax
- `src/dashboard/templates/dashboard.html` - CSRF meta tag

---

## ✅ Pre-Flight Checklist

```bash
# 1. Secrets configured?
grep KITE_API_KEY config/secrets.env

# 2. Encryption enabled?
grep ENCRYPTION_KEY config/secrets.env

# 3. Gitignore safe?
grep secrets.env .gitignore

# 4. Dependencies installed?
python -c "import flask_wtf, flask_limiter, cryptography; print('OK')"

# 5. Config loads?
python src/utils/config_loader.py
```

---

## 🐛 Quick Fixes

### "CSRF validation failed"
```bash
# Clear cookies, get new token
curl http://localhost:8050/api/csrf-token
```

### "ENCRYPTION_KEY not set"
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add output to config/secrets.env
```

### "Config file not found"
```bash
ls config/config.yaml  # Verify exists
pwd  # Ensure you're in project root
```

---

## 🔒 Security Scorecard

| Item | Status |
|------|--------|
| Token Encryption | ✅ FIXED |
| CSRF Protection | ✅ FIXED |
| Rate Limiting | ✅ FIXED |
| Audit Logging | ✅ FIXED |
| Env Variables | ✅ FIXED |
| Input Validation | ✅ IMPROVED |
| XSS Prevention | ❌ TODO |
| Test Coverage | ❌ TODO (0%) |

**Overall:** C+ (was D+)

---

## 📞 Help

- **Setup:** `SETUP_GUIDE.md`
- **Details:** `SECURITY_FIXES_IMPLEMENTED.md`
- **Summary:** `FIXES_SUMMARY.md`
- **Project:** `CLAUDE.md`

---

**⚡ Quick Start Command:**
```bash
python setup_security.py && python run_dashboard.py
```

---

*Last Updated: October 24, 2025*
