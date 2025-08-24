"""
Tool Registry Service
Manages external tool integrations and execution.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Type
from datetime import datetime
import inspect

from core.interfaces.tool_provider import (
    IToolProvider, IToolRegistry, ToolCategory, ToolResult, 
    ToolParameter, ToolDefinition
)
from core.models.tool import (
    ToolRequest, ToolExecution, ToolUsageStats, 
    ToolConfiguration, ToolStatus
)
from core.exceptions import (
    ToolException, ToolNotFound, ToolExecutionException, 
    ToolAuthenticationException, ToolTimeoutException
)

logger = logging.getLogger(__name__)

class ToolRegistry(IToolRegistry):
    """Registry for managing and executing tools."""
    
    def __init__(self):
        self._tools: Dict[str, IToolProvider] = {}
        self._tool_configs: Dict[str, ToolConfiguration] = {}
        self._executions: Dict[str, ToolExecution] = {}
        self._usage_stats: Dict[str, ToolUsageStats] = {}
        
        # Built-in tools will be registered during initialization
        self._builtin_tools = []
    
    def register_tool(self, tool: IToolProvider) -> bool:
        """Register a new tool."""
        try:
            tool_name = tool.get_tool_name()
            
            # Validate tool
            if not self._validate_tool(tool):
                raise ToolException(f"Tool {tool_name} failed validation")
            
            # Register tool
            self._tools[tool_name] = tool
            
            # Initialize usage stats
            if tool_name not in self._usage_stats:
                self._usage_stats[tool_name] = ToolUsageStats(tool_name=tool_name)
            
            logger.info(f"Registered tool: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool: {e}")
            return False
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        try:
            if tool_name in self._tools:
                del self._tools[tool_name]
                logger.info(f"Unregistered tool: {tool_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_name}: {e}")
            return False
    
    def get_tool(self, tool_name: str) -> Optional[IToolProvider]:
        """Get a tool by name."""
        return self._tools.get(tool_name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[IToolProvider]:
        """List available tools."""
        tools = list(self._tools.values())
        
        if category:
            tools = [tool for tool in tools if tool.get_tool_category() == category]
        
        return tools
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user_id: str = "system") -> ToolResult:
        """Execute a tool by name."""
        try:
            # Get tool
            tool = self._tools.get(tool_name)
            if not tool:
                raise ToolNotFound(f"Tool {tool_name} not found")
            
            # Check if tool is available
            if not tool.is_available():
                raise ToolExecutionException(f"Tool {tool_name} is not available")
            
            # Create tool request
            request = ToolRequest(
                tool_name=tool_name,
                parameters=parameters,
                user_id=user_id
            )
            
            # Create execution tracking
            execution = ToolExecution(
                tool_name=tool_name,
                request=request,
                status=ToolStatus.PENDING
            )
            execution.started_at = datetime.utcnow()
            execution.status = ToolStatus.RUNNING
            
            self._executions[request.id] = execution
            
            try:
                # Validate parameters
                if not tool.validate_parameters(parameters):
                    raise ToolExecutionException(f"Invalid parameters for tool {tool_name}")
                
                # Execute tool
                execution.add_log(f"Starting execution with parameters: {parameters}")
                result = tool.execute(parameters)
                
                # Update execution
                execution.completed_at = datetime.utcnow()
                execution.result = result
                
                if result.success:
                    execution.status = ToolStatus.COMPLETED
                    execution.add_log("Execution completed successfully")
                else:
                    execution.status = ToolStatus.FAILED
                    execution.add_log(f"Execution failed: {result.error}")
                
                # Update usage stats
                self._update_usage_stats(tool_name, execution, result)
                
                logger.info(f"Tool {tool_name} executed successfully")
                return result
                
            except Exception as e:
                execution.status = ToolStatus.FAILED
                execution.completed_at = datetime.utcnow()
                execution.add_log(f"Execution error: {str(e)}")
                
                error_result = ToolResult(
                    request_id=request.id,
                    tool_name=tool_name,
                    status=ToolStatus.FAILED,
                    success=False,
                    error=str(e)
                )
                execution.result = error_result
                
                raise ToolExecutionException(f"Tool execution failed: {e}")
                
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {e}")
            
            # Return error result
            return ToolResult(
                request_id="error",
                tool_name=tool_name,
                status=ToolStatus.FAILED,
                success=False,
                error=str(e)
            )
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get the schema for a tool."""
        tool = self._tools.get(tool_name)
        if not tool:
            raise ToolNotFound(f"Tool {tool_name} not found")
        
        parameters = tool.get_parameters()
        
        schema = {
            "name": tool.get_tool_name(),
            "description": tool.get_tool_description(),
            "category": tool.get_tool_category().value,
            "auth_type": tool.get_auth_type().value,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        for param in parameters:
            schema["parameters"]["properties"][param.name] = {
                "type": param.type.value,
                "description": param.description
            }
            
            if param.default is not None:
                schema["parameters"]["properties"][param.name]["default"] = param.default
            
            if param.enum_values:
                schema["parameters"]["properties"][param.name]["enum"] = param.enum_values
                
            if param.required:
                schema["parameters"]["required"].append(param.name)
        
        return schema
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all available tools."""
        return [self.get_tool_schema(name) for name in self._tools.keys()]
    
    def _validate_tool(self, tool: IToolProvider) -> bool:
        """Validate a tool before registration."""
        try:
            # Check required methods
            required_methods = ['get_tool_name', 'get_tool_description', 'get_tool_category', 'execute']
            for method in required_methods:
                if not hasattr(tool, method) or not callable(getattr(tool, method)):
                    logger.error(f"Tool missing required method: {method}")
                    return False
            
            # Check tool name is valid
            name = tool.get_tool_name()
            if not name or not isinstance(name, str) or len(name.strip()) == 0:
                logger.error("Tool name is invalid")
                return False
            
            # Check if already registered
            if name in self._tools:
                logger.warning(f"Tool {name} is already registered")
                return False
            
            # Validate parameters
            try:
                parameters = tool.get_parameters()
                if not isinstance(parameters, list):
                    logger.error("Tool parameters must be a list")
                    return False
            except Exception as e:
                logger.error(f"Error getting tool parameters: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Tool validation failed: {e}")
            return False
    
    def _update_usage_stats(self, tool_name: str, execution: ToolExecution, result: ToolResult):
        """Update usage statistics for a tool."""
        try:
            stats = self._usage_stats.get(tool_name)
            if not stats:
                stats = ToolUsageStats(tool_name=tool_name)
                self._usage_stats[tool_name] = stats
            
            # Update counters
            stats.total_executions += 1
            
            if result.success:
                stats.successful_executions += 1
            else:
                stats.failed_executions += 1
            
            # Update timing
            if execution.started_at and execution.completed_at:
                execution_time = (execution.completed_at - execution.started_at).total_seconds()
                stats.total_execution_time += execution_time
                
                if stats.total_executions > 0:
                    stats.average_execution_time = stats.total_execution_time / stats.total_executions
                
                if stats.min_execution_time is None or execution_time < stats.min_execution_time:
                    stats.min_execution_time = execution_time
                
                if stats.max_execution_time is None or execution_time > stats.max_execution_time:
                    stats.max_execution_time = execution_time
            
            # Update usage dates
            now = datetime.utcnow()
            if stats.first_used is None:
                stats.first_used = now
            stats.last_used = now
            
            # Update daily usage
            date_str = now.strftime('%Y-%m-%d')
            stats.daily_usage[date_str] = stats.daily_usage.get(date_str, 0) + 1
            
        except Exception as e:
            logger.error(f"Failed to update usage stats for {tool_name}: {e}")
    
    def get_tool_stats(self, tool_name: str) -> Optional[ToolUsageStats]:
        """Get usage statistics for a tool."""
        return self._usage_stats.get(tool_name)
    
    def get_all_stats(self) -> Dict[str, ToolUsageStats]:
        """Get usage statistics for all tools."""
        return self._usage_stats.copy()
    
    def get_execution_history(self, limit: int = 100) -> List[ToolExecution]:
        """Get recent tool execution history."""
        executions = list(self._executions.values())
        executions.sort(key=lambda x: x.started_at or datetime.min, reverse=True)
        return executions[:limit]
    
    def configure_tool(self, tool_name: str, config: ToolConfiguration) -> bool:
        """Configure a tool with credentials and settings."""
        try:
            if tool_name not in self._tools:
                raise ToolNotFound(f"Tool {tool_name} not found")
            
            self._tool_configs[tool_name] = config
            logger.info(f"Configured tool: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure tool {tool_name}: {e}")
            return False
    
    def get_tool_config(self, tool_name: str) -> Optional[ToolConfiguration]:
        """Get configuration for a tool."""
        return self._tool_configs.get(tool_name)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all tools."""
        health = {
            "status": "healthy",
            "total_tools": len(self._tools),
            "available_tools": 0,
            "tool_status": {},
            "errors": []
        }
        
        for tool_name, tool in self._tools.items():
            try:
                is_available = tool.is_available()
                health["tool_status"][tool_name] = {
                    "available": is_available,
                    "category": tool.get_tool_category().value,
                    "auth_type": tool.get_auth_type().value
                }
                
                if is_available:
                    health["available_tools"] += 1
                    
            except Exception as e:
                health["tool_status"][tool_name] = {
                    "available": False,
                    "error": str(e)
                }
                health["errors"].append(f"Tool {tool_name}: {e}")
        
        if health["errors"]:
            health["status"] = "degraded" if health["available_tools"] > 0 else "unhealthy"
        
        return health
    
    def search_tools(self, query: str, category: Optional[ToolCategory] = None) -> List[IToolProvider]:
        """Search tools by name or description."""
        query_lower = query.lower()
        results = []
        
        for tool in self._tools.values():
            # Skip if category filter doesn't match
            if category and tool.get_tool_category() != category:
                continue
            
            # Check if query matches name or description
            if (query_lower in tool.get_tool_name().lower() or 
                query_lower in tool.get_tool_description().lower()):
                results.append(tool)
        
        return results
    
    def cleanup_old_executions(self, max_age_hours: int = 24) -> int:
        """Clean up old execution records."""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
            
            executions_to_remove = []
            for exec_id, execution in self._executions.items():
                if execution.started_at and execution.started_at.timestamp() < cutoff_time:
                    executions_to_remove.append(exec_id)
            
            for exec_id in executions_to_remove:
                del self._executions[exec_id]
            
            if executions_to_remove:
                logger.info(f"Cleaned up {len(executions_to_remove)} old tool executions")
            
            return len(executions_to_remove)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old executions: {e}")
            return 0