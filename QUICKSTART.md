# K2Think API - Quick Start Guide

## 🚀 One-Command Deployment

Deploy the K2Think API proxy in seconds:

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

This will:
1. ✅ Clone the repository
2. ✅ Set up Python virtual environment
3. ✅ Install all dependencies
4. ✅ Start the server on http://localhost:7000
5. ✅ Run a test request to verify everything works

---

## 📋 What Gets Configured

After running the deployment script, you'll have:

- **Server URL**: `http://localhost:7000`
- **API Key**: Generated automatically (stored in `.env` file)
- **Token Auto-Update**: Disabled by default (no K2 credentials needed to start)
- **Test Script**: Ready to use (`send_request.sh`)

---

## 🧪 Testing the API

### Option 1: Use the provided test script

```bash
cd k2think2api3
./send_request.sh
```

### Option 2: Use Python directly

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7000/v1",
    api_key="dummy"  # Any value works if VALID_API_KEY check is disabled
)

response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "What is your model name?"}]
)

print(response)
```

### Option 3: Use curl

```bash
curl -X POST http://localhost:7000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "MBZUAI-IFM/K2-Think",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🔧 Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# 1. Clone the repository
git clone https://github.com/Zeeeepa/k2think2api3.git
cd k2think2api3

# 2. Run setup
./setup.sh

# 3. Start the server
./deploy.sh

# 4. Test the API
./send_request.sh
```

---

## 💡 Optional: Enable K2 Credentials Auto-Update

By default, the server works without K2 credentials. If you want to enable automatic token updates:

1. **Create `accounts.txt`** with your K2 credentials:
   ```json
   {"email": "your@email.com", "k2_password": "yourpassword"}
   ```

2. **Edit `.env`** and change:
   ```bash
   ENABLE_TOKEN_AUTO_UPDATE=true
   ```

3. **Restart the server**:
   ```bash
   ./deploy.sh
   ```

---

## 📊 Server Management

### Check if server is running
```bash
curl http://localhost:7000/
```

### View logs
```bash
tail -f k2think2api3/server.log
```

### Stop the server
```bash
kill $(cat k2think2api3/.server.pid)
```

### Restart the server
```bash
cd k2think2api3
./deploy.sh
```

---

## 🐛 Troubleshooting

### Server won't start

**Problem**: Error about missing `accounts.txt`

**Solution**: Make sure `.env` has `ENABLE_TOKEN_AUTO_UPDATE=false`, or create `accounts.txt` with K2 credentials.

```bash
cd k2think2api3
# Check current setting
grep ENABLE_TOKEN_AUTO_UPDATE .env

# If it's true but you don't have accounts.txt, change it:
sed -i 's/ENABLE_TOKEN_AUTO_UPDATE=true/ENABLE_TOKEN_AUTO_UPDATE=false/' .env

# Restart server
./deploy.sh
```

### Port already in use

**Problem**: Port 7000 is already in use

**Solution**: Change the port in `.env`:

```bash
# Edit .env and change PORT value
PORT=8000

# Restart server
./deploy.sh
```

### Python version issues

**Problem**: Python 3 not found or wrong version

**Solution**: Install Python 3.8 or higher:

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip

# On macOS
brew install python3
```

---

## 🌟 Features

- ✅ OpenAI-compatible API interface
- ✅ Supports K2-Think model
- ✅ Optional token auto-update
- ✅ Streaming responses
- ✅ Easy deployment
- ✅ Comprehensive logging
- ✅ Docker support (see main README)

---

## 📚 More Information

For detailed documentation, see:
- [Full README](README.md) - Complete documentation
- [Deployment Guide](README_NEW_SECTION.md) - Advanced deployment options
- [Project Repository](https://github.com/Zeeeepa/k2think2api3)

---

## 🎯 Quick Reference

| What | Command |
|------|---------|
| Deploy | `curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh \| bash` |
| Test | `cd k2think2api3 && ./send_request.sh` |
| Logs | `tail -f k2think2api3/server.log` |
| Stop | `kill $(cat k2think2api3/.server.pid)` |
| Restart | `cd k2think2api3 && ./deploy.sh` |

---

## 💬 Support

If you encounter issues:
1. Check the logs: `tail -f k2think2api3/server.log`
2. Review the troubleshooting section above
3. Open an issue on [GitHub](https://github.com/Zeeeepa/k2think2api3/issues)

