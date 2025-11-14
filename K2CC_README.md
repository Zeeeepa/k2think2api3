# K2CC - K2Think Claude Code Complete Setup

**One-script automation for complete Claude Code deployment powered by K2Think inference**

## 🎯 What is K2CC?

K2CC (K2Think Claude Code) is a comprehensive automation script that sets up a complete AI coding environment from scratch. It handles everything from system dependencies to Claude Code integration in a single command.

## ✨ Features

**Complete Automation:**
- ✅ Installs all system dependencies
- ✅ Clones k2think2api3 repository
- ✅ Sets up Python virtual environment
- ✅ Configures K2Think server with credentials
- ✅ Extracts and manages K2Think tokens
- ✅ Starts K2Think server (port 7000)
- ✅ Installs Node.js (if needed)
- ✅ Installs claude-code-router globally
- ✅ Configures router to point to K2Think
- ✅ Starts claude-code-router service (port 3456)
- ✅ Validates complete deployment

**Result:** Fully functional Claude Code environment powered by K2Think inference!

## 🚀 Quick Start

### One-Line Installation

```bash
python3 k2cc.py
```

That's it! The script will:
1. Ask for confirmation
2. Install everything
3. Configure all services
4. Validate deployment
5. Show you how to use Claude Code

### With Custom Credentials

```bash
python3 k2cc.py --email your@email.com --password "yourpassword"
```

### Custom Installation Directory

```bash
python3 k2cc.py --dir /opt/k2think
```

### Skip System Dependencies

If you already have Python, Git, etc. installed:

```bash
python3 k2cc.py --skip-deps
```

## 📋 Requirements

**Minimum:**
- Python 3.7+
- Internet connection
- sudo/root access (for system packages)
- 2GB free disk space

**Supported Systems:**
- Ubuntu/Debian (apt)
- CentOS/RHEL (yum)
- macOS (homebrew)
- Other Linux distributions (with manual dependencies)

## 🔧 Command Line Options

```
usage: k2cc.py [-h] [--email EMAIL] [--password PASSWORD] [--dir DIR] [--skip-deps]

Options:
  --email EMAIL        K2Think account email
                       (default: developer@pixelium.uk)
  
  --password PASSWORD  K2Think account password
                       (default: developer123?)
  
  --dir DIR           Installation directory
                       (default: ~/k2think2api3)
  
  --skip-deps         Skip system dependencies installation
  
  -h, --help          Show help message
```

## 📊 Deployment Steps

K2CC performs 10 steps automatically:

1. **Install System Dependencies** - Python, Git, Node.js prerequisites
2. **Clone Repository** - Download k2think2api3 from GitHub
3. **Setup Python Environment** - Create venv and install packages
4. **Configure K2Think Server** - Set up credentials and environment
5. **Extract Tokens** - Authenticate with K2Think API
6. **Install Node.js** - Via nvm if not present
7. **Install Claude Code Router** - Global npm installation
8. **Configure Router** - Point to K2Think server
9. **Start Services** - Launch K2Think + Router
10. **Validate Deployment** - End-to-end testing

## 🎨 Example Session

```bash
$ python3 k2cc.py

======================================================================
         K2CC - K2Think Claude Code Complete Setup
======================================================================

Configuration:
   Email: developer@pixelium.uk
   Password: ****************
   Directory: /home/user/k2think2api3

Proceed with installation? (Y/n): y

[1/10] Installing System Dependencies
   → Updating package lists
   → Installing packages
✅ System dependencies installed

[2/10] Cloning K2Think Repository
   → Cloning https://github.com/Zeeeepa/k2think2api3.git
✅ Repository cloned to /home/user/k2think2api3

[3/10] Setting Up Python Environment
   → Creating virtual environment
   → Upgrading pip
   → Installing Python dependencies
✅ Python environment configured

[4/10] Configuring K2Think Server
✅ Credentials configured: developer@pixelium.uk
✅ Environment configured with API key: sk-k2think-proxy-1731583074

[5/10] Extracting K2Think Tokens
ℹ️  Using get_tokens_fixed.py
   → Extracting tokens from K2Think API
✅ Tokens extracted successfully

ℹ️  Starting K2Think server...
ℹ️  Waiting for K2Think server to initialize...
✅ K2Think server is running on port 7000

[6/10] Installing Node.js
✅ Node.js already installed: v22.14.0

[7/10] Installing Claude Code Router
   → Installing @musistudio/claude-code-router
✅ Claude Code Router installed

[8/10] Configuring Claude Code Router
✅ Configuration saved to /home/user/.claude-code-router/config.json

[9/10] Starting Claude Code Router
   → Stopping existing router
ℹ️  Starting claude-code-router service...
✅ Claude Code Router is running on port 3456

[10/10] Validating Deployment

======================================================================
Deployment Status:

   ✅ K2Think Server (port 7000)
   ✅ Claude Code Router (port 3456)
   ✅ End-to-End Integration

======================================================================
🎉 Deployment Complete!
======================================================================

📋 Architecture:
   Claude Code → claude-code-router → K2Think Server → K2Think API
                 (Port 3456)         (Port 7000)

🚀 Quick Start:
   ccr code "Create a hello world script"

🎯 Available Models:
   • MBZUAI-IFM/K2-Think (with reasoning)
   • MBZUAI-IFM/K2-Think-nothink (without reasoning)

🔧 Management Commands:
   ccr status      # Check router status
   ccr stop        # Stop router
   ccr restart     # Restart router
   ccr ui          # Web configuration interface
   ccr model       # Interactive model selector

📁 Installation Directory:
   /home/user/k2think2api3

📝 Configuration:
   Router: ~/.claude-code-router/config.json
   Logs: ~/.claude-code-router/logs/

✅ All systems operational! Ready to use Claude Code with K2Think.
```

## 🔍 Troubleshooting

### Script Fails During Installation

**Check Python Version:**
```bash
python3 --version  # Should be 3.7 or higher
```

**Check Internet Connection:**
```bash
curl -I https://github.com
```

**Run with Debug Info:**
```bash
python3 k2cc.py 2>&1 | tee k2cc_install.log
```

### Services Not Starting

**Check K2Think Server:**
```bash
curl http://localhost:7000/health
# OR
curl http://localhost:7000/
```

**Check Router:**
```bash
ccr status
```

**View Logs:**
```bash
tail -f ~/.claude-code-router/logs/ccr-*.log
```

### Token Extraction Fails

**Manual Token Extraction:**
```bash
cd ~/k2think2api3
source venv/bin/activate
python3 get_tokens_fixed.py
```

**Check Credentials:**
```bash
cat ~/k2think2api3/accounts.txt
```

### Node.js Issues

**Check Installation:**
```bash
node --version
npm --version
```

**Reinstall Node.js:**
```bash
# Via nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install --lts
```

### Router Won't Start

**Kill Existing Process:**
```bash
ccr stop
# OR
pkill -f claude-code-router
```

**Reinstall Router:**
```bash
npm uninstall -g @musistudio/claude-code-router
npm install -g @musistudio/claude-code-router
```

## 🎯 Post-Installation

### Using Claude Code

**Basic Usage:**
```bash
ccr code "Create a Python FastAPI hello world app"
```

**Interactive Mode:**
```bash
ccr code
# Then type your requests
```

**With Specific Model:**
```bash
ccr code "/model k2think,MBZUAI-IFM/K2-Think-nothink"
ccr code "Optimize this code"
```

### Managing Services

**Check Status:**
```bash
ccr status
```

**Stop All:**
```bash
ccr stop
# K2Think server:
kill $(cat ~/k2think2api3/.server.pid)
```

**Restart:**
```bash
ccr restart
# K2Think server:
cd ~/k2think2api3
bash scripts/start.sh
```

### Configuration

**Edit Router Config:**
```bash
nano ~/.claude-code-router/config.json
ccr restart
```

**Change K2Think Credentials:**
```bash
nano ~/k2think2api3/accounts.txt
cd ~/k2think2api3
python3 get_tokens_fixed.py
bash scripts/restart.sh
```

## 🏗️ Architecture

```
┌─────────────┐
│ Claude Code │ (Your terminal/IDE)
└──────┬──────┘
       │ Anthropic API format
       ▼
┌──────────────────────┐
│ claude-code-router   │ Port 3456
│ - Request translation│
│ - Model routing      │
│ - Smart load balance │
└──────┬───────────────┘
       │ OpenAI API format
       ▼
┌──────────────────────┐
│ K2Think Server       │ Port 7000
│ - Token management   │
│ - Request proxy      │
│ - Load balancing     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ K2Think API (MBZUAI) │
│ - K2-Think model     │
│ - Advanced reasoning │
│ - Code generation    │
└──────────────────────┘
```

## 📦 What Gets Installed

**System Packages:**
- python3, python3-pip, python3-venv
- git, curl, wget
- build-essential (gcc, make)
- Node.js (via nvm)

**Python Packages:**
- fastapi, uvicorn
- httpx, requests
- pydantic, python-dotenv

**Node.js Packages:**
- @musistudio/claude-code-router

**Repositories:**
- k2think2api3 (complete)

## 🔐 Security Notes

- Credentials are stored locally in `accounts.txt`
- API keys are generated and stored in `.env`
- All traffic is local (localhost only by default)
- No external services except K2Think API
- Token files are gitignored

## 📝 Environment Variables

After installation, these are set in `.env`:

```env
API_KEY=sk-k2think-proxy-TIMESTAMP
PORT=7000
HOST=0.0.0.0
LOG_LEVEL=info
TOKEN_REFRESH_INTERVAL=3600
MAX_RETRIES=3
REQUEST_TIMEOUT=120
```

## 🆘 Support

**Check Installation:**
```bash
python3 k2cc.py --help
```

**View This Guide:**
```bash
cat ~/k2think2api3/K2CC_README.md
```

**Check Services:**
```bash
# K2Think
curl http://localhost:7000/health

# Router
ccr status
curl http://127.0.0.1:3456/health
```

**Get Logs:**
```bash
# K2Think
tail -f ~/k2think2api3/server.log

# Router
tail -f ~/.claude-code-router/logs/ccr-*.log
```

## 🎉 Success Indicators

After running k2cc.py, you should see:

✅ K2Think Server (port 7000) - Running
✅ Claude Code Router (port 3456) - Running  
✅ End-to-End Integration - Working

If all three show ✅, you're ready to code with Claude powered by K2Think!

## 🚀 Next Steps

1. **Test the setup:**
   ```bash
   ccr code "Create a hello world script"
   ```

2. **Explore models:**
   ```bash
   ccr model
   ```

3. **Configure router:**
   ```bash
   ccr ui
   ```

4. **Start building:**
   ```bash
   ccr code "Create a FastAPI REST API with authentication"
   ```

Enjoy coding with Claude Code powered by K2Think! 🎨✨

