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
from fastapi.responses import StreamingResponse, JSONResponse
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

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]

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
    version="1.0.0"
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
        "actions": ["search"],
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

@app.get("/.well-known/mcp.json")
async def mcp_config():
    """MCP configuration endpoint"""
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "MCP Knowledge Base",
        "name_for_model": "mcp_knowledge_base",
        "description_for_human": "Search through the knowledge base",
        "description_for_model": "Use this to search through documents in the knowledge base",
        "auth": {
            "type": "oauth",
            "client_url": "https://mcp.crsv.me/oauth/register",
            "scope": "search",
            "authorization_url": "https://mcp.crsv.me/oauth/authorize",
            "token_url": "https://mcp.crsv.me/oauth/token"
        },
        "api": {
            "type": "openapi",
            "url": "https://mcp.crsv.me/.well-known/openapi.json"
        },
        "actions": [{
            "name": "search",
            "description": "Search through the knowledge base",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }]
    })

@app.get("/.well-known/openapi.json")
async def openapi_spec():
    """OpenAPI specification"""
    return JSONResponse({
        "openapi": "3.0.1",
        "info": {
            "title": "MCP Knowledge Base API",
            "version": "v1"
        },
        "paths": {
            "/search": {
                "post": {
                    "operationId": "search",
                    "summary": "Search through the knowledge base",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The search query"
                                        }
                                    },
                                    "required": ["query"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "results": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "string"},
                                                        "title": {"type": "string"},
                                                        "text": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    })

@app.post("/search")
async def search(request: SearchRequest, authorized: bool = Depends(verify_api_key)):
    """Search the knowledge base"""
    query = request.query.lower()
    results = []
    
    for doc in SAMPLE_DATA:
        if query in doc["title"].lower() or query in doc["text"].lower():
            results.append(doc)
    
    return SearchResponse(results=results)

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
            try:
                body = await request.json()
                tool_name = body.get("name")
                arguments = body.get("arguments", {})
                
                # Handle tool calls
                if tool_name == "search":
                    result = await search(SearchRequest(query=arguments.get("query", "")))
                elif tool_name == "fetch":
                    result = await fetch_tool(FetchRequest(doc_id=arguments.get("doc_id", "")))
                else:
                    result = ToolResponse(result="Unknown tool", status="error")
                
                # Send the result
                yield f"data: {json.dumps(result.dict())}\n\n"
            except:
                # Keep connection alive even if no message
                yield f"data: {json.dumps({'status': 'alive'})}\n\n"
            
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

@app.get("/oauth/authorize")
async def authorize_endpoint(
    response_type: str,
    client_id: str,
    redirect_uri: str = None,
    scope: str = None,
    state: str = None
):
    """OAuth authorization endpoint"""
    if response_type == "code":
        auth_code = secrets.token_urlsafe(32)
        return JSONResponse({
            "code": auth_code,
            "state": state
        })
    else:
        return JSONResponse({
            "access_token": API_KEY,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "tools.read tools.write",
            "state": state
        })

@app.post("/oauth/register")
async def register_client(request: Request):
    """OAuth client registration endpoint"""
    try:
        body = await request.json()
        return JSONResponse({
            "client_id": "mcp_client",
            "client_secret": API_KEY,
            "client_id_issued_at": 1683000000,
            "client_secret_expires_at": 0,
            "application_type": "web",
            "grant_types": ["client_credentials"],
            "token_endpoint_auth_method": "none",
            "scope": "tools.read tools.write"
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid request")

@app.post("/oauth/token")
async def token_endpoint(request: Request):
    """OAuth token endpoint"""
    return JSONResponse({
        "access_token": API_KEY,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "tools.read tools.write"
    })

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
