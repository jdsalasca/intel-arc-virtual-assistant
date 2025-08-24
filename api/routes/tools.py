"""
Tools API Routes
Endpoints for managing and executing tools.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

# Request/Response models
class ToolExecutionRequest(BaseModel):
    """Tool execution request model."""
    parameters: Dict[str, Any] = {}

class ToolExecutionResponse(BaseModel):
    """Tool execution response model."""
    tool_name: str
    success: bool
    result: Any = None
    error: str = None
    execution_time: float = None
    timestamp: datetime

# Create router
router = APIRouter()

async def get_tool_registry() -> ToolRegistry:
    """Get tool registry dependency."""
    from main import tool_registry
    return tool_registry

@router.get("/")
async def list_tools(tool_registry: ToolRegistry = Depends(get_tool_registry)):
    """Get list of available tools."""
    try:
        tools = []
        for tool_name in tool_registry.get_available_tools():
            tool = tool_registry.get_tool(tool_name)
            if tool:
                tools.append({
                    "name": tool.get_tool_name(),
                    "description": tool.get_tool_description(),
                    "category": tool.get_tool_category().value,
                    "auth_type": tool.get_auth_type().value,
                    "available": tool.is_available(),
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "description": p.description,
                            "required": p.required,
                            "default": p.default
                        }
                        for p in tool.get_parameters()
                    ]
                })
        
        return {
            "tools": tools,
            "total": len(tools)
        }
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@router.get("/{tool_name}")
async def get_tool_info(tool_name: str, tool_registry: ToolRegistry = Depends(get_tool_registry)):
    """Get information about a specific tool."""
    try:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        return {
            "name": tool.get_tool_name(),
            "description": tool.get_tool_description(),
            "category": tool.get_tool_category().value,
            "auth_type": tool.get_auth_type().value,
            "available": tool.is_available(),
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in tool.get_parameters()
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool info for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tool info: {str(e)}")

@router.post("/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    request: ToolExecutionRequest,
    tool_registry: ToolRegistry = Depends(get_tool_registry)
):
    """Execute a tool."""
    try:
        if tool_name not in tool_registry.get_available_tools():
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        start_time = datetime.utcnow()
        result = await tool_registry.execute_tool(tool_name, request.parameters)
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return ToolExecutionResponse(
            tool_name=tool_name,
            success=result.success,
            result=result.data,
            error=result.error,
            execution_time=execution_time,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@router.get("/{tool_name}/schema")
async def get_tool_schema(tool_name: str, tool_registry: ToolRegistry = Depends(get_tool_registry)):
    """Get tool schema for OpenAPI/JSON Schema compatibility."""
    try:
        schema = tool_registry.get_tool_schema(tool_name)
        return schema
        
    except Exception as e:
        logger.error(f"Failed to get tool schema for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tool schema: {str(e)}")