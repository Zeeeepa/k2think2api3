# 🔐 K2Think Credential Setup Guide

The K2Think API proxy now supports **interactive credential input** during setup, making it easier to configure your API credentials.

## 📋 Setup Methods

### Method 1: Interactive Prompt (NEW! ✨)

The setup script will automatically prompt you for credentials if none are found:

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/codegen-bot/csds-python-venv-fix/csds.sh -o csds.sh
bash csds.sh codegen-bot/csds-python-venv-fix
```

**What happens:**
1. Script checks for existing `accounts.txt`
2. If not found, prompts: "Would you like to enter your credentials now? (y/n)"
3. If yes, asks for:
   - 📧 **Email** (visible input)
   - 🔑 **Password** (visible input as requested)
4. Saves to `accounts.txt` automatically
5. Continues with deployment

**Example interaction:**
```
⚠️  No K2Think credentials found!

Would you like to enter your credentials now? (y/n): y

🔐 K2Think Account Setup
==========================

To use this API proxy, you need a K2Think account.
If you don't have one, sign up at: https://www.k2think.ai/

📧 Enter your K2Think email: user@example.com
🔑 Enter your K2Think password (input will be visible):
Password: mypassword123

💾 Saving credentials to accounts.txt...
✅ Credentials saved!
```

### Method 2: Environment Variables

Set credentials as environment variables before running:

```bash
export K2_EMAIL="your@email.com"
export K2_PASSWORD="yourpassword"
bash csds.sh
```

### Method 3: Manual File Creation

Create `accounts.txt` manually before running setup:

```bash
cd k2think2api3
echo '{"email": "your@email.com", "k2_password": "yourpassword"}' > accounts.txt
bash setup.sh
```

## 🔄 Updating Credentials

If `accounts.txt` contains placeholder credentials, the script will detect and offer to update:

```
⚠️  Warning: accounts.txt contains placeholder credentials!

Would you like to update with real credentials? (y/n):
```

## 🛡️ Security Notes

1. **Visible Password Input**: As requested, passwords are displayed during input for easier verification
2. **Local Storage**: Credentials are stored locally in `accounts.txt`
3. **Git Ignore**: Make sure `accounts.txt` is in `.gitignore` (already configured)
4. **Virtual Environment**: All dependencies are isolated in `venv/`

## ❌ Troubleshooting

### Server Won't Start

**Error:** `配置错误: 错误：启用了token自动更新，但账户文件 accounts.txt 不存在`

**Solution:** Run setup again and enter credentials when prompted:
```bash
bash setup.sh
```

### Invalid Credentials

**Error:** `Model not found (400)` or `No available tokens`

**Solution:** 
1. Verify your K2Think account works at https://www.k2think.ai/
2. Update `accounts.txt` with correct credentials
3. Restart the server: `bash deploy.sh`

### Placeholder Credentials Detected

If you see: `Warning: accounts.txt contains placeholder credentials!`

**Solution:** Type `y` when asked to update credentials

## 🎯 Quick Start with Interactive Setup

```bash
# 1. Download and run CSDS
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/codegen-bot/csds-python-venv-fix/csds.sh -o csds.sh
bash csds.sh codegen-bot/csds-python-venv-fix

# 2. When prompted, enter your credentials:
#    Email: your@email.com
#    Password: yourpassword

# 3. Server starts automatically!

# 4. Test the API:
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",  # From .env file
    base_url="http://localhost:7000/v1"
)

response = client.chat.completions.create(
    model="k2-think",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## 📞 Getting K2Think Account

1. Visit https://www.k2think.ai/
2. Sign up for an account
3. Use your login email and password for this proxy

---

**Need help?** Check the main [README.md](README.md) for more information.

