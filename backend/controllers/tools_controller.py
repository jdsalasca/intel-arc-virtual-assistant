"""
Tools Controller for Intel Virtual Assistant Backend
FastAPI endpoints for tool execution and management.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends

from ..interfaces.services import IToolService
from ..models.dto import ExecuteToolRequest
from ..models.domain import ToolResult

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


from ..config.container import get_tool_service


# Dependency injection function is imported from container


@router.get("/", response_model=List[Dict[str, Any]])
async def get_available_tools(
    category: Optional[str] = None,
    enabled_only: bool = True,
    tool_service: IToolService = Depends(get_tool_service)
) -> List[Dict[str, Any]]:
    """Get list of available tools."""
    try:
        logger.debug(f"Getting available tools: category={category}, enabled_only={enabled_only}")
        
        tools = await tool_service.get_available_tools()
        
        # Filter by category if specified
        if category:
            tools = [tool for tool in tools if tool.get("category") == category]
        
        # Filter by enabled status if requested
        if enabled_only:
            tools = [tool for tool in tools if tool.get("enabled", False)]
        
        return tools
        
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/execute", response_model=ToolResult)
async def execute_tool(
    request: ExecuteToolRequest,
    tool_service: IToolService = Depends(get_tool_service)
) -> ToolResult:
    """Execute a tool with given parameters."""
    try:
        logger.info(f"Executing tool: {request.tool_name}")
        
        if not request.tool_name.strip():
            raise HTTPException(status_code=400, detail="Tool name cannot be empty")
        
        if not isinstance(request.parameters, dict):
            raise HTTPException(status_code=400, detail="Parameters must be a dictionary")
        
        # Execute tool
        result = await tool_service.execute_tool(
            request.tool_name, 
            request.parameters
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid tool execution request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing tool {request.tool_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tool_name}")
async def get_tool_info(
    tool_name: str,
    tool_service: IToolService = Depends(get_tool_service)
) -> Dict[str, Any]:
    """Get detailed information about a specific tool."""
    try:
        logger.debug(f"Getting info for tool: {tool_name}")
        
        if not tool_name.strip():
            raise HTTPException(status_code=400, detail="Tool name cannot be empty")
        
        tool_info = await tool_service.get_tool_info(tool_name)
        if not tool_info:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        return tool_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool info for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{tool_name}/enable")
async def enable_tool(
    tool_name: str,
    tool_service: IToolService = Depends(get_tool_service)
):
    """Enable a tool."""
    try:
        logger.info(f"Enabling tool: {tool_name}")
        
        if not tool_name.strip():
            raise HTTPException(status_code=400, detail="Tool name cannot be empty")
        
        success = await tool_service.enable_tool(tool_name)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        return {
            "message": f"Tool {tool_name} enabled successfully",
            "tool_name": tool_name,
            "enabled": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{tool_name}/disable")
async def disable_tool(
    tool_name: str,
    tool_service: IToolService = Depends(get_tool_service)
):
    """Disable a tool."""
    try:
        logger.info(f"Disabling tool: {tool_name}")
        
        if not tool_name.strip():
            raise HTTPException(status_code=400, detail="Tool name cannot be empty")
        
        success = await tool_service.disable_tool(tool_name)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        return {
            "message": f"Tool {tool_name} disabled successfully",
            "tool_name": tool_name,
            "enabled": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics/overview")
async def get_execution_statistics(
    tool_service: IToolService = Depends(get_tool_service)
) -> Dict[str, Any]:
    """Get overall tool execution statistics."""
    try:
        logger.debug("Getting tool execution statistics")
        
        stats = await tool_service.get_execution_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting execution statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories")
async def get_tool_categories(
    tool_service: IToolService = Depends(get_tool_service)
) -> Dict[str, Any]:
    """Get available tool categories."""
    try:
        logger.debug("Getting tool categories")
        
        tools = await tool_service.get_available_tools()
        
        # Group tools by category
        categories = {}
        for tool in tools:
            category = tool.get("category", "general")
            if category not in categories:
                categories[category] = {
                    "name": category,
                    "tools": [],
                    "total_tools": 0,
                    "enabled_tools": 0
                }
            
            categories[category]["tools"].append(tool["name"])
            categories[category]["total_tools"] += 1
            if tool.get("enabled", False):
                categories[category]["enabled_tools"] += 1
        
        return {
            "categories": list(categories.values()),
            "total_categories": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting tool categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search")
async def search_tools(
    query: str,
    category: Optional[str] = None,
    tool_service: IToolService = Depends(get_tool_service)
) -> Dict[str, Any]:
    """Search for tools by name or description."""
    try:
        logger.debug(f"Searching tools: query={query}, category={category}")
        
        if not query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        if len(query) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
        
        tools = await tool_service.get_available_tools()
        
        # Filter by category if specified
        if category:
            tools = [tool for tool in tools if tool.get("category") == category]
        
        # Search in name and description
        query_lower = query.lower()
        matching_tools = []
        
        for tool in tools:
            name_match = query_lower in tool.get("name", "").lower()
            desc_match = query_lower in tool.get("description", "").lower()
            
            if name_match or desc_match:
                tool_copy = tool.copy()
                tool_copy["match_score"] = 2 if name_match else 1  # Name matches score higher
                matching_tools.append(tool_copy)
        
        # Sort by match score (descending)
        matching_tools.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "query": query,
            "category": category,
            "tools": matching_tools,
            "total_matches": len(matching_tools)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching tools: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch/execute")
async def execute_tools_batch(
    requests: List[ExecuteToolRequest],
    continue_on_error: bool = True,
    tool_service: IToolService = Depends(get_tool_service)
) -> Dict[str, Any]:
    """Execute multiple tools in batch."""
    try:
        logger.info(f"Executing {len(requests)} tools in batch")
        
        if not requests:
            raise HTTPException(status_code=400, detail="No tool requests provided")
        
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 tools can be executed in batch")
        
        results = []
        successful = 0
        failed = 0
        
        for i, request in enumerate(requests):
            try:
                result = await tool_service.execute_tool(
                    request.tool_name,
                    request.parameters
                )
                results.append({
                    "index": i,
                    "tool_name": request.tool_name,
                    "success": result.success,
                    "result": result.result,
                    "execution_time": result.execution_time,
                    "error": result.error
                })
                
                if result.success:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                error_result = {
                    "index": i,
                    "tool_name": request.tool_name,
                    "success": False,
                    "result": None,
                    "execution_time": 0,
                    "error": str(e)
                }
                results.append(error_result)
                
                if not continue_on_error:
                    logger.warning(f"Stopping batch execution due to error in tool {request.tool_name}")
                    break
        
        return {
            "batch_results": results,
            "summary": {
                "total_tools": len(requests),
                "successful": successful,
                "failed": failed,
                "completed": len(results)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tools batch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def check_tools_health(
    tool_service: IToolService = Depends(get_tool_service)
) -> Dict[str, Any]:
    """Check health status of all tools."""
    try:
        logger.debug("Checking tools health")
        
        tools = await tool_service.get_available_tools()
        stats = await tool_service.get_execution_statistics()
        
        health_info = {
            "total_tools": len(tools),
            "enabled_tools": len([t for t in tools if t.get("enabled", False)]),
            "disabled_tools": len([t for t in tools if not t.get("enabled", False)]),
            "overall_success_rate": stats.get("overall_success_rate", 0.0),
            "total_executions": stats.get("total_executions", 0),
            "status": "healthy" if stats.get("overall_success_rate", 0) > 0.8 else "degraded"
        }
        
        # Check individual tool health
        tool_health = {}
        for tool in tools:
            tool_name = tool["name"]
            tool_stats = stats.get("tool_statistics", {}).get(tool_name, {})
            
            tool_health[tool_name] = {
                "enabled": tool.get("enabled", False),
                "usage_count": tool.get("usage_count", 0),
                "success_rate": tool_stats.get("success_rate", 0.0),
                "last_execution": tool_stats.get("last_execution"),
                "status": "healthy" if tool_stats.get("success_rate", 0) > 0.8 else "degraded"
            }
        
        health_info["tool_health"] = tool_health
        
        return health_info
        
    except Exception as e:
        logger.error(f"Error checking tools health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/registry/register")
async def register_custom_tool(
    tool_name: str,
    tool_config: Dict[str, Any],
    tool_service: IToolService = Depends(get_tool_service)
):
    """Register a custom tool (placeholder for extensibility)."""
    try:
        logger.info(f"Registering custom tool: {tool_name}")
        
        # This would be implemented to allow runtime tool registration
        # For now, return a not implemented error
        raise HTTPException(status_code=501, detail="Custom tool registration not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering custom tool: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/registry/{tool_name}")
async def unregister_tool(
    tool_name: str,
    tool_service: IToolService = Depends(get_tool_service)
):
    """Unregister a tool."""
    try:
        logger.info(f"Unregistering tool: {tool_name}")
        
        if not tool_name.strip():
            raise HTTPException(status_code=400, detail="Tool name cannot be empty")
        
        success = await tool_service.unregister_tool(tool_name)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        return {
            "message": f"Tool {tool_name} unregistered successfully",
            "tool_name": tool_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")