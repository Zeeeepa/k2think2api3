# 🎯 Claude Code Integration with K2Think Server

Complete guide for using your K2Think server with Claude Code via claude-code-router.

## Quick Start

```bash
# One-line setup
bash scripts/setup_claude_code.sh

# Start coding
ccr code
```

## Architecture

```
Claude Code → claude-code-router → K2Think Server → K2Think API
             (Port 3456)         (Port 7000)      (MBZUAI)
```

For full documentation, see the complete guide in this file or visit:
https://github.com/musistudio/claude-code-router

## Models Available

- **MBZUAI-IFM/K2-Think** - Full model with reasoning
- **MBZUAI-IFM/K2-Think-nothink** - Faster without reasoning

## Usage

```bash
ccr code "Create a hello world script"
ccr model  # Interactive model selector  
ccr ui     # Web configuration interface
```

See full documentation above for advanced configuration and troubleshooting.
