#!/bin/bash

# K2Think API Server Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.server.pid"
LOG_FILE="$SCRIPT_DIR/server.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

case "${1:-}" in
    start)
        log_info "Starting K2Think API server..."
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        nohup python3 k2think_proxy.py &> "$LOG_FILE" &
        echo $! > "$PID_FILE"
        log_success "Server started"
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            pid=$(cat "$PID_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping server (PID: $pid)..."
                kill "$pid"
                rm -f "$PID_FILE"
                log_success "Server stopped"
            else
                log_warning "Server is not running"
                rm -f "$PID_FILE"
            fi
        else
            log_warning "PID file not found"
        fi
        ;;
    restart)
        "$0" stop
        sleep 2
        "$0" start
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            log_success "Server is running (PID: $(cat "$PID_FILE"))"
        else
            log_warning "Server is not running"
        fi
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            log_error "Log file not found: $LOG_FILE"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo "  start   - Start the server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  status  - Show server status"
        echo "  logs    - Show server logs"
        exit 1
        ;;
esac
