#!/bin/bash
# K2Think API Proxy - Server Management Script
# Usage: ./k2think_server.sh {start|stop|restart|status|logs}

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="${SCRIPT_DIR}/.server.pid"
LOG_FILE="${SCRIPT_DIR}/server.log"

# Activate venv
if [ -f "${SCRIPT_DIR}/venv/bin/activate" ]; then
    source "${SCRIPT_DIR}/venv/bin/activate"
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    exit 1
fi

# Change to script directory
cd "${SCRIPT_DIR}"

# Read port from .env
if [ -f ".env" ]; then
    PORT=$(grep "^PORT=" .env | cut -d'=' -f2)
else
    PORT=7000
fi

start_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Server is already running (PID: ${PID})${NC}"
            return 1
        fi
    fi
    
    echo -e "${BLUE}Starting K2Think API server on port ${PORT}...${NC}"
    nohup python k2think_proxy.py > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 3
    
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server started successfully (PID: ${PID})${NC}"
        echo -e "${BLUE}   URL: http://localhost:${PORT}${NC}"
        return 0
    else
        echo -e "${RED}❌ Server failed to start${NC}"
        echo -e "${YELLOW}Check logs: tail -f ${LOG_FILE}${NC}"
        return 1
    fi
}

stop_server() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  No PID file found${NC}"
        # Try to find and kill any running process
        pkill -f "python.*k2think_proxy.py"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Server is not running${NC}"
        rm -f "$PID_FILE"
        return 0
    fi
    
    echo -e "${YELLOW}Stopping server (PID: ${PID})...${NC}"
    kill $PID 2>/dev/null
    
    # Wait up to 10 seconds for graceful shutdown
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server stopped successfully${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo -e "${YELLOW}Force killing server...${NC}"
    kill -9 $PID 2>/dev/null
    rm -f "$PID_FILE"
    echo -e "${GREEN}✅ Server stopped${NC}"
}

restart_server() {
    echo -e "${CYAN}Restarting server...${NC}"
    stop_server
    sleep 2
    start_server
}

status_server() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  K2Think Server Status${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}●${NC} Server Status: ${GREEN}Running${NC}"
            echo -e "${BLUE}•${NC} PID: ${PID}"
            echo -e "${BLUE}•${NC} Port: ${PORT}"
            echo -e "${BLUE}•${NC} URL: http://localhost:${PORT}"
            
            # Check memory and CPU usage
            if command -v ps &> /dev/null; then
                MEM=$(ps -p $PID -o %mem= 2>/dev/null | tr -d ' ')
                CPU=$(ps -p $PID -o %cpu= 2>/dev/null | tr -d ' ')
                echo -e "${BLUE}•${NC} Memory: ${MEM}%"
                echo -e "${BLUE}•${NC} CPU: ${CPU}%"
            fi
            
            # Check if port is listening
            if command -v lsof &> /dev/null; then
                if sudo lsof -ti :${PORT} &> /dev/null; then
                    echo -e "${GREEN}✅${NC} Port ${PORT} is listening"
                else
                    echo -e "${YELLOW}⚠️${NC}  Port ${PORT} is not listening"
                fi
            fi
            
            return 0
        else
            echo -e "${RED}●${NC} Server Status: ${RED}Not Running${NC} (stale PID file)"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo -e "${RED}●${NC} Server Status: ${RED}Not Running${NC}"
        return 1
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}  Server Logs (tail -f ${LOG_FILE})${NC}"
        echo -e "${CYAN}  Press Ctrl+C to exit${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠️  Log file not found: ${LOG_FILE}${NC}"
        exit 1
    fi
}

show_help() {
    echo -e "${CYAN}K2Think Server Management${NC}"
    echo -e ""
    echo -e "${GREEN}Usage:${NC} $0 {start|stop|restart|status|logs|help}"
    echo -e ""
    echo -e "${BLUE}Commands:${NC}"
    echo -e "  ${GREEN}start${NC}    - Start the K2Think API server"
    echo -e "  ${GREEN}stop${NC}     - Stop the running server"
    echo -e "  ${GREEN}restart${NC}  - Restart the server"
    echo -e "  ${GREEN}status${NC}   - Show server status and information"
    echo -e "  ${GREEN}logs${NC}     - Show and follow server logs"
    echo -e "  ${GREEN}help${NC}     - Show this help message"
    echo -e ""
}

# Main command handler
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac

