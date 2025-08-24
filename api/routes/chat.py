"""
Chat API Routes
Real-time chat interface with WebSocket support for streaming responses.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.interfaces.agent_provider import AgentRequest, ExecutionMode
from services.chat_agent_orchestrator import ChatAgentOrchestrator

logger = logging.getLogger(__name__)

# Request/Response models
class ChatMessage(BaseModel):
    """Chat message model."""
    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=2048)
    stream: bool = False

class ChatResponse(BaseModel):
    """Chat response model."""
    content: str
    conversation_id: str
    success: bool = True
    error: Optional[str] = None
    tools_used: Optional[list] = None
    processing_time: Optional[float] = None
    timestamp: datetime

class ConversationInfo(BaseModel):
    """Conversation information model."""
    conversation_id: str
    created_at: datetime
    message_count: int
    last_activity: datetime

# Create router
router = APIRouter()

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_connections: Dict[str, set] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
            # Remove from conversation connections
            for conversation_id, clients in self.conversation_connections.items():
                clients.discard(client_id)
            
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    def add_to_conversation(self, client_id: str, conversation_id: str):
        """Add client to conversation group."""
        if conversation_id not in self.conversation_connections:
            self.conversation_connections[conversation_id] = set()
        self.conversation_connections[conversation_id].add(client_id)

# Global connection manager
manager = ConnectionManager()

# Dependency to get chat agent
async def get_chat_agent() -> ChatAgentOrchestrator:
    """Get chat agent dependency."""
    # This would be injected from the main app
    # For now, we'll assume it's available in the app state
    from main import model_manager, conversation_manager
    from services.tool_registry import ToolRegistry
    
    tool_registry = ToolRegistry()
    chat_agent = ChatAgentOrchestrator(model_manager, conversation_manager, tool_registry)
    
    # Initialize if not already done
    if not await chat_agent.is_ready():
        await chat_agent.initialize({})
    
    return chat_agent

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    chat_agent: ChatAgentOrchestrator = Depends(get_chat_agent)
):
    """Send a chat message and get response."""
    try:
        # Create agent request
        request = AgentRequest(
            user_input=message.content,
            conversation_id=message.conversation_id,
            temperature=message.temperature,
            max_tokens=message.max_tokens,
            execution_mode=ExecutionMode.STREAMING if message.stream else ExecutionMode.ASYNC
        )
        
        # Process request
        if message.stream:
            # Return streaming response
            async def generate():
                async for response in await chat_agent.process_request(request):
                    if response.is_final:
                        break
                    yield f"data: {json.dumps({'content': response.content, 'is_partial': response.is_partial})}\n\n"
                yield f"data: {json.dumps({'content': '', 'is_final': True})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/plain")
        else:
            # Non-streaming response
            response = await chat_agent.process_request(request)
            
            return ChatResponse(
                content=response.content,
                conversation_id=response.conversation_id or "default",
                success=response.success,
                error=response.error,
                tools_used=response.tools_used,
                processing_time=response.processing_time,
                timestamp=datetime.utcnow()
            )
    
    except Exception as e:
        logger.error(f"Chat message processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    chat_agent: ChatAgentOrchestrator = Depends(get_chat_agent)
):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type", "message")
            
            if message_type == "message":
                # Handle chat message
                await handle_websocket_message(websocket, client_id, data, chat_agent)
            
            elif message_type == "join_conversation":
                # Join conversation room
                conversation_id = data.get("conversation_id")
                if conversation_id:
                    manager.add_to_conversation(client_id, conversation_id)
                    await manager.send_personal_message({
                        "type": "joined_conversation",
                        "conversation_id": conversation_id
                    }, client_id)
            
            elif message_type == "ping":
                # Heartbeat
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)

async def handle_websocket_message(
    websocket: WebSocket,
    client_id: str,
    data: Dict[str, Any],
    chat_agent: ChatAgentOrchestrator
):
    """Handle incoming WebSocket chat message."""
    try:
        content = data.get("content", "")
        conversation_id = data.get("conversation_id")
        temperature = data.get("temperature")
        max_tokens = data.get("max_tokens")
        
        if not content.strip():
            await manager.send_personal_message({
                "type": "error",
                "error": "Empty message content"
            }, client_id)
            return
        
        # Send acknowledgment
        await manager.send_personal_message({
            "type": "message_received",
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)
        
        # Create agent request
        request = AgentRequest(
            user_input=content,
            conversation_id=conversation_id,
            temperature=temperature,
            max_tokens=max_tokens,
            execution_mode=ExecutionMode.STREAMING
        )
        
        # Process request with streaming
        full_response = ""
        async for response in await chat_agent.process_request(request):
            # Send partial response
            await manager.send_personal_message({
                "type": "response_chunk",
                "content": response.content,
                "conversation_id": response.conversation_id,
                "is_partial": response.is_partial,
                "is_final": response.is_final,
                "tools_used": response.tools_used,
                "timestamp": datetime.utcnow().isoformat()
            }, client_id)
            
            if not response.is_partial:
                full_response += response.content
            
            if response.is_final:
                # Send completion message
                await manager.send_personal_message({
                    "type": "response_complete",
                    "conversation_id": response.conversation_id,
                    "processing_time": response.processing_time,
                    "tools_used": response.tools_used,
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
                break
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "error": f"Failed to process message: {str(e)}"
        }, client_id)

@router.get("/conversations", response_model=list[ConversationInfo])
async def get_conversations(
    chat_agent: ChatAgentOrchestrator = Depends(get_chat_agent)
):
    """Get list of conversations."""
    try:
        # Get conversations from conversation manager
        conversations = await chat_agent.conversation_manager.get_conversations()
        
        conversation_info = []
        for conv in conversations:
            conversation_info.append(ConversationInfo(
                conversation_id=conv.id,
                created_at=conv.created_at,
                message_count=len(conv.messages),
                last_activity=conv.updated_at or conv.created_at
            ))
        
        return conversation_info
    
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")

@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    chat_agent: ChatAgentOrchestrator = Depends(get_chat_agent)
):
    """Get conversation history."""
    try:
        history = await chat_agent.get_conversation_history(conversation_id)
        return {"conversation_id": conversation_id, "messages": history}
    
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation history")

@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(
    conversation_id: str,
    chat_agent: ChatAgentOrchestrator = Depends(get_chat_agent)
):
    """Clear conversation history."""
    try:
        success = await chat_agent.clear_conversation(conversation_id)
        if success:
            return {"message": "Conversation cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    except Exception as e:
        logger.error(f"Failed to clear conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear conversation")

@router.get("/status")
async def get_chat_status(
    chat_agent: ChatAgentOrchestrator = Depends(get_chat_agent)
):
    """Get chat service status."""
    try:
        is_ready = await chat_agent.is_ready()
        stats = chat_agent.get_performance_stats()
        
        return {
            "status": "ready" if is_ready else "initializing",
            "agent_name": chat_agent.get_agent_name(),
            "version": chat_agent.get_agent_version(),
            "capabilities": chat_agent.get_capabilities().__dict__,
            "available_tools": chat_agent.get_available_tools(),
            "active_connections": len(manager.active_connections),
            "performance_stats": stats
        }
    
    except Exception as e:
        logger.error(f"Failed to get chat status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    chat_agent: ChatAgentOrchestrator = Depends(get_chat_agent)
):
    """Execute a tool directly."""
    try:
        if tool_name not in chat_agent.get_available_tools():
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        result = await chat_agent.execute_tool(tool_name, parameters)
        return {
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to execute tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")