#!/usr/bin/env python3
"""
Secure MCP Server with environment-based configuration
"""

import os
import json
import uvicorn
import secrets
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configuration from environment
API_KEY = os.getenv("MCP_API_KEY", "dev-key-local-testing-only")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
SERVER_NAME = os.getenv("SERVER_NAME", "Knowledge Base")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Sample knowledge base data
SAMPLE_DATA = [
    {
        "id": "doc1",
        "title": "Python Best Practices",
        "text": "Python best practices include using virtual environments, type hints, and docstrings."
    },
    {
        "id": "doc2",
        "title": "FastAPI Overview",
        "text": "FastAPI is a modern web framework for building APIs with Python 3.7+."
    },
    {
        "id": "doc3",
        "title": "Database Design",
        "text": "Good database design involves normalization, indexing, and proper relationships."
    },
    {
        "id": "doc4",
        "title": "Security Guidelines",
        "text": "Always validate input, use HTTPS, and follow the principle of least privilege."
    },
    {
        "id": "doc5",
        "title": "Testing Strategies",
        "text": "Include unit tests, integration tests, and end-to-end tests in your test suite."
    }
]

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    
class FetchRequest(BaseModel):
    doc_id: str

class ToolResponse(BaseModel):
    result: str
    status: str = "success"

class MCPResponse(BaseModel):
    tools: List[Dict[str, Any]]

# FastAPI app
app = FastAPI(
    title=SERVER_NAME,
    description="MCP-compatible Knowledge Base Server",
    version="1.0.0",
    root_path="/mcp"  # Add this line!
)

# Security
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """Verify the API key"""
    if API_KEY == "dev-key-local-testing-only":
        return True  # Skip validation in dev mode
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": SERVER_NAME,
        "version": "1.0.0",
        "status": "running",
        "tools": ["search", "fetch"],
        "documents": len(SAMPLE_DATA)
    }

@app.get("/tools", response_model=MCPResponse)
async def list_tools(authorized: bool = Depends(verify_api_key)):
    """List available MCP tools"""
    tools = [
        {
            "name": "search",
            "description": "Search the knowledge base for relevant documents",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "fetch",
            "description": "Fetch a specific document by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "Document ID to fetch"
                    }
                },
                "required": ["doc_id"]
            }
        }
    ]
    return MCPResponse(tools=tools)

@app.post("/tools/search", response_model=ToolResponse)
async def search_tool(request: SearchRequest, authorized: bool = Depends(verify_api_key)):
    """Search the knowledge base for relevant documents"""
    query = request.query
    results = []
    
    for doc in SAMPLE_DATA:
        if query.lower() in doc["title"].lower() or query.lower() in doc["text"].lower():
            results.append(doc)
    
    if not results:
        return ToolResponse(result="No matching documents found.")
    
    formatted_results = []
    for doc in results:
        formatted_results.append(f"Title: {doc['title']}\nContent: {doc['text']}\n")
    
    result = "\n".join(formatted_results)
    return ToolResponse(result=result)

@app.post("/tools/fetch", response_model=ToolResponse)
async def fetch_tool(request: FetchRequest, authorized: bool = Depends(verify_api_key)):
    """Fetch a specific document by ID"""
    doc_id = request.doc_id
    doc = next((doc for doc in SAMPLE_DATA if doc["id"] == doc_id), None)
    
    if not doc:
        return ToolResponse(
            result=f"Document {doc_id} not found.",
            status="error"
        )
    
    result = f"Title: {doc['title']}\nContent: {doc['text']}"
    return ToolResponse(result=result)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-06-08"}

@app.post("/sse")
async def sse_endpoint(request: Request, authorized: bool = Depends(verify_api_key)):
    """SSE endpoint for ChatGPT integration"""
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            # Process any incoming messages
            if await request.body():
                body = await request.json()
                tool_name = body.get("name")
                arguments = body.get("arguments", {})
                
                # Handle tool calls
                if tool_name == "search":
                    result = await search_tool(SearchRequest(query=arguments.get("query", "")))
                elif tool_name == "fetch":
                    result = await fetch_tool(FetchRequest(doc_id=arguments.get("doc_id", "")))
                else:
                    result = ToolResponse(result="Unknown tool", status="error")
                
                # Send the result
                yield f"data: {json.dumps(result.dict())}\n\n"
            
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )

def main():
    """Run the server"""
    if API_KEY == "dev-key-local-testing-only":
        new_api_key = secrets.token_urlsafe(32)
        print("⚠️  WARNING: Using development mode - API key validation disabled")
        print(f"🔑 Generated API Key: {new_api_key}")
        print("💡 Update MCP_API_KEY in .env file for production")
    
    print(f"🔒 Starting {SERVER_NAME}...")
    print(f"🔍 Available tools: search, fetch")
    print(f"📊 Knowledge base: {len(SAMPLE_DATA)} documents")
    print(f"🌐 Server will run on http://{SERVER_HOST}:{SERVER_PORT}")
    
    uvicorn.run(
        "mcp_server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level=LOG_LEVEL.lower(),
        reload=False
    )

if __name__ == "__main__":
    main()
