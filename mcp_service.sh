#!/bin/bash

# MCP Server management script
# Usage: ./mcp_service.sh [start|stop|restart|status]

MCP_DIR="$HOME/mcp-server"
PID_FILE="$MCP_DIR/mcp_server.pid"

start_server() {
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "❌ MCP server is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    echo "🚀 Starting MCP server..."
    cd "$MCP_DIR"
    source venv/bin/activate
    
    # Start server in background and save PID
    nohup python3 mcp_server.py > mcp_server.log 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✅ MCP server started successfully (PID: $(cat $PID_FILE))"
        echo "📋 Log file: $MCP_DIR/mcp_server.log"
        echo "🌐 Test it: curl http://localhost:8000/health"
    else
        echo "❌ Failed to start MCP server"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_server() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ No PID file found. Server may not be running."
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🛑 Stopping MCP server (PID: $PID)..."
        kill "$PID"
        sleep 2
        
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️ Server didn't stop gracefully, forcing..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ MCP server stopped"
    else
        echo "❌ Server not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
}

status_server() {
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✅ MCP server is running (PID: $(cat $PID_FILE))"
        echo "📊 Process info:"
        ps -p $(cat "$PID_FILE") -o pid,ppid,cmd,etime
        
        echo ""
        echo "🧪 Quick health check:"
        curl -s http://localhost:8000/health 2>/dev/null || echo "❌ Health check failed"
    else
        echo "❌ MCP server is not running"
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    fi
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the MCP server"
        echo "  stop    - Stop the MCP server"
        echo "  restart - Restart the MCP server"
        echo "  status  - Check server status"
        exit 1
        ;;
esac
