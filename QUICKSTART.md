# K2Think API - Quick Start Guide

## 🚀 One-Command Deployment

Deploy the K2Think API proxy in seconds with **automatic credential handling** and **API key export**!

### Method 1: With Pre-Exported Credentials (Recommended)

```bash
export K2_EMAIL="your@email.com"
export K2_PASSWORD="yourpassword"
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

### Method 2: Interactive Credential Prompt

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

The script will automatically prompt you for credentials if they're not already set!

### What Happens Automatically

1. ✅ **Credential Detection**: Checks for K2_EMAIL/K2_PASSWORD env vars
2. ✅ **Interactive Prompt**: Asks for credentials if not found (or reads from accounts.txt)
3. ✅ **Account Setup**: Creates accounts.txt automatically from your input
4. ✅ **Token Setup**: Creates empty tokens.txt file
5. ✅ **Environment Setup**: Creates Python virtual environment
6. ✅ **Dependency Installation**: Installs all required packages
7. ✅ **Server Start**: Launches server on http://localhost:7000
8. ✅ **API Key Export**: Automatically exports OPENAI_API_KEY and OPENAI_BASE_URL
9. ✅ **Test Run**: Verifies everything works with a test request

---

## 📋 What Gets Configured

After running the deployment script, you'll have:

- **Server URL**: `http://localhost:7000`
- **API Key**: Generated automatically (stored in `.env` file)
- **Environment Variables**: `OPENAI_API_KEY` and `OPENAI_BASE_URL` exported
- **Virtual Environment**: Located at `k2think2api3/venv/` with OpenAI SDK installed
- **Token Auto-Update**: Enabled with your K2 credentials
- **Test Script**: Ready to use (`send_request.sh`)

---

## 🐍 Using with Python

### Option 1: Using the Virtual Environment (Recommended)

```bash
# Activate the venv
source ~/k2think2api3/venv/bin/activate

# Run your script
python your_script.py

# Deactivate when done
deactivate
```

### Option 2: Direct Execution with venv Python

```bash
~/k2think2api3/venv/bin/python your_script.py
```

### Option 3: Export Environment Variables

```bash
cd ~/k2think2api3
export OPENAI_API_KEY=$(grep VALID_API_KEY .env | cut -d'=' -f2)
export OPENAI_BASE_URL="http://localhost:7000/v1"

# Now use system Python (if you have openai installed)
python your_script.py
```

---

## 🧪 Example Python Scripts

### Simple Example (Using Environment Variables)

```python
from openai import OpenAI

# Uses OPENAI_API_KEY and OPENAI_BASE_URL from environment
client = OpenAI()

response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "What is your model name?"}]
)

print(response.choices[0].message.content)
```

### Explicit Configuration

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7000/v1",
    api_key="sk-k2think-proxy-xxxxxxxxxx"  # Get from .env file
)

response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
```

### Streaming Response Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7000/v1",
    api_key="sk-k2think-proxy-xxxxxxxxxx"
)

stream = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "Write a short poem about AI"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)
print()
```

---

## 🧪 Testing the API

### Using the Test Script

```bash
cd k2think2api3
./send_request.sh
```

### Using curl

```bash
curl http://localhost:7000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-k2think-proxy-xxxxxxxxxx" \
  -d '{
    "model": "MBZUAI-IFM/K2-Think",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🔧 Server Management

### View Server Logs

```bash
tail -f ~/k2think2api3/server.log
```

### Stop the Server

```bash
kill $(cat ~/k2think2api3/.server.pid)
```

### Restart the Server

```bash
cd ~/k2think2api3
./deploy.sh
```

### Get Your API Key

```bash
grep VALID_API_KEY ~/k2think2api3/.env
```

---

## 🛠️ Advanced Configuration

### Enable/Disable Token Auto-Update

Edit `.env` file:

```bash
# Enable auto-update (requires accounts.txt with K2 credentials)
ENABLE_TOKEN_AUTO_UPDATE=true

# Disable auto-update
ENABLE_TOKEN_AUTO_UPDATE=false
```

### Configure K2 Credentials

Edit `accounts.txt`:

```json
{"email": "your@email.com", "k2_password": "yourpassword"}
```

### Change Server Port

Edit `.env` file:

```bash
PORT=8000  # Default is 7000
```

Then restart the server.

---

## 🔍 Troubleshooting

### Server won't start

1. Check if port 7000 is already in use:
   ```bash
   lsof -i :7000
   ```

2. View server logs:
   ```bash
   cat ~/k2think2api3/server.log
   ```

3. Ensure Python 3.8+ is installed:
   ```bash
   python3 --version
   ```

### "Module not found: openai"

Use the virtual environment:
```bash
source ~/k2think2api3/venv/bin/activate
python your_script.py
```

Or use venv Python directly:
```bash
~/k2think2api3/venv/bin/python your_script.py
```

### Token auto-update not working

1. Verify `accounts.txt` exists and has correct format
2. Check `.env` has `ENABLE_TOKEN_AUTO_UPDATE=true`
3. View updater logs in `server.log`

---

## 📚 API Endpoints

### Chat Completions
- **Endpoint**: `/v1/chat/completions`
- **Method**: POST
- **Compatible with**: OpenAI SDK

### Models List
- **Endpoint**: `/v1/models`
- **Method**: GET

### Health Check
- **Endpoint**: `/health`
- **Method**: GET

### Admin Endpoints

All admin endpoints require authentication:

- `/admin/tokens/stats` - View token statistics
- `/admin/tokens/reload` - Reload tokens from file
- `/admin/tokens/reset-all` - Reset all token states
- `/admin/tokens/updater/status` - Check auto-updater status
- `/admin/tokens/updater/force-update` - Trigger manual token update

---

## 🎯 Complete One-Liner Examples

### With Credentials

```bash
export K2_EMAIL="your@email.com" K2_PASSWORD="yourpassword" && curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

### Interactive Setup

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

---

## 💡 Pro Tips

1. **Keep credentials secure**: Never commit `accounts.txt` or `.env` to version control
2. **Monitor token usage**: Check `/admin/tokens/stats` regularly
3. **Use environment variables**: Easier than hardcoding API keys in scripts
4. **Virtual environment**: Always use the venv for consistent Python dependencies
5. **Logs are your friend**: Check `server.log` when troubleshooting

---

## 🚀 Next Steps

- Integrate with your application
- Set up monitoring and alerts
- Configure rate limiting if needed
- Deploy behind a reverse proxy for production use
- Set up SSL/TLS for secure connections

---

## 📞 Support

For issues or questions:
- Check the [GitHub repository](https://github.com/Zeeeepa/k2think2api3)
- Review server logs: `tail -f ~/k2think2api3/server.log`
- Verify configuration: `cat ~/k2think2api3/.env`

---

**Happy coding! 🎉**

