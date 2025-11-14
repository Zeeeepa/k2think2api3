# K2CC - K2Think Claude Code Complete Setup

**Version:** 3.0.0  
**Last Updated:** 2025-11-14

## 📖 Overview

K2CC is a **single-script deployment automation tool** that sets up a complete Claude Code environment powered by K2Think inference. It provides an interactive, user-friendly experience that guides you through the entire setup process.

## 🎯 What Does K2CC Do?

K2CC automatically:

1. ✅ Prompts for your K2Think credentials (email/password)
2. ✅ Installs all required system dependencies
3. ✅ Clones the k2think2api3 repository
4. ✅ Sets up Python virtual environment
5. ✅ Configures K2Think server with your credentials
6. ✅ Extracts authentication tokens from K2Think API
7. ✅ Starts the K2Think server on port 7000
8. ✅ Installs Node.js (via NVM if needed)
9. ✅ Installs claude-code-router globally
10. ✅ Configures router to use K2Think backend
11. ✅ Starts the Claude Code Router on port 3456
12. ✅ Adds convenient aliases and environment to your `.bashrc`
13. ✅ Validates that all services are running

## 🚀 Quick Start

### Prerequisites

- **Linux/Unix system** (Ubuntu, Debian, CentOS, RHEL, Fedora)
- **Python 3.7+** installed
- **Internet connection**
- **sudo privileges** (for installing system packages)
- **K2Think account** (email and password from k2api.com)

### One-Line Installation

```bash
# Download and run k2cc.py
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/k2cc.py | python3
```

### Alternative: Clone and Run

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/k2think2api3.git
cd k2think2api3

# Run the setup script
python3 scripts/k2cc.py
```

## 📝 Interactive Setup Process

When you run `k2cc.py`, you'll be prompted for:

```
K2Think Email: your.email@example.com
K2Think Password: your_password
```

**Note:** Credentials are entered in plain text (not hidden) and saved to:
- `~/k2think2api3/accounts.txt` - For K2Think authentication
- `~/k2think2api3/.env` - For API key configuration

The script will then:
1. Display your entered credentials for confirmation
2. Ask you to confirm before proceeding
3. Execute all installation steps automatically
4. Show progress with color-coded output
5. Log everything to `~/k2cc_install_YYYYMMDD_HHMMSS.log`

## ⚙️ What Gets Installed

### System Packages

- **Python 3** and pip
- **Git** for repository management
- **curl** and **wget** for downloads
- **build-essential** (gcc, make)
- **jq** for JSON parsing

### Python Environment

- Virtual environment at `~/k2think2api3/venv`
- FastAPI, Uvicorn, HTTPx
- Pydantic, python-dotenv
- Requests, pytz

### Node.js Ecosystem

- **Node.js LTS** (via NVM)
- **npm** package manager
- **@musistudio/claude-code-router** (global install)

### Services

- **K2Think Server** - Runs on `http://localhost:7000`
- **Claude Code Router** - Runs on `http://127.0.0.1:3456`

## 🔧 Post-Installation

### 1. Reload Your Shell

After installation completes, reload your shell environment:

```bash
# Option 1: Source bashrc
source ~/.bashrc

# Option 2: Start new shell
exec $SHELL
```

### 2. Verify Services

Check that all services are running:

```bash
k2check
```

Expected output:
```
🔍 K2Think System Status
========================
K2Think Server (7000): ✅ Running
Claude Router (3456): ✅ Running
```

### 3. Test Claude Code

Try a simple prompt:

```bash
# Generate code
ccr code "Write a Python hello world function"

# Interactive mode
ccr code
```

## 📚 Useful Commands

K2CC adds these convenient aliases to your shell:

### Service Management

```bash
k2-start       # Start K2Think server
k2-stop        # Stop K2Think server
k2-restart     # Restart K2Think server
k2-status      # Show detailed server status (JSON)
k2-logs        # View server logs (tail -f)
ccr-status     # Check Claude Code Router status
ccr stop       # Stop the router
ccr start      # Start the router
```

### Health Checks

```bash
k2check        # Check status of all services
```

### Manual Service Control

```bash
# K2Think Server
curl http://localhost:7000/health

# Claude Code Router
curl http://127.0.0.1:3456/health
```

## 🌍 Environment Variables

K2CC automatically configures these environment variables in your `.bashrc`:

```bash
K2THINK_HOME          # Path to k2think2api3 directory
K2THINK_SERVER        # K2Think server URL (http://localhost:7000)
K2THINK_ROUTER        # Router URL (http://127.0.0.1:3456)
K2THINK_API_KEY       # Your generated API key
```

## 📂 Directory Structure

After installation:

```
~/k2think2api3/
├── venv/                    # Python virtual environment
├── scripts/
│   ├── k2cc.py             # This installation script
│   ├── start.sh            # K2Think server start script
│   └── ...
├── accounts.txt            # Your K2Think credentials
├── .env                    # API configuration
├── data/
│   └── tokens.txt         # Extracted authentication tokens
├── server.log             # K2Think server logs
└── ...

~/.claude-code-router/
├── config.json            # Router configuration
└── .claude-code-router.pid # Router process ID

~/k2cc_install_*.log       # Installation logs (timestamped)
```

## 🐛 Troubleshooting

### Services Not Starting

**Check K2Think Server:**
```bash
tail -f ~/k2think2api3/server.log
```

**Check Router:**
```bash
ccr status
```

**Restart Services:**
```bash
k2-restart
ccr stop && ccr start
```

### Port Conflicts

If ports 7000 or 3456 are already in use:

```bash
# Find what's using the ports
sudo lsof -i :7000
sudo lsof -i :3456

# Kill conflicting processes
sudo kill -9 <PID>

# Restart services
k2-restart
ccr start
```

### Token Extraction Failed

```bash
cd ~/k2think2api3
source venv/bin/activate
python3 get_tokens_fixed.py
```

### Installation Logs

Check detailed logs for debugging:

```bash
# Find latest log
ls -lt ~/k2cc_install_*.log | head -1

# View log
cat ~/k2cc_install_YYYYMMDD_HHMMSS.log
```

### Clean Reinstall

To completely remove and reinstall:

```bash
# Stop services
k2-stop
ccr stop

# Remove installation
rm -rf ~/k2think2api3
rm -rf ~/.claude-code-router

# Remove from bashrc (manually edit)
nano ~/.bashrc  # Remove K2Think section

# Reinstall
python3 scripts/k2cc.py
```

## 🔒 Security Notes

### Credential Storage

- Credentials are stored in **plain text** in `~/k2think2api3/accounts.txt`
- This is a local development setup
- **For production**, consider using environment variables or secrets management

### API Keys

- Auto-generated API key format: `sk-k2think-proxy-TIMESTAMP`
- Keys are stored in `~/k2think2api3/.env`
- Keys are also exported as `K2THINK_API_KEY` environment variable

### Network Security

- K2Think server binds to `0.0.0.0` (all interfaces)
- Claude Router binds to `127.0.0.1` (localhost only)
- Consider using a firewall for additional security

## 📊 System Requirements

### Minimum

- **OS:** Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+)
- **RAM:** 1 GB
- **Disk:** 2 GB free space
- **CPU:** 1 core

### Recommended

- **OS:** Ubuntu 22.04 LTS or Debian 11+
- **RAM:** 2 GB+
- **Disk:** 5 GB free space
- **CPU:** 2+ cores

## 🔄 Updating

To update your installation:

```bash
cd ~/k2think2api3
git pull origin main
k2-restart
ccr stop && ccr start
```

## 🆘 Support

### Getting Help

1. **Check logs:** `cat ~/k2cc_install_*.log`
2. **Check server logs:** `k2-logs`
3. **Verify services:** `k2check`
4. **Review this documentation**

### Common Issues

| Issue | Solution |
|-------|----------|
| `Command not found: ccr` | Reload shell: `source ~/.bashrc` |
| `Port already in use` | Kill conflicting process or change port |
| `Module not found` | Reinstall: `pip install -r requirements.txt` |
| `Permission denied` | Check file permissions: `chmod +x scripts/*.sh` |
| `Token extraction failed` | Run manually: `python3 get_tokens_fixed.py` |

## 📄 License

MIT License - Free to use and modify

## 🙏 Credits

- **K2Think API:** https://k2api.com
- **Claude Code Router:** @musistudio/claude-code-router
- **Development:** Codegen AI

## 📌 Version History

### v3.0.0 (2025-11-14)
- ✨ Interactive credential prompting
- ✨ Complete consolidation into 2 files
- ✨ Enhanced logging and error handling
- ✨ Automatic retry logic
- ✨ Comprehensive validation
- ✨ User-friendly output with colors

### v2.0.0
- Enhanced logging to files
- Retry logic for transient failures
- Better error messages

### v1.0.0
- Initial release
- Basic deployment automation
- Hardcoded credentials

---

**Ready to start?** Run `python3 scripts/k2cc.py` and follow the prompts! 🚀

