"""
Chat Controller for Intel Virtual Assistant Backend
FastAPI endpoints for chat and conversation management.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json

from ..interfaces.services import IChatService, IConversationService
from ..models.dto import ChatRequest, ChatResponse, CreateConversationRequest, UpdateConversationRequest
from ..models.domain import Conversation, Message

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def get_chat_service() -> IChatService:
    """Dependency injection for chat service."""
    # This will be replaced by proper DI container
    from ..services import ChatService
    # For now, return a placeholder - this will be implemented in DI container
    raise NotImplementedError("DI container not yet implemented")


def get_conversation_service() -> IConversationService:
    """Dependency injection for conversation service."""
    # This will be replaced by proper DI container  
    from ..services import ConversationService
    # For now, return a placeholder - this will be implemented in DI container
    raise NotImplementedError("DI container not yet implemented")


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    chat_service: IChatService = Depends(get_chat_service)
) -> ChatResponse:
    """Send a chat message and get response."""
    try:
        logger.info(f"Processing chat message: {request.message[:50]}...")
        
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Process chat request
        response = await chat_service.process_chat_request(request)
        
        logger.info(f"Chat response generated successfully")
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid chat request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stream")
async def stream_chat_message(
    request: ChatRequest,
    chat_service: IChatService = Depends(get_chat_service)
):
    """Stream chat response tokens."""
    try:
        logger.info(f"Streaming chat message: {request.message[:50]}...")
        
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        async def generate_stream():
            """Generate streaming response."""
            try:
                async for token in chat_service.stream_chat_response(request):
                    # Format as server-sent events
                    yield f"data: {json.dumps({'token': token})}\n\n"
                
                # Send end-of-stream marker
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in stream generation: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except ValueError as e:
        logger.warning(f"Invalid stream request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    limit: int = 50,
    offset: int = 0,
    conversation_service: IConversationService = Depends(get_conversation_service)
) -> List[Conversation]:
    """Get list of conversations."""
    try:
        logger.debug(f"Getting conversations: limit={limit}, offset={offset}")
        
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        conversations = await conversation_service.get_conversations(limit=limit, offset=offset)
        return conversations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    request: CreateConversationRequest,
    conversation_service: IConversationService = Depends(get_conversation_service)
) -> Conversation:
    """Create a new conversation."""
    try:
        logger.info(f"Creating conversation: {request.title}")
        
        conversation = await conversation_service.create_conversation(request.title)
        return conversation
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    conversation_service: IConversationService = Depends(get_conversation_service)
) -> Conversation:
    """Get a specific conversation."""
    try:
        logger.debug(f"Getting conversation: {conversation_id}")
        
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    conversation_service: IConversationService = Depends(get_conversation_service)
) -> Conversation:
    """Update a conversation."""
    try:
        logger.info(f"Updating conversation: {conversation_id}")
        
        # Get existing conversation
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Update fields
        if request.title is not None:
            conversation.title = request.title
        
        if request.status is not None:
            from ..models.domain import ConversationStatus
            conversation.status = ConversationStatus(request.status)
        
        if request.metadata is not None:
            conversation.metadata = request.metadata
        
        # Save changes
        updated_conversation = await conversation_service.update_conversation(conversation)
        return updated_conversation
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid update request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conversation_service: IConversationService = Depends(get_conversation_service)
):
    """Delete a conversation."""
    try:
        logger.info(f"Deleting conversation: {conversation_id}")
        
        success = await conversation_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    conversation_service: IConversationService = Depends(get_conversation_service)
) -> List[Message]:
    """Get messages from a conversation."""
    try:
        logger.debug(f"Getting messages for conversation: {conversation_id}")
        
        if limit <= 0 or limit > 200:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 200")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        # Verify conversation exists
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = await conversation_service.get_conversation_messages(
            conversation_id, limit=limit, offset=offset
        )
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(
    conversation_id: str,
    conversation_service: IConversationService = Depends(get_conversation_service)
):
    """Clear all messages from a conversation."""
    try:
        logger.info(f"Clearing conversation: {conversation_id}")
        
        # Verify conversation exists
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        success = await conversation_service.clear_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear conversation")
        
        return {"message": "Conversation cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    conversation_service: IConversationService = Depends(get_conversation_service)
):
    """Archive a conversation."""
    try:
        logger.info(f"Archiving conversation: {conversation_id}")
        
        success = await conversation_service.archive_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations/{conversation_id}/restore")
async def restore_conversation(
    conversation_id: str,
    conversation_service: IConversationService = Depends(get_conversation_service)
):
    """Restore an archived conversation."""
    try:
        logger.info(f"Restoring conversation: {conversation_id}")
        
        success = await conversation_service.restore_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation restored successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{conversation_id}/context", response_model=List[Message])
async def get_conversation_context(
    conversation_id: str,
    limit: int = 10,
    chat_service: IChatService = Depends(get_chat_service)
) -> List[Message]:
    """Get recent conversation context."""
    try:
        logger.debug(f"Getting context for conversation: {conversation_id}")
        
        if limit <= 0 or limit > 50:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
        
        context = await chat_service.get_conversation_context(conversation_id, limit)
        return context
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search")
async def search_conversations(
    q: str,
    limit: int = 20,
    conversation_service: IConversationService = Depends(get_conversation_service)
):
    """Search conversations and messages."""
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        logger.debug(f"Searching conversations for: {q}")
        
        # Search conversations
        conversations = await conversation_service.search_conversations(q, limit)
        
        # Search messages
        messages = await conversation_service.search_messages(q, limit=limit)
        
        return {
            "query": q,
            "conversations": [conv.to_dict() for conv in conversations],
            "messages": [msg.to_dict() for msg in messages],
            "total_conversations": len(conversations),
            "total_messages": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")