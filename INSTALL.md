# 🚀 K2Think API - Dead Simple Installation

## ⚡ **THE SIMPLEST WAY** (Copy & Paste This!)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh)
```

**That's it!** The script will:
1. ✅ Ask for your K2 credentials
2. ✅ Clone the repository
3. ✅ Install dependencies
4. ✅ Start the server
5. ✅ Run a test request

---

## 📝 **With Credentials Pre-Set** (No Prompts!)

```bash
export K2_EMAIL="developer@pixelium.uk" && export K2_PASSWORD="developer123?" && bash <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh)
```

---

## 🎯 **Why This Works Better**

### ❌ Old Way (Prone to URL Mistakes):
```bash
# Easy to get wrong - users typed:
curl -fsSL https://raw.github.com/...  # ❌ WRONG
curl -fsSL https://github.com/blob/...  # ❌ WRONG
```

### ✅ New Way (Foolproof):
```bash
# Bash handles the download automatically
bash <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh)
```

**Why it's better:**
- 🔒 Bash process substitution `<()` prevents file system errors
- 🎯 Single command = less room for mistakes
- 🚀 Cleaner, more professional
- ✅ Industry-standard pattern (used by Homebrew, rustup, nvm, etc.)

---

## 🔧 **Alternative: Download Then Run**

If you prefer to see the script first:

```bash
# Download
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/install.sh -o install.sh

# Review (optional)
cat install.sh

# Run
bash install.sh
```

---

## 🚨 **Having Issues?**

### Problem: "Command not found: bash"
**Solution:** You're probably on Windows. Use WSL or Git Bash.

### Problem: "Permission denied"
**Solution:** The script doesn't need sudo. Run as your normal user.

### Problem: "curl: command not found"
**Solution:** Install curl first:
```bash
# Ubuntu/Debian
sudo apt-get install curl

# macOS
brew install curl

# CentOS/RHEL
sudo yum install curl
```

---

## 📚 **What Gets Installed?**

After running the installer, you'll have:

```
~/k2think2api3/
├── .env                 # API key and configuration
├── accounts.txt         # Your K2 credentials
├── tokens.txt          # Auto-refreshing tokens
├── server.log          # Server logs
├── .server.pid         # Process ID for stopping server
└── venv/               # Python virtual environment with OpenAI SDK
```

---

## 🎮 **Quick Commands After Install**

```bash
# View logs
tail -f ~/k2think2api3/server.log

# Stop server
kill $(cat ~/k2think2api3/.server.pid)

# Restart server
cd ~/k2think2api3 && bash deploy.sh

# Get your API key
grep VALID_API_KEY ~/k2think2api3/.env

# Test the API
cd ~/k2think2api3 && bash send_request.sh
```

---

## 🐍 **Using with Python**

After installation, use it in your Python code:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7000/v1",
    api_key="<your-api-key>"  # Get from .env file
)

response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

---

## 💡 **Pro Tips**

1. **Set environment variables** for easier use:
   ```bash
   export OPENAI_API_KEY=$(grep VALID_API_KEY ~/k2think2api3/.env | cut -d'=' -f2)
   export OPENAI_BASE_URL="http://localhost:7000/v1"
   ```

2. **Use the virtual environment** for OpenAI SDK:
   ```bash
   source ~/k2think2api3/venv/bin/activate
   python your_script.py
   ```

3. **Check server status** anytime:
   ```bash
   curl http://localhost:7000/health
   ```

---

## 🆘 **Need Help?**

- 📖 [Full Documentation](./QUICKSTART.md)
- 🐛 [URL Format Guide](./DEPLOYMENT_URL_GUIDE.md) (if you're having URL issues)
- 💬 [Open an Issue](https://github.com/Zeeeepa/k2think2api3/issues)

---

**Happy coding! 🎉**

