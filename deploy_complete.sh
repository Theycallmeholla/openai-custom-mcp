#!/bin/bash

# Complete MCP deployment script
echo "🚀 Starting complete MCP server deployment..."

# Upload all necessary files
echo "📦 Uploading files to server..."
scp -r \
    mcp_server.py \
    requirements.txt \
    .env \
    htaccess_for_server \
    setup_server_structure.sh \
    crsv:/home/wqt4uxigy2y4/

# Connect and set everything up
echo "🔧 Connecting to server for setup..."

ssh crsv << 'SETUP_EOF'
echo "🏠 Current location: $(pwd)"
echo "📋 Files uploaded:"
ls -la

# Make setup script executable and run it
chmod +x setup_server_structure.sh
./setup_server_structure.sh

# Move to mcp-server directory and set up the application
echo "📁 Setting up MCP server application..."
cd ~/mcp-server

# Copy application files
cp ~/mcp_server.py .
cp ~/requirements.txt .
cp ~/.env .

# Activate virtual environment (create if it doesn't exist)
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install fastapi pydantic python-dotenv uvicorn

# Try to install from requirements
pip install -r requirements.txt 2>/dev/null || echo "⚠️ Some requirements might not be available for Python 3.6"

echo "🧪 Testing MCP server..."
# Quick test to see if the server starts
timeout 10s python3 mcp_server.py &
SERVER_PID=$!
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ MCP server started successfully!"
    kill $SERVER_PID
else
    echo "❌ MCP server failed to start"
fi

echo ""
echo "🎯 Deployment Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Web Directory: ~/public_html/mcp/"
echo "🔗 Public URL: https://mcp.crsv.me/"
echo "🖥️  Server Files: ~/mcp-server/"
echo "🔧 Configuration: ~/public_html/mcp/_config.env"
echo ""
echo "🚀 To start the server:"
echo "   cd ~/mcp-server"
echo "   source venv/bin/activate"
echo "   python3 mcp_server.py"
echo ""
echo "🧪 To test locally:"
echo "   curl http://localhost:8000/health"
echo ""
echo "🌐 To test via web:"
echo "   curl https://mcp.crsv.me/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SETUP_EOF

echo "✅ Deployment complete!"
echo ""
echo "🔄 Next steps:"
echo "1. SSH into your server: ssh crsv"
echo "2. Start the MCP server: cd ~/mcp-server && source venv/bin/activate && python3 mcp_server.py"
echo "3. Test it works: curl https://mcp.crsv.me/health"
