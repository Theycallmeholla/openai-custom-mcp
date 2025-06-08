# MCP Server for ChatGPT Integration

A secure, configurable MCP (Model Context Protocol) server that connects to ChatGPT Deep Research with authentication and environment-based configuration.

## Quick Start

### 1. Local Development Setup

```bash
# Clone the repository
git clone https://github.com/Theycallmeholla/openai-custom-mcp.git
cd openai-custom-mcp

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create and configure .env
cp .env.example .env
# Edit .env with your settings
```

### 2. Run Locally

```bash
# Start the server
python mcp_server.py
```

### 3. Deploy to Production

```bash
# Make the deployment script executable
chmod +x deploy_complete.sh

# Run the deployment script
./deploy_complete.sh
```

## Project Structure

```
openai-custom-mcp/
├── .env                    # Local configuration (not in repo)
├── .env.example           # Configuration template
├── .gitignore            # Git ignore rules
├── deploy_complete.sh    # Complete deployment script
├── htaccess_for_server   # Apache configuration
├── mcp_server.py         # Main MCP server code
├── mcp_service.sh        # Service management script
├── requirements.txt      # Python dependencies
└── README.md             # This documentation
```

## Configuration

All configuration is done through environment variables in the `.env` file:

### Core Settings
- `MCP_API_KEY`: Authentication key for API access
- `DOMAIN`: Your domain name (for deployment)
- `SERVER_HOST`: Host to bind to (127.0.0.1 for local, 0.0.0.0 for VPS)
- `SERVER_PORT`: Port to run on (default: 8000)

### Security Settings
- `SSL_EMAIL`: Email for Let's Encrypt SSL certificates
- `RATE_LIMIT_PER_SECOND`: API rate limiting (default: 10)
- `RATE_LIMIT_BURST`: Burst rate limit (default: 20)

### Example .env for Production
```env
MCP_API_KEY=your-super-secure-api-key-here
DOMAIN=mcp.yourdomain.com
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SSL_EMAIL=admin@yourdomain.com
RATE_LIMIT_PER_SECOND=10
RATE_LIMIT_BURST=20
```

## Connecting to ChatGPT

1. **Go to ChatGPT Settings** → **Connectors** → **Add Custom Connector**

2. **Fill in the form:**
   - **Name**: `Your Knowledge Base`
   - **Description**: `Secure MCP server with company knowledge`
   - **MCP Server URL**: `https://your-domain.com` (from DOMAIN in .env)
   - **Authentication**: Add header
     - **Header Name**: `Authorization`
     - **Header Value**: `Bearer your-api-key-here` (from MCP_API_KEY in .env)

3. **Check "I trust this application"** and click **Create**

4. **Test it:**
   - Start a new chat
   - Click **Tools** → **Run deep research**
   - Select your connector
   - Ask: "What are Python best practices?"

## API Endpoints

### Health Check (No Auth Required)
```bash
GET /health
```

### MCP Tools (Requires Authorization Header)
```bash
POST /mcp/tools/list
POST /mcp/tools/call
```

## Available MCP Tools

### 1. Search Tool
Searches the knowledge base for relevant documents.

**Input:**
```json
{
  "name": "search",
  "arguments": {"query": "your search terms"}
}
```

**Output:**
```json
{
  "results": [
    {
      "id": "doc1",
      "title": "Document Title",
      "text": "Document snippet...",
      "url": "https://example.com/doc"
    }
  ]
}
```

### 2. Fetch Tool
Retrieves complete document by ID.

**Input:**
```json
{
  "name": "fetch",
  "arguments": {"id": "doc1"}
}
```

**Output:**
```json
{
  "id": "doc1",
  "title": "Document Title",
  "text": "Complete document text...",
  "url": "https://example.com/doc",
  "metadata": {"category": "programming"}
}
```

## Customizing the Knowledge Base

Edit the `SAMPLE_DATA` list in `mcp_server.py` to add your own documents:

```python
SAMPLE_DATA = [
    {
        "id": "unique-id",
        "title": "Document Title",
        "text": "Full document content here...",
        "url": "https://source-url.com",
        "metadata": {
            "category": "your-category",
            "tags": "tag1,tag2"
        }
    }
]
```

## Testing

### Local Testing
```bash
# Test locally
python test_server.py

# Manual testing
curl http://localhost:8000/health
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/mcp/tools/list
```

### Production Testing
```bash
# Test health endpoint
curl https://your-domain.com/health

# Test with authentication
curl -H "Authorization: Bearer your-api-key" https://your-domain.com/mcp/tools/list
```

## Troubleshooting

### Server Won't Start
- Check `.env` file exists and has valid values
- Ensure port isn't already in use: `lsof -i :8000`
- Check Python dependencies: `pip install -r requirements.txt`

### ChatGPT Can't Connect
- Verify server is accessible: `curl https://your-domain.com/health`
- Check API key in ChatGPT matches your `.env` file
- Ensure domain has valid SSL certificate
- Check firewall allows HTTPS traffic

### Authentication Errors
- Verify API key format: `Bearer your-api-key`
- Check API key matches in server logs
- Ensure Authorization header is properly set

## Security Features

- ✅ **API Key Authentication**: All endpoints (except health) require valid API key
- ✅ **HTTPS/SSL**: Automatic SSL setup with Let's Encrypt
- ✅ **Rate Limiting**: Configurable request rate limits
- ✅ **CORS Protection**: Configurable origin restrictions
- ✅ **Security Headers**: X-Frame-Options, HSTS, etc.
- ✅ **Access Logging**: All requests are logged

## Production Considerations

1. **Use Strong API Keys**: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. **Regular Updates**: Keep dependencies updated
3. **Monitor Logs**: `sudo journalctl -u mcp-server -f`
4. **Backup Configuration**: Keep `.env` backed up securely
5. **SSL Renewal**: Automatic with certbot, but monitor expiration

## License

MIT License - feel free to modify and use for your projects.
