"""
Simple Conversation Manager
Basic conversation management for the AI assistant.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.interfaces.storage_provider import IStorageProvider
from core.models.conversation import Conversation, Message, MessageRole

logger = logging.getLogger(__name__)

class ConversationManager:
    """Simple conversation manager."""
    
    def __init__(self, storage: IStorageProvider):
        self.storage = storage
        self._active_conversations: Dict[str, Conversation] = {}
    
    async def create_conversation(self, user_id: str = "default") -> Conversation:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.utcnow()
        )
        
        self._active_conversations[conversation_id] = conversation
        self.storage.save_conversation(conversation)
        
        logger.info(f"Created conversation: {conversation_id}")
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation."""
        # Check active conversations first
        if conversation_id in self._active_conversations:
            return self._active_conversations[conversation_id]
        
        # Load from storage
        conversation = self.storage.load_conversation(conversation_id)
        if conversation:
            self._active_conversations[conversation_id] = conversation
        
        return conversation
    
    async def add_message(self, conversation_id: str, role: MessageRole, content: str) -> Message:
        """Add a message to a conversation."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        conversation.add_message(message)
        conversation.updated_at = datetime.utcnow()
        
        # Save to storage
        self.storage.save_conversation(conversation)
        
        return message
    
    async def get_conversations(self, limit: int = 50) -> List[Conversation]:
        """Get list of conversations."""
        conversations_info = self.storage.list_conversations(limit=limit)
        conversations = []
        
        for info in conversations_info:
            conversation = self.storage.load_conversation(info['id'])
            if conversation:
                conversations.append(conversation)
        
        return conversations
    
    async def save_conversation(self, conversation: Conversation) -> bool:
        """Save a conversation."""
        return self.storage.save_conversation(conversation)