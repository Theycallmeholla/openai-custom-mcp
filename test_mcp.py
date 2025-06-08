#!/usr/bin/env python3
"""
Quick test to verify MCP protocol implementation
"""

import json
import requests

def test_mcp_initialize():
    """Test the MCP initialize handshake"""
    url = "http://localhost:8000/mcp"
    
    # Test initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    print("Testing initialize...")
    response = requests.post(url, json=init_request, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        content = response.text
        print("Initialize response:")
        print(content)
        print()
        
        # Parse the SSE response
        if "data: " in content:
            data_line = [line for line in content.split('\n') if line.startswith('data: ')][0]
            json_data = data_line[6:]  # Remove "data: " prefix
            parsed = json.loads(json_data)
            print("Parsed response:")
            print(json.dumps(parsed, indent=2))
            print()
            
            # Check if response has required fields
            result = parsed.get("result", {})
            if "protocolVersion" in result and "capabilities" in result and "serverInfo" in result:
                print("✅ Initialize response has all required fields!")
                print(f"   Protocol Version: {result['protocolVersion']}")
                print(f"   Capabilities: {result['capabilities']}")
                print(f"   Server Info: {result['serverInfo']}")
            else:
                print("❌ Initialize response missing required fields")
                print(f"   Has protocolVersion: {'protocolVersion' in result}")
                print(f"   Has capabilities: {'capabilities' in result}")
                print(f"   Has serverInfo: {'serverInfo' in result}")
        else:
            print("❌ No SSE data found in response")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)

def test_tools_list():
    """Test tools/list method"""
    url = "http://localhost:8000/mcp"
    
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    print("Testing tools/list...")
    response = requests.post(url, json=tools_request, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        content = response.text
        print("Tools list response:")
        print(content[:500] + "..." if len(content) > 500 else content)
        print()
    else:
        print(f"❌ Request failed: {response.status_code}")

if __name__ == "__main__":
    print("🧪 Testing MCP Server Implementation\n")
    test_mcp_initialize()
    print("-" * 50)
    test_tools_list()
