# Server Management Guide

## 📋 Overview

K2Think v2.0 includes powerful server management tools that make it easy to control your API proxy.

---

## 🛠️ k2think_server.sh - Main Management Script

### Available Commands

```bash
./k2think_server.sh start    # Start the server
./k2think_server.sh stop     # Stop the server  
./k2think_server.sh restart  # Restart the server
./k2think_server.sh status   # Show detailed status
./k2think_server.sh logs     # View live logs
./k2think_server.sh help     # Show help message
```

### Usage Examples

**Start the server:**
```bash
cd ~/k2think2api3
./k2think_server.sh start
```

Output:
```
Starting K2Think API server on port 7000...
✅ Server started successfully (PID: 12345)
   URL: http://localhost:7000
```

**Check status:**
```bash
./k2think_server.sh status
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  K2Think Server Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
● Server Status: Running
• PID: 12345
• Port: 7000
• URL: http://localhost:7000
• Memory: 2.5%
• CPU: 0.3%
✅ Port 7000 is listening
```

**View logs:**
```bash
./k2think_server.sh logs
```

This will show live logs (press Ctrl+C to exit).

---

## 🔄 k2think_activate.sh - Environment Activation

### What It Does

- Changes to k2think2api3 directory
- Activates virtual environment
- Shows server status
- Displays available commands

### Usage

```bash
source ~/k2think2api3/k2think_activate.sh
```

### Make It Permanent

Add to your shell config file:

**Bash:**
```bash
echo 'alias k2think="source ~/k2think2api3/k2think_activate.sh"' >> ~/.bashrc
source ~/.bashrc
```

**Zsh:**
```bash
echo 'alias k2think="source ~/k2think2api3/k2think_activate.sh"' >> ~/.zshrc
source ~/.zshrc
```

Then simply run `k2think` anytime!

---

## 🗑️ k2think_uninstall.sh - Clean Removal

### Complete Uninstallation

```bash
cd ~/k2think2api3
./k2think_uninstall.sh
```

This will:
1. Stop the running server
2. Free up the port
3. Remove the installation directory
4. Detect shell aliases (requires manual removal)

### Manual Alias Removal

If you added the `k2think` alias, remove it from:
- `~/.bashrc` (Bash users)
- `~/.zshrc` (Zsh users)

Then reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

---

## 🔍 Troubleshooting

### Server Won't Start

**Check if port is in use:**
```bash
sudo lsof -i :7000
```

**Kill process on port:**
```bash
sudo kill -9 $(sudo lsof -t -i :7000)
```

**Check logs for errors:**
```bash
cat ~/k2think2api3/server.log
```

### Server Crashes on Startup

**Check dependencies:**
```bash
cd ~/k2think2api3
source venv/bin/activate
pip install -r requirements.txt
```

**Test manually:**
```bash
python k2think_proxy.py
```

### Can't Activate Environment

**Verify venv exists:**
```bash
ls ~/k2think2api3/venv/bin/activate
```

**Recreate if missing:**
```bash
cd ~/k2think2api3
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Monitoring

### Check Deployment Log

```bash
tail -f ~/k2think2api3/k2think_deployment.log
```

### Check Server Log

```bash
tail -f ~/k2think2api3/server.log
```

### Monitor Resource Usage

```bash
./k2think_server.sh status
```

---

## 🔐 Port Management

### Change Port After Installation

1. Stop the server:
```bash
./k2think_server.sh stop
```

2. Edit .env file:
```bash
nano ~/k2think2api3/.env
```

Change `PORT=7000` to your desired port.

3. Start server:
```bash
./k2think_server.sh start
```

### Check Available Ports

```bash
# Check if specific port is free
sudo lsof -i :8000

# Find available port range
for port in {7000..7010}; do
    if ! sudo lsof -i :$port > /dev/null 2>&1; then
        echo "Port $port is available"
    fi
done
```

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| Activate environment | `source ~/k2think2api3/k2think_activate.sh` |
| Start server | `./k2think_server.sh start` |
| Stop server | `./k2think_server.sh stop` |
| Check status | `./k2think_server.sh status` |
| View logs | `./k2think_server.sh logs` |
| Restart server | `./k2think_server.sh restart` |
| Test API | `curl http://localhost:7000/v1/models` |
| Uninstall | `./k2think_uninstall.sh` |

---

## 💡 Tips

- Always activate the environment before running Python commands
- Use `./k2think_server.sh status` to check if server is healthy
- Deployment logs are in `k2think_deployment.log`
- Server logs are in `server.log`
- PID file is `.server.pid`
