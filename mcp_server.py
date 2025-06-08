#!/usr/bin/env python3
"""
MCP Server with Streamable HTTP transport for ChatGPT Deep Research
Based on OpenAI's MCP specification for remote servers
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SERVER_NAME = os.getenv("SERVER_NAME", "Local Knowledge Base")

# Sample knowledge base data
SAMPLE_DATA = [
    {
        "id": "doc1",
        "title": "Python Best Practices",
        "text": "Python best practices include using virtual environments, type hints, and docstrings. Virtual environments help isolate project dependencies, type hints improve code readability and catch errors early, and docstrings provide essential documentation for functions and classes.",
        "url": None,
        "metadata": {"category": "programming", "language": "python"}
    },
    {
        "id": "doc2", 
        "title": "FastAPI Overview",
        "text": "FastAPI is a modern web framework for building APIs with Python 3.7+. It provides automatic API documentation, type validation, and high performance through async/await support.",
        "url": None,
        "metadata": {"category": "framework", "language": "python"}
    },
    {
        "id": "doc3",
        "title": "Database Design",
        "text": "Good database design involves normalization, indexing, and proper relationships. Normalization reduces redundancy, indexes improve query performance, and proper relationships maintain data integrity.",
        "url": None,
        "metadata": {"category": "database", "topic": "design"}
    },
    {
        "id": "doc4",
        "title": "Security Guidelines", 
        "text": "Always validate input, use HTTPS, and follow the principle of least privilege. Input validation prevents injection attacks, HTTPS encrypts data in transit, and least privilege limits potential damage from breaches.",
        "url": None,
        "metadata": {"category": "security", "topic": "guidelines"}
    },
    {
        "id": "doc5",
        "title": "Testing Strategies",
        "text": "Include unit tests, integration tests, and end-to-end tests in your test suite. Unit tests verify individual components, integration tests check component interactions, and end-to-end tests validate complete workflows.",
        "url": None,
        "metadata": {"category": "testing", "topic": "strategies"}
    }
]

# Create lookup dictionary for quick access
LOOKUP = {doc["id"]: doc for doc in SAMPLE_DATA}

# Initialize FastAPI app
app = FastAPI(
    title=SERVER_NAME,
    description="MCP Server for ChatGPT Deep Research - Streamable HTTP Transport",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": SERVER_NAME,
        "description": "MCP Server for ChatGPT Deep Research",
        "version": "1.0.0",
        "protocol": "MCP-SSE",
        "transport": "server-sent-events",
        "tools": ["search", "fetch"],
        "documents": len(SAMPLE_DATA),
        "mcp_endpoint": "/mcp"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "server": SERVER_NAME,
        "timestamp": int(time.time()),
        "tools_available": 2,
        "documents": len(SAMPLE_DATA)
    }

@app.post("/mcp")
async def mcp_sse_endpoint(request: Request):
    """
    MCP SSE endpoint for ChatGPT Deep Research
    Implements proper Server-Sent Events transport as specified by OpenAI
    """
    body_bytes = await request.body()
    body_text = body_bytes.decode()
    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON body")
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    method = data.get("method")
    params = data.get("params", {})
    request_id = data.get("id")

    async def event_generator():
        try:
            logger.info(f"Method: {method}, Params: {params}, ID: {request_id}")

            if method == "initialize":
                logger.info("Processing initialize request")
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": SERVER_NAME,
                            "version": "1.0.0"
                        }
                    }
                }
                yield f"data: {json.dumps(response)}\n\n"
                await asyncio.sleep(0.1)

            elif method == "notifications/initialized":
                logger.info("Processing notifications/initialized")
                # No response needed for notifications
                return

            elif method == "tools/list":
                logger.info("Processing tools/list request")
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "search",
                                "description": "Searches for resources using the provided query string and returns matching results.",
                                "input_schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "Search query."
                                        }
                                    },
                                    "required": ["query"]
                                },
                                "output_schema": {
                                    "type": "object",
                                    "properties": {
                                        "results": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string", "description": "ID of the resource."},
                                                    "title": {"type": "string", "description": "Title or headline of the resource."},
                                                    "text": {"type": "string", "description": "Text snippet or summary from the resource."},
                                                    "url": {"type": ["string", "null"], "description": "URL of the resource. Optional but needed for citations to work."}
                                                },
                                                "required": ["id", "title", "text"]
                                            }
                                        }
                                    },
                                    "required": ["results"]
                                }
                            },
                            {
                                "name": "fetch",
                                "description": "Retrieves detailed content for a specific resource identified by the given ID.",
                                "input_schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "type": "string",
                                            "description": "ID of the resource to fetch."
                                        }
                                    },
                                    "required": ["id"]
                                },
                                "output_schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "description": "ID of the resource."},
                                        "title": {"type": "string", "description": "Title or headline of the fetched resource."},
                                        "text": {"type": "string", "description": "Complete textual content of the resource."},
                                        "url": {"type": ["string", "null"], "description": "URL of the resource. Optional but needed for citations to work."},
                                        "metadata": {
                                            "type": ["object", "null"],
                                            "additionalProperties": {"type": "string"},
                                            "description": "Optional metadata providing additional context."
                                        }
                                    },
                                    "required": ["id", "title", "text"]
                                }
                            }
                        ]
                    }
                }
                yield f"data: {json.dumps(response)}\n\n"

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                logger.info(f"Processing tools/call request for tool: {tool_name}")
                logger.info(f"Tool arguments: {arguments}")

                # Validate arguments is a dictionary (not a string)
                if not isinstance(arguments, dict):
                    logger.error(f"Invalid arguments type: {type(arguments)}. Expected dict, got {type(arguments).__name__}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Invalid params: arguments must be an object, not {type(arguments).__name__}"
                        }
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
                    return

                try:
                    if tool_name == "search":
                        # Return the raw tool result that matches the output_schema
                        result = handle_search_sse(arguments.get("query", ""))
                    elif tool_name == "fetch":
                        # Return the raw tool result that matches the output_schema
                        result = handle_fetch_sse(arguments.get("id", ""))
                    else:
                        logger.error(f"Unknown tool requested: {tool_name}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {tool_name}"
                            }
                        }
                        yield f"data: {json.dumps(error_response)}\n\n"
                        return

                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
                    return

                # Return the tool result directly as per MCP specification
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                yield f"data: {json.dumps(response)}\n\n"

            else:
                logger.error(f"Unknown method: {method}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                yield f"data: {json.dumps(error_response)}\n\n"

        except Exception as e:
            logger.error(f"Exception in SSE endpoint: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            yield f"data: {json.dumps(error_response)}\n\n"

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


def handle_search_sse(query: str) -> Dict[str, Any]:
    """Handle search tool execution for SSE - returns results in format expected by ChatGPT"""
    logger.info(f"Executing SSE search with query: '{query}'")

    query_lower = query.lower()
    results = []

    for doc in SAMPLE_DATA:
        searchable_text = (
            doc["title"].lower() + " " +
            doc["text"].lower() + " " +
            " ".join(str(v) for v in doc.get("metadata", {}).values()).lower()
        )

        if query_lower in searchable_text:
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                "url": doc.get("url")
            })

    logger.info(f"SSE Search found {len(results)} results")
    return {"results": results}

def handle_fetch_sse(doc_id: str) -> Dict[str, Any]:
    """Handle fetch tool execution for SSE"""
    logger.info(f"Executing SSE fetch with document ID: '{doc_id}'")

    if not doc_id:
        logger.warning("Empty document ID received")
        raise HTTPException(status_code=400, detail="Document ID is required")

    if doc_id not in LOOKUP:
        logger.warning(f"Document ID '{doc_id}' not found")
        raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found")

    doc = LOOKUP[doc_id]
    logger.info(f"Found document: {doc['title']}")

    return {
        "id": doc["id"],
        "title": doc["title"],
        "text": doc["text"],
        "url": doc.get("url"),
        "metadata": doc.get("metadata")
    }

# Backward compatibility functions for testing
def handle_search(query: str) -> Dict[str, Any]:
    """Handle search tool execution - for backward compatibility with tests"""
    return handle_search_sse(query)

def handle_fetch(doc_id: str) -> Dict[str, Any]:
    """Handle fetch tool execution - for backward compatibility with tests"""
    return handle_fetch_sse(doc_id)

# Legacy SSE endpoint - redirects to Streamable HTTP
@app.post("/sse")
async def mcp_sse_endpoint(request: Request):
    """SSE endpoint - redirects to Streamable HTTP for backward compatibility"""
    logger.info("Request received at /sse endpoint, redirecting to /mcp")
    return await mcp_sse_endpoint(request)

# OAuth endpoints for ChatGPT connector compatibility
@app.get("/.well-known/oauth-authorization-server")
async def oauth_config():
    """OAuth authorization server configuration"""
    base_url = "https://mcp.crsv.me"
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "registration_endpoint": f"{base_url}/oauth/register",
        "grant_types_supported": ["authorization_code"],
        "response_types_supported": ["code"],
        "scopes_supported": ["read"]
    })

@app.get("/oauth/authorize")
async def authorize_endpoint(
    response_type: str,
    client_id: str,
    redirect_uri: str = None,
    scope: str = None,
    state: str = None
):
    """OAuth authorization endpoint"""
    import secrets
    auth_code = secrets.token_urlsafe(32)
    redirect_uri_with_code = f"{redirect_uri}?code={auth_code}&state={state}"
    return RedirectResponse(url=redirect_uri_with_code)

@app.post("/oauth/register")
async def register_client(request: Request):
    """OAuth client registration endpoint"""
    return JSONResponse({
        "client_id": "mcp_client",
        "client_secret": "mcp_secret",
        "application_type": "web",
        "grant_types": ["authorization_code"],
        "scope": "read"
    })

@app.post("/oauth/token")
async def token_endpoint(request: Request):
    """OAuth token endpoint"""
    return JSONResponse({
        "access_token": "mcp_access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "read"
    })

def main():
    """Run the server"""
    print(f"🔒 Starting {SERVER_NAME}...")
    print(f"🔍 Available tools: search, fetch")
    print(f"📊 Knowledge base: {len(SAMPLE_DATA)} documents")
    print(f"✅ MCP Protocol: SSE Transport")
    print(f"🌐 MCP Endpoint: /mcp")
    print(f"🌐 Server will run on port 8000")
    
    import uvicorn
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
