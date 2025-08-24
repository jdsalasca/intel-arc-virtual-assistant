"""
Tool Provider for Intel Virtual Assistant Backend
Implements extensible tool system for web search, Gmail, and other integrations.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from ..interfaces.providers import IToolProvider

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
        self.usage_count = 0
        
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema for this tool."""
        pass


class WebSearchTool(BaseTool):
    """Tool for web search functionality."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="web_search",
            description="Search the web for current information"
        )
        self._api_key = api_key
        self._search_engine = "bing"  # Default to Bing
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute web search."""
        try:
            query = parameters.get("query", "")
            max_results = parameters.get("max_results", 5)
            
            if not query:
                raise ValueError("Query parameter is required")
            
            logger.info(f"Searching web for: {query}")
            
            # Simulate web search (in real implementation, use actual search API)
            results = await self._perform_search(query, max_results)
            
            self.usage_count += 1
            return {
                "query": query,
                "results": results,
                "total_results": len(results),
                "source": "web_search"
            }
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            raise
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for web search."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                    "required": True
                },
                "max_results": {
                    "type": "integer", 
                    "description": "Maximum number of results",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
    
    async def _perform_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform actual web search."""
        # Placeholder implementation
        # Real implementation would use Bing Search API, Google Custom Search, etc.
        
        await asyncio.sleep(0.5)  # Simulate API call
        
        return [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a search result snippet for query '{query}'. Contains relevant information about the topic.",
                "rank": i + 1
            }
            for i in range(min(max_results, 5))
        ]


class GmailTool(BaseTool):
    """Tool for Gmail integration."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        super().__init__(
            name="gmail",
            description="Access Gmail for reading emails and basic operations"
        )
        self._credentials_path = credentials_path
        self._authenticated = False
        self._service = None
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute Gmail operation."""
        try:
            operation = parameters.get("operation", "list_emails")
            
            if not self._authenticated:
                await self._authenticate()
            
            if operation == "list_emails":
                return await self._list_emails(parameters)
            elif operation == "read_email":
                return await self._read_email(parameters)
            elif operation == "search_emails":
                return await self._search_emails(parameters)
            else:
                raise ValueError(f"Unknown Gmail operation: {operation}")
                
        except Exception as e:
            logger.error(f"Gmail operation error: {e}")
            raise
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for Gmail."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list_emails", "read_email", "search_emails"],
                    "description": "Gmail operation to perform",
                    "default": "list_emails"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of emails to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "email_id": {
                    "type": "string",
                    "description": "Email ID for read_email operation"
                },
                "search_query": {
                    "type": "string", 
                    "description": "Search query for search_emails operation"
                }
            }
        }
    
    async def _authenticate(self):
        """Authenticate with Gmail API."""
        # Placeholder for Gmail authentication
        logger.info("Authenticating with Gmail")
        await asyncio.sleep(0.2)
        self._authenticated = True
    
    async def _list_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List recent emails."""
        limit = parameters.get("limit", 10)
        
        # Placeholder implementation
        emails = [
            {
                "id": f"email_{i}",
                "subject": f"Email Subject {i+1}",
                "sender": f"sender{i+1}@example.com",
                "date": f"2024-08-{24-i:02d}",
                "preview": f"This is a preview of email {i+1}..."
            }
            for i in range(min(limit, 10))
        ]
        
        self.usage_count += 1
        return {
            "emails": emails,
            "total": len(emails),
            "operation": "list_emails"
        }
    
    async def _read_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Read a specific email."""
        email_id = parameters.get("email_id")
        if not email_id:
            raise ValueError("email_id is required for read_email operation")
        
        # Placeholder implementation
        email = {
            "id": email_id,
            "subject": "Email Subject",
            "sender": "sender@example.com",
            "date": "2024-08-24",
            "body": "This is the full email body content...",
            "attachments": []
        }
        
        self.usage_count += 1
        return {
            "email": email,
            "operation": "read_email"
        }
    
    async def _search_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search emails."""
        search_query = parameters.get("search_query")
        limit = parameters.get("limit", 10)
        
        if not search_query:
            raise ValueError("search_query is required for search_emails operation")
        
        # Placeholder implementation
        emails = [
            {
                "id": f"search_result_{i}",
                "subject": f"Email matching '{search_query}' - {i+1}",
                "sender": f"sender{i+1}@example.com",
                "date": f"2024-08-{24-i:02d}",
                "preview": f"Email containing '{search_query}' keywords..."
            }
            for i in range(min(limit, 5))
        ]
        
        self.usage_count += 1
        return {
            "emails": emails,
            "query": search_query,
            "total": len(emails),
            "operation": "search_emails"
        }


class SystemInfoTool(BaseTool):
    """Tool for getting system information."""
    
    def __init__(self):
        super().__init__(
            name="system_info",
            description="Get system information and hardware details"
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Get system information."""
        try:
            info_type = parameters.get("type", "overview")
            
            if info_type == "overview":
                return await self._get_system_overview()
            elif info_type == "hardware":
                return await self._get_hardware_info()
            elif info_type == "performance":
                return await self._get_performance_info()
            else:
                raise ValueError(f"Unknown info type: {info_type}")
                
        except Exception as e:
            logger.error(f"System info error: {e}")
            raise
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for system info."""
        return {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["overview", "hardware", "performance"],
                    "description": "Type of system information",
                    "default": "overview"
                }
            }
        }
    
    async def _get_system_overview(self) -> Dict[str, Any]:
        """Get system overview."""
        import platform
        import psutil
        
        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "cpu_cores": psutil.cpu_count(),
            "type": "overview"
        }
    
    async def _get_hardware_info(self) -> Dict[str, Any]:
        """Get detailed hardware information."""
        import psutil
        
        return {
            "cpu": {
                "cores": psutil.cpu_count(),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2)
            },
            "type": "hardware"
        }
    
    async def _get_performance_info(self) -> Dict[str, Any]:
        """Get performance information."""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None,
            "type": "performance"
        }


class ToolProvider(IToolProvider):
    """Main tool provider implementing the tool system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize tool provider."""
        self._config = config or {}
        self._tools: Dict[str, BaseTool] = {}
        self._tool_stats: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> bool:
        """Initialize the tool provider."""
        try:
            logger.info("Initializing tool provider")
            
            # Initialize built-in tools
            await self._initialize_builtin_tools()
            
            logger.info(f"Tool provider initialized with {len(self._tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize tool provider: {e}")
            return False
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool."""
        try:
            if tool_name not in self._tools:
                raise ValueError(f"Tool '{tool_name}' not found")
            
            tool = self._tools[tool_name]
            
            if not tool.enabled:
                raise ValueError(f"Tool '{tool_name}' is disabled")
            
            # Execute tool
            result = await tool.execute(parameters)
            
            # Update statistics
            await self._update_tool_stats(tool_name, True)
            
            return result
            
        except Exception as e:
            await self._update_tool_stats(tool_name, False)
            logger.error(f"Tool execution error for {tool_name}: {e}")
            raise
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        tools = []
        
        for name, tool in self._tools.items():
            stats = self._tool_stats.get(name, {})
            
            tool_info = {
                "name": name,
                "description": tool.description,
                "enabled": tool.enabled,
                "parameters": tool.get_parameters_schema(),
                "usage_count": tool.usage_count,
                "success_rate": stats.get("success_rate", 0.0),
                "category": self._get_tool_category(name)
            }
            tools.append(tool_info)
        
        return tools
    
    async def can_handle_tool(self, tool_name: str) -> bool:
        """Check if provider can handle a tool."""
        return tool_name in self._tools
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool."""
        if tool_name not in self._tools:
            return None
        
        tool = self._tools[tool_name]
        stats = self._tool_stats.get(tool_name, {})
        
        return {
            "name": tool_name,
            "description": tool.description,
            "enabled": tool.enabled,
            "parameters": tool.get_parameters_schema(),
            "usage_count": tool.usage_count,
            "statistics": stats,
            "category": self._get_tool_category(tool_name)
        }
    
    async def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool."""
        if tool_name in self._tools:
            self._tools[tool_name].enabled = True
            return True
        return False
    
    async def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool."""
        if tool_name in self._tools:
            self._tools[tool_name].enabled = False
            return True
        return False
    
    # Private helper methods
    
    async def _initialize_builtin_tools(self):
        """Initialize built-in tools."""
        # Web search tool
        web_search_key = self._config.get("web_search_api_key")
        self._tools["web_search"] = WebSearchTool(web_search_key)
        
        # Gmail tool
        gmail_creds = self._config.get("gmail_credentials_path")
        self._tools["gmail"] = GmailTool(gmail_creds)
        
        # System info tool
        self._tools["system_info"] = SystemInfoTool()
        
        # Initialize tool statistics
        for tool_name in self._tools.keys():
            self._tool_stats[tool_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "last_execution": None
            }
    
    async def _update_tool_stats(self, tool_name: str, success: bool):
        """Update tool execution statistics."""
        if tool_name not in self._tool_stats:
            self._tool_stats[tool_name] = {
                "total_executions": 0,
                "successful_executions": 0, 
                "failed_executions": 0,
                "success_rate": 0.0,
                "last_execution": None
            }
        
        stats = self._tool_stats[tool_name]
        stats["total_executions"] += 1
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        stats["success_rate"] = (
            stats["successful_executions"] / stats["total_executions"]
            if stats["total_executions"] > 0 else 0.0
        )
        
        from datetime import datetime
        stats["last_execution"] = datetime.now().isoformat()
    
    def _get_tool_category(self, tool_name: str) -> str:
        """Get category for a tool."""
        categories = {
            "web_search": "information",
            "gmail": "communication",
            "system_info": "system"
        }
        return categories.get(tool_name, "general")