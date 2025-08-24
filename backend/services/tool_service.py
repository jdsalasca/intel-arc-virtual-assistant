"""
Tool Service Implementation for Intel Virtual Assistant Backend
Handles tool execution and management for extensible functionality.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import time

from ..interfaces.services import IToolService
from ..interfaces.providers import IToolProvider
from ..models.domain import ToolResult

logger = logging.getLogger(__name__)


class ToolService(IToolService):
    """Service for managing and executing tools."""

    def __init__(self, tool_providers: Optional[List[IToolProvider]] = None):
        """Initialize tool service with optional providers."""
        self._tool_providers: List[IToolProvider] = tool_providers or []
        self._registered_tools: Dict[str, Dict[str, Any]] = {}
        self._tool_handlers: Dict[str, Callable] = {}
        self._execution_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute a tool with given parameters."""
        start_time = time.time()
        
        try:
            logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
            
            # Validate tool exists
            if tool_name not in self._registered_tools:
                raise ValueError(f"Tool '{tool_name}' is not registered")

            # Get tool configuration
            tool_config = self._registered_tools[tool_name]
            
            # Validate parameters
            await self._validate_parameters(tool_name, parameters)

            # Find appropriate provider or handler
            result = None
            if tool_name in self._tool_handlers:
                # Use local handler
                handler = self._tool_handlers[tool_name]
                result = await self._execute_local_handler(handler, parameters)
            else:
                # Use provider
                provider = await self._find_tool_provider(tool_name)
                if not provider:
                    raise ValueError(f"No provider found for tool '{tool_name}'")
                
                result = await provider.execute_tool(tool_name, parameters)

            execution_time = time.time() - start_time

            # Create tool result
            tool_result = ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "parameters_count": len(parameters),
                    "provider": tool_config.get("provider", "local")
                }
            )

            # Update execution statistics
            await self._update_execution_stats(tool_name, execution_time, True)

            logger.info(f"Tool {tool_name} executed successfully in {execution_time:.2f}s")
            return tool_result

        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            
            # Update execution statistics
            await self._update_execution_stats(tool_name, execution_time, False)

            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                execution_time=execution_time,
                error=str(e),
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "error_type": type(e).__name__
                }
            )

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        try:
            tools = []
            
            # Add registered tools
            for tool_name, config in self._registered_tools.items():
                stats = self._execution_stats.get(tool_name, {})
                
                tool_info = {
                    "name": tool_name,
                    "description": config.get("description", ""),
                    "parameters": config.get("parameters", {}),
                    "category": config.get("category", "general"),
                    "provider": config.get("provider", "local"),
                    "enabled": config.get("enabled", True),
                    "statistics": {
                        "total_executions": stats.get("total_executions", 0),
                        "success_rate": stats.get("success_rate", 0.0),
                        "average_execution_time": stats.get("average_execution_time", 0.0),
                        "last_execution": stats.get("last_execution")
                    }
                }
                tools.append(tool_info)

            # Add tools from providers
            for provider in self._tool_providers:
                provider_tools = await provider.get_available_tools()
                for tool in provider_tools:
                    if tool["name"] not in self._registered_tools:
                        tools.append(tool)

            return tools

        except Exception as e:
            logger.error(f"Error getting available tools: {str(e)}")
            return []

    async def register_tool(
        self, tool_name: str, tool_handler: Any
    ) -> bool:
        """Register a new tool."""
        try:
            async with self._lock:
                logger.info(f"Registering tool: {tool_name}")

                # Validate tool name
                if not tool_name or not isinstance(tool_name, str):
                    raise ValueError("Tool name must be a non-empty string")

                # Extract tool configuration
                if hasattr(tool_handler, '__dict__'):
                    # Handler is a class/object with metadata
                    config = {
                        "description": getattr(tool_handler, "description", ""),
                        "parameters": getattr(tool_handler, "parameters", {}),
                        "category": getattr(tool_handler, "category", "general"),
                        "provider": "local",
                        "enabled": True
                    }
                    
                    # Store the actual handler method
                    if hasattr(tool_handler, "execute"):
                        self._tool_handlers[tool_name] = tool_handler.execute
                    elif callable(tool_handler):
                        self._tool_handlers[tool_name] = tool_handler
                    else:
                        raise ValueError("Tool handler must be callable or have an 'execute' method")
                        
                elif callable(tool_handler):
                    # Handler is a simple function
                    config = {
                        "description": getattr(tool_handler, "__doc__", ""),
                        "parameters": {},
                        "category": "general",
                        "provider": "local",
                        "enabled": True
                    }
                    self._tool_handlers[tool_name] = tool_handler
                else:
                    raise ValueError("Tool handler must be callable")

                # Register the tool
                self._registered_tools[tool_name] = config
                
                # Initialize statistics
                self._execution_stats[tool_name] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "success_rate": 0.0,
                    "total_execution_time": 0.0,
                    "average_execution_time": 0.0,
                    "last_execution": None
                }

                logger.info(f"Successfully registered tool: {tool_name}")
                return True

        except Exception as e:
            logger.error(f"Error registering tool {tool_name}: {str(e)}")
            return False

    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        try:
            async with self._lock:
                logger.info(f"Unregistering tool: {tool_name}")

                if tool_name not in self._registered_tools:
                    logger.warning(f"Tool {tool_name} is not registered")
                    return True

                # Remove tool
                del self._registered_tools[tool_name]
                
                if tool_name in self._tool_handlers:
                    del self._tool_handlers[tool_name]
                
                if tool_name in self._execution_stats:
                    del self._execution_stats[tool_name]

                logger.info(f"Successfully unregistered tool: {tool_name}")
                return True

        except Exception as e:
            logger.error(f"Error unregistering tool {tool_name}: {str(e)}")
            return False

    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool."""
        try:
            if tool_name not in self._registered_tools:
                return None

            config = self._registered_tools[tool_name]
            stats = self._execution_stats.get(tool_name, {})

            return {
                "name": tool_name,
                "description": config.get("description", ""),
                "parameters": config.get("parameters", {}),
                "category": config.get("category", "general"),
                "provider": config.get("provider", "local"),
                "enabled": config.get("enabled", True),
                "statistics": stats,
                "last_updated": config.get("last_updated")
            }

        except Exception as e:
            logger.error(f"Error getting tool info for {tool_name}: {str(e)}")
            return None

    async def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool."""
        try:
            if tool_name not in self._registered_tools:
                return False

            self._registered_tools[tool_name]["enabled"] = True
            logger.info(f"Enabled tool: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"Error enabling tool {tool_name}: {str(e)}")
            return False

    async def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool."""
        try:
            if tool_name not in self._registered_tools:
                return False

            self._registered_tools[tool_name]["enabled"] = False
            logger.info(f"Disabled tool: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"Error disabling tool {tool_name}: {str(e)}")
            return False

    async def get_execution_statistics(self) -> Dict[str, Any]:
        """Get overall tool execution statistics."""
        try:
            total_executions = sum(
                stats.get("total_executions", 0) 
                for stats in self._execution_stats.values()
            )
            
            total_success = sum(
                stats.get("successful_executions", 0) 
                for stats in self._execution_stats.values()
            )
            
            overall_success_rate = (
                total_success / total_executions 
                if total_executions > 0 else 0.0
            )

            return {
                "total_tools": len(self._registered_tools),
                "enabled_tools": sum(
                    1 for config in self._registered_tools.values() 
                    if config.get("enabled", True)
                ),
                "total_executions": total_executions,
                "successful_executions": total_success,
                "overall_success_rate": overall_success_rate,
                "tool_statistics": self._execution_stats
            }

        except Exception as e:
            logger.error(f"Error getting execution statistics: {str(e)}")
            return {}

    async def _validate_parameters(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> None:
        """Validate tool parameters."""
        tool_config = self._registered_tools[tool_name]
        required_params = tool_config.get("parameters", {})
        
        # Check if tool is enabled
        if not tool_config.get("enabled", True):
            raise ValueError(f"Tool '{tool_name}' is disabled")

        # Validate required parameters (basic validation)
        for param_name, param_config in required_params.items():
            if param_config.get("required", False) and param_name not in parameters:
                raise ValueError(f"Required parameter '{param_name}' missing for tool '{tool_name}'")

    async def _find_tool_provider(self, tool_name: str) -> Optional[IToolProvider]:
        """Find a provider that can handle the specified tool."""
        for provider in self._tool_providers:
            if await provider.can_handle_tool(tool_name):
                return provider
        return None

    async def _execute_local_handler(
        self, handler: Callable, parameters: Dict[str, Any]
    ) -> Any:
        """Execute a local tool handler."""
        if asyncio.iscoroutinefunction(handler):
            return await handler(**parameters)
        else:
            # Run synchronous handler in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: handler(**parameters))

    async def _update_execution_stats(
        self, tool_name: str, execution_time: float, success: bool
    ) -> None:
        """Update execution statistics for a tool."""
        try:
            async with self._lock:
                if tool_name not in self._execution_stats:
                    self._execution_stats[tool_name] = {
                        "total_executions": 0,
                        "successful_executions": 0,
                        "failed_executions": 0,
                        "success_rate": 0.0,
                        "total_execution_time": 0.0,
                        "average_execution_time": 0.0,
                        "last_execution": None
                    }

                stats = self._execution_stats[tool_name]
                
                # Update counters
                stats["total_executions"] += 1
                if success:
                    stats["successful_executions"] += 1
                else:
                    stats["failed_executions"] += 1

                # Update timing
                stats["total_execution_time"] += execution_time
                stats["average_execution_time"] = (
                    stats["total_execution_time"] / stats["total_executions"]
                )

                # Update success rate
                stats["success_rate"] = (
                    stats["successful_executions"] / stats["total_executions"]
                )

                # Update last execution timestamp
                stats["last_execution"] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Error updating execution stats: {str(e)}")