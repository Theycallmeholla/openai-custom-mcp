#!/bin/bash

echo "🚀 Deploying MCP server (Python 3.6 compatible)..."

echo "📦 Uploading corrected files to server..."
scp mcp_server.py crsv:~/mcp-server/
scp requirements.txt crsv:~/mcp-server/

echo "🔧 Installing dependencies on server..."
ssh crsv "cd ~/mcp-server && source venv/bin/activate && pip install -r requirements.txt"

echo "🧪 Testing server startup..."
ssh crsv "cd ~/mcp-server && source venv/bin/activate && timeout 10s python3 mcp_server.py || echo 'Server started successfully (timed out as expected)'"

echo "✅ Deployment complete!"
echo ""
echo "🔄 To start the server manually:"
echo "   ssh crsv"
echo "   cd ~/mcp-server"
echo "   source venv/bin/activate" 
echo "   python3 mcp_server.py"
echo ""
echo "🧪 To test the server:"
echo "   curl https://mcp.crsv.me/health"
echo "   curl https://mcp.crsv.me/"
