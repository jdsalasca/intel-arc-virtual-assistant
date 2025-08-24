"""
Conversation Manager for chat history and context preservation.
Handles conversation state, memory management, and context optimization.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from uuid import uuid4

from core.models.conversation import (
    Conversation, Message, ConversationContext, ConversationSummary,
    MessageRole, MessageType, ConversationStatus, UserProfile
)
from core.interfaces.storage_provider import IStorageProvider
from core.exceptions import ConversationNotFound, MessageNotFound, ValidationException

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversations, messages, and context."""
    
    def __init__(
        self, 
        storage: IStorageProvider,
        max_context_messages: int = 20,
        context_strategy: str = "sliding_window"
    ):
        self.storage = storage
        self.max_context_messages = max_context_messages
        self.context_strategy = context_strategy
        
        # In-memory conversation contexts for active sessions
        self._active_contexts: Dict[str, Any] = {}
    
    async def create_conversation(
        self, 
        user_id: str, 
        title: Optional[str] = None,
        system_message: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation."""
        try:
            # Create conversation
            conversation_id = self.storage.create_conversation(
                user_id=user_id,
                title=title or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                metadata={
                    "model_config": model_config or {},
                    "created_via": "api"
                }
            )
            
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=title,
                model_config=model_config or {}
            )
            
            # Add system message if provided
            if system_message:
                await self.add_message(
                    conversation_id=conversation_id,
                    role=MessageRole.SYSTEM,
                    content=system_message,
                    message_type=MessageType.TEXT
                )
            
            # Create initial context
            self._active_contexts[conversation_id] = ConversationContext(
                conversation_id=conversation_id,
                messages=[],
                max_context_messages=self.max_context_messages,
                context_strategy=self.context_strategy
            )
            
            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise ValidationException(f"Failed to create conversation: {e}")
    
    async def get_conversation(self, conversation_id: str) -> Conversation:
        """Get a conversation by ID."""
        try:
            # Try cache first
            if self.cache:
                cached = await self._get_from_cache(f"conversation:{conversation_id}")
                if cached:
                    return Conversation(**cached)
            
            # Get from storage
            conv_data = self.storage.get_conversation(conversation_id)
            if not conv_data:
                raise ConversationNotFound(f"Conversation {conversation_id} not found")
            
            conversation = Conversation(**conv_data)
            
            # Cache for future requests
            if self.cache:
                await self._set_cache(f"conversation:{conversation_id}", conversation.dict(), ttl=3600)
            
            return conversation
            
        except ConversationNotFound:
            raise
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            raise ValidationException(f"Failed to get conversation: {e}")
    
    async def list_conversations(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        status: Optional[ConversationStatus] = None
    ) -> List[ConversationSummary]:
        """List conversations for a user."""
        try:
            conversations = self.storage.list_conversations(user_id, limit, offset)
            
            summaries = []
            for conv in conversations:
                # Filter by status if specified
                if status and conv.get("status") != status.value:
                    continue
                
                # Get preview from last message
                messages = self.storage.get_messages(conv["id"], limit=1)
                preview = messages[0]["content"][:100] + "..." if messages else "No messages"
                
                summaries.append(ConversationSummary(
                    id=conv["id"],
                    title=conv["title"],
                    status=ConversationStatus(conv.get("status", "active")),
                    created_at=conv["created_at"],
                    last_activity=conv.get("last_activity", conv["created_at"]),
                    message_count=conv.get("message_count", 0),
                    preview=preview,
                    metadata=conv.get("metadata", {})
                ))
            
            return summaries
            
        except Exception as e:
            logger.error(f"Failed to list conversations for user {user_id}: {e}")
            raise ValidationException(f"Failed to list conversations: {e}")
    
    async def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        """Add a message to a conversation."""
        try:
            # Validate conversation exists
            await self.get_conversation(conversation_id)
            
            # Create message
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_type=message_type,
                metadata=metadata or {},
                tool_calls=tool_calls or []
            )
            
            # Store in database
            message_id = self.storage.add_message(
                conversation_id=conversation_id,
                role=role.value,
                content=content,
                metadata={
                    **message.dict(),
                    "message_type": message_type.value
                }
            )
            message.id = message_id
            
            # Update active context
            if conversation_id in self._active_contexts:
                self._active_contexts[conversation_id].add_message(message)
                
                # Manage context size
                context = self._active_contexts[conversation_id]
                if len(context.messages) > self.max_context_messages:
                    await self._optimize_context(conversation_id)
            
            # Invalidate conversation cache
            if self.cache:
                await self._delete_from_cache(f"conversation:{conversation_id}")
            
            logger.debug(f"Added message {message_id} to conversation {conversation_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            raise ValidationException(f"Failed to add message: {e}")
    
    async def get_conversation_context(self, conversation_id: str) -> ConversationContext:
        """Get conversation context for inference."""
        try:
            # Check if context is already loaded
            if conversation_id in self._active_contexts:
                return self._active_contexts[conversation_id]
            
            # Load conversation and messages
            conversation = await self.get_conversation(conversation_id)
            messages_data = self.storage.get_messages(conversation_id, limit=self.max_context_messages)
            
            # Convert to Message objects
            messages = []
            for msg_data in messages_data:
                messages.append(Message(
                    id=msg_data["id"],
                    conversation_id=conversation_id,
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    message_type=MessageType(msg_data.get("message_type", "text")),
                    timestamp=msg_data["timestamp"],
                    metadata=msg_data.get("metadata", {})
                ))
            
            # Create context
            context = ConversationContext(
                conversation_id=conversation_id,
                messages=messages,
                max_context_messages=self.max_context_messages,
                context_strategy=self.context_strategy
            )
            
            # Cache the context
            self._active_contexts[conversation_id] = context
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context for conversation {conversation_id}: {e}")
            raise ValidationException(f"Failed to get conversation context: {e}")
    
    async def _optimize_context(self, conversation_id: str) -> None:
        """Optimize conversation context when it gets too long."""
        try:
            context = self._active_contexts[conversation_id]
            
            if self.context_strategy == "sliding_window":
                # Keep only recent messages
                context.messages = context.messages[-self.max_context_messages:]
                
            elif self.context_strategy == "summarize":
                # Summarize older messages and keep recent ones
                if len(context.messages) > self.max_context_messages:
                    messages_to_summarize = context.messages[:-10]  # Keep last 10 full
                    summary = await self._summarize_messages(messages_to_summarize)
                    
                    # Create summary message
                    summary_message = Message(
                        conversation_id=conversation_id,
                        role=MessageRole.SYSTEM,
                        content=f"Previous conversation summary: {summary}",
                        message_type=MessageType.TEXT,
                        metadata={"type": "summary", "summarized_count": len(messages_to_summarize)}
                    )
                    
                    # Replace old messages with summary + recent messages
                    context.messages = [summary_message] + context.messages[-10:]
            
            elif self.context_strategy == "hybrid":
                # Combination of sliding window and summarization
                if len(context.messages) > self.max_context_messages:
                    # Summarize middle part, keep first few and last few
                    first_messages = context.messages[:3]
                    last_messages = context.messages[-10:]
                    middle_messages = context.messages[3:-10]
                    
                    if middle_messages:
                        summary = await self._summarize_messages(middle_messages)
                        summary_message = Message(
                            conversation_id=conversation_id,
                            role=MessageRole.SYSTEM,
                            content=f"Conversation summary: {summary}",
                            message_type=MessageType.TEXT,
                            metadata={"type": "summary", "summarized_count": len(middle_messages)}
                        )
                        context.messages = first_messages + [summary_message] + last_messages
                    else:
                        context.messages = first_messages + last_messages
            
            logger.debug(f"Optimized context for conversation {conversation_id}, now has {len(context.messages)} messages")
            
        except Exception as e:
            logger.error(f"Failed to optimize context for conversation {conversation_id}: {e}")
    
    async def _summarize_messages(self, messages: List[Message]) -> str:
        """Summarize a list of messages."""
        try:
            # Simple summarization - in a real implementation, you'd use an LLM
            user_messages = [msg.content for msg in messages if msg.role == MessageRole.USER]
            assistant_messages = [msg.content for msg in messages if msg.role == MessageRole.ASSISTANT]
            
            summary_parts = []
            
            if user_messages:
                summary_parts.append(f"User discussed: {', '.join(user_messages[:3])}")
            
            if assistant_messages:
                summary_parts.append(f"Assistant responded with: {', '.join(assistant_messages[:3])}")
            
            return ". ".join(summary_parts)
            
        except Exception as e:
            logger.warning(f"Failed to summarize messages: {e}")
            return "Previous conversation content"
    
    async def search_conversations(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 20
    ) -> List[ConversationSummary]:
        """Search conversations by content."""
        try:
            results = self.storage.search_conversations(user_id, query, limit)
            
            summaries = []
            for conv in results:
                summaries.append(ConversationSummary(
                    id=conv["id"],
                    title=conv["title"],
                    status=ConversationStatus(conv.get("status", "active")),
                    created_at=conv["created_at"],
                    last_activity=conv.get("last_activity", conv["created_at"]),
                    message_count=conv.get("message_count", 0),
                    preview=conv.get("preview", ""),
                    metadata=conv.get("metadata", {})
                ))
            
            return summaries
            
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            raise ValidationException(f"Failed to search conversations: {e}")
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        try:
            # Remove from active contexts
            if conversation_id in self._active_contexts:
                del self._active_contexts[conversation_id]
            
            # Clear cache
            if self.cache:
                await self._delete_from_cache(f"conversation:{conversation_id}")
            
            # Delete from storage
            return self.storage.delete_conversation(conversation_id)
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            raise ValidationException(f"Failed to delete conversation: {e}")
    
    async def _get_from_cache(self, key: str) -> Any:
        """Get value from cache."""
        try:
            if self.cache:
                return self.cache.get(key)
        except Exception as e:
            logger.debug(f"Cache get failed for {key}: {e}")
        return None
    
    async def _set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        try:
            if self.cache:
                self.cache.set(key, value, ttl)
        except Exception as e:
            logger.debug(f"Cache set failed for {key}: {e}")
    
    async def _delete_from_cache(self, key: str) -> None:
        """Delete value from cache."""
        try:
            if self.cache:
                self.cache.delete(key)
        except Exception as e:
            logger.debug(f"Cache delete failed for {key}: {e}")
    
    async def cleanup_old_contexts(self, max_age_hours: int = 24) -> None:
        """Clean up old inactive contexts."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            contexts_to_remove = []
            for conv_id, context in self._active_contexts.items():
                # Check if context has been inactive
                if context.messages:
                    last_message_time = context.messages[-1].timestamp
                    if last_message_time < cutoff_time:
                        contexts_to_remove.append(conv_id)
                else:
                    contexts_to_remove.append(conv_id)
            
            for conv_id in contexts_to_remove:
                del self._active_contexts[conv_id]
                logger.debug(f"Cleaned up inactive context for conversation {conv_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old contexts: {e}")
    
    def get_active_conversations_count(self) -> int:
        """Get count of active conversations."""
        return len(self._active_contexts)