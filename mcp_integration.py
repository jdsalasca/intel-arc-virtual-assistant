"""
Model Context Protocol (MCP) Integration for OpenVINO GenAI Server
Demonstrates how to integrate the local OpenVINO server with MCP.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
import aiohttp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class OpenVINOGenAIMCP:
    """MCP client for OpenVINO GenAI server."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional authentication."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health status."""
        async with self.session.get(f"{self.base_url}/healthz") as response:
            return await response.json()
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models."""
        async with self.session.get(
            f"{self.base_url}/v1/models",
            headers=self._get_headers()
        ) as response:
            return await response.json()
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """Generate chat completion."""
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if model:
            payload["model"] = model
        
        async with self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._get_headers(),
            json=payload
        ) as response:
            return await response.json()
    
    async def completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """Generate text completion."""
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if model:
            payload["model"] = model
        
        async with self.session.post(
            f"{self.base_url}/v1/completions",
            headers=self._get_headers(),
            json=payload
        ) as response:
            return await response.json()
    
    async def simple_generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """Simple generation endpoint."""
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with self.session.post(
            f"{self.base_url}/generate",
            headers=self._get_headers(),
            json=payload
        ) as response:
            return await response.json()

class OpenVINOMCPServer:
    """MCP Server that provides OpenVINO GenAI capabilities as tools."""
    
    def __init__(self, openvino_client: OpenVINOGenAIMCP):
        self.client = openvino_client
    
    async def handle_list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        return [
            {
                "name": "generate_text",
                "description": "Generate text using OpenVINO GenAI model",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The text prompt to generate from"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for generation (0.0-2.0)",
                            "default": 0.2
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens to generate",
                            "default": 256
                        }
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "chat_with_model",
                "description": "Have a conversation with the OpenVINO GenAI model",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string"},
                                    "content": {"type": "string"}
                                },
                                "required": ["role", "content"]
                            },
                            "description": "Conversation messages"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for generation (0.0-2.0)",
                            "default": 0.2
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens to generate",
                            "default": 256
                        }
                    },
                    "required": ["messages"]
                }
            },
            {
                "name": "check_model_health",
                "description": "Check the health status of the OpenVINO GenAI server",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls."""
        try:
            if name == "generate_text":
                result = await self.client.simple_generate(
                    prompt=arguments["prompt"],
                    temperature=arguments.get("temperature", 0.2),
                    max_tokens=arguments.get("max_tokens", 256)
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result["text"]
                        }
                    ]
                }
            
            elif name == "chat_with_model":
                result = await self.client.chat_completion(
                    messages=arguments["messages"],
                    temperature=arguments.get("temperature", 0.2),
                    max_tokens=arguments.get("max_tokens", 256)
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result["choices"][0]["message"]["content"]
                        }
                    ]
                }
            
            elif name == "check_model_health":
                result = await self.client.health_check()
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {name}"
                        }
                    ],
                    "isError": True
                }
        
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing tool {name}: {str(e)}"
                    }
                ],
                "isError": True
            }

# Example usage functions
async def example_direct_client():
    """Example using the MCP client directly."""
    print("🔗 Direct MCP Client Example")
    
    async with OpenVINOGenAIMCP() as client:
        # Check health
        health = await client.health_check()
        print(f"Server Health: {health}")
        
        # List models
        models = await client.list_models()
        print(f"Available Models: {models}")
        
        # Simple generation
        result = await client.simple_generate(
            prompt="Explain the benefits of local AI inference.",
            temperature=0.7,
            max_tokens=100
        )
        print(f"Generated Text: {result['text']}")
        
        # Chat completion
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What is OpenVINO and why is it useful?"}
        ]
        chat_result = await client.chat_completion(messages=messages)
        print(f"Chat Response: {chat_result['choices'][0]['message']['content']}")

async def example_mcp_server():
    """Example demonstrating MCP server functionality."""
    print("\n🛠️  MCP Server Example")
    
    async with OpenVINOGenAIMCP() as client:
        server = OpenVINOMCPServer(client)
        
        # List tools
        tools = await server.handle_list_tools()
        print(f"Available Tools: {[tool['name'] for tool in tools]}")
        
        # Test generate_text tool
        result = await server.handle_call_tool(
            "generate_text",
            {
                "prompt": "Write a haiku about artificial intelligence.",
                "temperature": 0.8,
                "max_tokens": 50
            }
        )
        print(f"Generated Haiku: {result['content'][0]['text']}")
        
        # Test chat_with_model tool
        chat_result = await server.handle_call_tool(
            "chat_with_model",
            {
                "messages": [
                    {"role": "user", "content": "What are the advantages of running AI models locally?"}
                ],
                "temperature": 0.5
            }
        )
        print(f"Chat Response: {chat_result['content'][0]['text']}")

async def main():
    """Main example function."""
    print("🚀 OpenVINO GenAI MCP Integration Examples")
    print("Make sure your OpenVINO GenAI server is running on http://localhost:8000")
    
    try:
        # Test server connectivity
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/healthz", timeout=5) as response:
                if response.status == 200:
                    print("✅ Server is running!")
                    
                    await example_direct_client()
                    await example_mcp_server()
                    
                else:
                    print("❌ Server is not responding correctly")
                    
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to server. Please start the server first:")
        print("   python start_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())