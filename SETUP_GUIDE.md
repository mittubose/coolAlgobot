# 🚀 Scalping Bot - Secure Setup Guide

Complete guide to setting up the bot with all security enhancements.

---

## 📋 Prerequisites

- Python 3.8+ installed
- Zerodha Kite Connect account
- API Key and Secret from Zerodha

---

## 🔧 Step 1: Install Dependencies

### Option A: Install All Dependencies
```bash
cd scalping-bot
pip install -r requirements.txt
pip install -r requirements_security.txt
```

### Option B: Install Security Dependencies Only
```bash
pip install Flask-WTF Flask-Limiter cryptography python-dotenv
```

**Verify Installation:**
```bash
python -c "import flask_wtf, flask_limiter, cryptography, dotenv; print('✅ All dependencies installed')"
```

---

## 🔐 Step 2: Generate Security Secrets

### Automated Setup (Recommended)
```bash
python setup_security.py
```

This script will:
1. Generate Flask secret key
2. Generate encryption key
3. Create `config/secrets.env` file
4. Set secure file permissions
5. Verify dependencies
6. Check .gitignore configuration

### Manual Setup
If you prefer manual setup:

**1. Generate Flask Secret Key:**
```bash
python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
```

**2. Generate Encryption Key:**
```bash
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

**3. Create config/secrets.env:**
```bash
cp config/secrets.env.example config/secrets.env
```

**4. Edit config/secrets.env:**
```bash
nano config/secrets.env
```

Add the generated keys and your Zerodha credentials.

---

## 📝 Step 3: Configure Zerodha API

1. **Get API Credentials:**
   - Visit: https://kite.trade/docs/connect/v3/
   - Create a new app
   - Copy API Key and API Secret

2. **Add to config/secrets.env:**
```env
KITE_API_KEY=your_actual_api_key_here
KITE_API_SECRET=your_actual_api_secret_here
```

3. **Verify Configuration:**
```bash
python -c "from src.utils.config_loader import get_config; c=get_config(); print('✅ Config loaded')"
```

---

## 🧪 Step 4: Test Security Features

### Test 1: Token Encryption
```bash
python src/utils/encryption.py generate-key
```

Expected output:
```
Generated encryption key:
<base64_encoded_key>

Add this to config/secrets.env:
ENCRYPTION_KEY=<base64_encoded_key>
```

### Test 2: Config Loader
```bash
python src/utils/config_loader.py
```

Expected output:
```
✅ Configuration loaded successfully!
Trading mode: paper
Max positions: 3
Risk per trade: 1.0%
```

### Test 3: CSRF Protection
```bash
# Start the dashboard
python run_dashboard.py

# In another terminal, test CSRF endpoint
curl http://localhost:8050/api/csrf-token
```

Expected output:
```json
{
  "csrf_token": "ImExY2YzNjI3ZjU4MDI0MDU3ODg0ZjY0MzMwNjI2NzYxZjA3NDEwMGMi..."
}
```

---

## 🎯 Step 5: Run the Dashboard

### Development Mode
```bash
python run_dashboard.py
```

The dashboard will be available at: http://localhost:8050

### Production Mode
For production deployment:

1. **Update Security Settings** in `src/dashboard/app.py`:
```python
# Line 35: Enable HTTPS-only cookies
app.config['SESSION_COOKIE_SECURE'] = True

# Line 33: Strict SSL for CSRF
app.config['WTF_CSRF_SSL_STRICT'] = True

# Line 42-47: Restrict CORS origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],  # Your actual domain
        "supports_credentials": True
    }
})
```

2. **Use Redis for Rate Limiting:**
```python
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"  # Install Redis first
)
```

3. **Run with Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8050 src.dashboard.app:app
```

---

## 🔒 Security Checklist

Before going to production, verify:

- [ ] `config/secrets.env` exists and is properly filled
- [ ] `ENCRYPTION_KEY` is set (not empty)
- [ ] `FLASK_SECRET_KEY` is set (not empty)
- [ ] `.gitignore` includes `config/secrets.env`
- [ ] `.gitignore` includes `.access_token`
- [ ] `config/secrets.env` has 600 permissions (`chmod 600 config/secrets.env`)
- [ ] No secrets hardcoded in `config/config.yaml`
- [ ] All API endpoints return CSRF errors without valid token
- [ ] Rate limiting is active (test with repeated requests)
- [ ] Audit logs are working (check logs/ directory)
- [ ] HTTPS is enabled for production
- [ ] CORS origins are restricted to your domain

**Verify Checklist:**
```bash
# Check .gitignore
grep -E "(secrets\.env|\.access_token)" .gitignore

# Check file permissions
ls -la config/secrets.env  # Should show -rw-------

# Check for hardcoded secrets
grep -r "YOUR_API_KEY_HERE" config/  # Should find none in secrets.env

# Test CSRF protection
curl -X POST http://localhost:8050/api/start  # Should return 400 CSRF error
```

---

## 🧪 Testing the Bot

### 1. Test Authentication
```bash
# Start dashboard
python run_dashboard.py

# Navigate to http://localhost:8050
# Try starting the bot in PAPER mode
```

### 2. Test CSRF Protection
```javascript
// In browser console
fetch('/api/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({mode: 'paper'})
})
// Should fail with CSRF error

// Now with CSRF token
const token = document.querySelector('meta[name="csrf-token"]').content;
fetch('/api/start', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': token
    },
    body: JSON.stringify({mode: 'paper'})
})
// Should succeed
```

### 3. Test Rate Limiting
```bash
# Run this 10 times quickly
for i in {1..10}; do
  curl -X POST http://localhost:8050/api/emergency-stop \
    -H "X-CSRFToken: $(curl -s http://localhost:8050/api/csrf-token | jq -r .csrf_token)"
done
# Should start returning 429 Too Many Requests after 10 attempts
```

---

## 🐛 Troubleshooting

### Issue: "ENCRYPTION_KEY not set. Cannot encrypt tokens."
**Solution:**
```bash
# Generate new key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to config/secrets.env
echo "ENCRYPTION_KEY=<generated_key>" >> config/secrets.env
```

### Issue: "CSRF validation failed"
**Solution:**
1. Check that meta tag exists in HTML:
   ```bash
   curl http://localhost:8050 | grep csrf-token
   ```
2. Verify Flask secret key is set:
   ```bash
   grep FLASK_SECRET_KEY config/secrets.env
   ```
3. Clear browser cookies and try again

### Issue: "Configuration file not found"
**Solution:**
```bash
# Verify config.yaml exists
ls config/config.yaml

# Verify you're running from project root
pwd  # Should end in /scalping-bot
```

### Issue: "ModuleNotFoundError: No module named 'flask_wtf'"
**Solution:**
```bash
pip install -r requirements_security.txt
```

### Issue: Rate limiting not working
**Solution:**
Check that Flask-Limiter is installed:
```bash
python -c "import flask_limiter; print('✅ Installed')"
```

---

## 📚 Additional Resources

- **Zerodha API Docs:** https://kite.trade/docs/connect/v3/
- **Flask-WTF CSRF:** https://flask-wtf.readthedocs.io/en/stable/csrf.html
- **Flask-Limiter:** https://flask-limiter.readthedocs.io/
- **Cryptography (Fernet):** https://cryptography.io/en/latest/fernet/

---

## 🎉 Next Steps

After setup is complete:

1. **Read SECURITY_FIXES_IMPLEMENTED.md** for details on what was fixed
2. **Test in Paper Trading Mode** for at least 2 weeks
3. **Review CLAUDE.md** for project guidelines
4. **Check IMPLEMENTATION_PROGRESS.md** for roadmap

---

## ⚠️ Important Warnings

### 🚫 NEVER:
- Commit `config/secrets.env` to Git
- Share your API keys publicly
- Run LIVE trading without thorough testing
- Disable CSRF protection
- Store secrets in code

### ✅ ALWAYS:
- Start with PAPER trading mode
- Test all features before live deployment
- Monitor logs for errors
- Keep secrets in `config/secrets.env`
- Use strong passwords for dashboard authentication

---

**🔐 Setup Complete! Your bot is now secured against major vulnerabilities.**

**Next:** Test in paper mode → Review security logs → Monitor performance → (After 2 weeks) Consider live trading

---

*Last Updated: October 24, 2025*
*For support: Check GitHub Issues or CLAUDE.md*
