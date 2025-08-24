"""
Conversation Service Implementation for Intel Virtual Assistant Backend
Handles conversation management and message history.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..interfaces.services import IConversationService
from ..interfaces.repositories import IConversationRepository, IMessageRepository
from ..models.domain import Conversation, Message, ConversationStatus, MessageRole

logger = logging.getLogger(__name__)


class ConversationService(IConversationService):
    """Service for managing conversations and message history."""

    def __init__(
        self,
        conversation_repository: IConversationRepository,
        message_repository: IMessageRepository
    ):
        """Initialize conversation service with repositories."""
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository

    async def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        try:
            conversation_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Generate title if not provided
            if not title:
                title = f"Conversation {now.strftime('%Y-%m-%d %H:%M')}"

            conversation = Conversation(
                id=conversation_id,
                title=title,
                created_at=now,
                updated_at=now,
                status=ConversationStatus.ACTIVE,
                message_count=0
            )

            # Store in repository
            saved_conversation = await self._conversation_repository.create_conversation(conversation)
            
            logger.info(f"Created new conversation: {conversation_id}")
            return saved_conversation

        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        try:
            conversation = await self._conversation_repository.get_conversation_by_id(conversation_id)
            
            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return None

            return conversation

        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            raise

    async def get_conversations(
        self, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """Get list of conversations."""
        try:
            conversations = await self._conversation_repository.get_conversations(
                limit=limit, offset=offset
            )
            
            logger.debug(f"Retrieved {len(conversations)} conversations")
            return conversations

        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []

    async def add_message(
        self, conversation_id: str, message: Message
    ) -> Message:
        """Add a message to a conversation."""
        try:
            # Verify conversation exists
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            # Set message conversation_id if not already set
            if not message.conversation_id:
                message.conversation_id = conversation_id

            # Ensure message has an ID
            if not message.id:
                message.id = str(uuid.uuid4())

            # Set timestamp if not provided
            if not message.timestamp:
                message.timestamp = datetime.now()

            # Save message
            saved_message = await self._message_repository.create_message(message)

            # Update conversation
            conversation.message_count += 1
            conversation.updated_at = datetime.now()
            await self._conversation_repository.update_conversation(conversation)

            logger.debug(f"Added message to conversation {conversation_id}")
            return saved_message

        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
            raise

    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Message]:
        """Get messages from a conversation."""
        try:
            messages = await self._message_repository.get_messages_by_conversation_id(
                conversation_id=conversation_id,
                limit=limit,
                offset=offset
            )
            
            logger.debug(f"Retrieved {len(messages)} messages from conversation {conversation_id}")
            return messages

        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {str(e)}")
            return []

    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update a conversation."""
        try:
            # Update timestamp
            conversation.updated_at = datetime.now()
            
            # Save to repository
            updated_conversation = await self._conversation_repository.update_conversation(conversation)
            
            logger.info(f"Updated conversation: {conversation.id}")
            return updated_conversation

        except Exception as e:
            logger.error(f"Error updating conversation {conversation.id}: {str(e)}")
            raise

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        try:
            # First, delete all messages in the conversation
            await self._message_repository.delete_messages_by_conversation_id(conversation_id)
            
            # Then delete the conversation
            success = await self._conversation_repository.delete_conversation(conversation_id)
            
            if success:
                logger.info(f"Deleted conversation: {conversation_id}")
            else:
                logger.warning(f"Failed to delete conversation: {conversation_id}")
            
            return success

        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return False

    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages from a conversation."""
        try:
            # Delete all messages
            await self._message_repository.delete_messages_by_conversation_id(conversation_id)
            
            # Update conversation message count
            conversation = await self.get_conversation(conversation_id)
            if conversation:
                conversation.message_count = 0
                conversation.updated_at = datetime.now()
                await self._conversation_repository.update_conversation(conversation)
            
            logger.info(f"Cleared messages from conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error clearing conversation {conversation_id}: {str(e)}")
            return False

    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False

            conversation.status = ConversationStatus.ARCHIVED
            await self.update_conversation(conversation)
            
            logger.info(f"Archived conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error archiving conversation {conversation_id}: {str(e)}")
            return False

    async def restore_conversation(self, conversation_id: str) -> bool:
        """Restore an archived conversation."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False

            conversation.status = ConversationStatus.ACTIVE
            await self.update_conversation(conversation)
            
            logger.info(f"Restored conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error restoring conversation {conversation_id}: {str(e)}")
            return False

    async def search_conversations(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by title or content."""
        try:
            conversations = await self._conversation_repository.search_conversations(
                query=query, limit=limit
            )
            
            logger.debug(f"Found {len(conversations)} conversations matching '{query}'")
            return conversations

        except Exception as e:
            logger.error(f"Error searching conversations: {str(e)}")
            return []

    async def search_messages(
        self, 
        query: str, 
        conversation_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Message]:
        """Search messages by content."""
        try:
            messages = await self._message_repository.search_messages(
                query=query,
                conversation_id=conversation_id,
                limit=limit
            )
            
            logger.debug(f"Found {len(messages)} messages matching '{query}'")
            return messages

        except Exception as e:
            logger.error(f"Error searching messages: {str(e)}")
            return []

    async def get_conversation_statistics(self, conversation_id: str) -> Dict[str, Any]:
        """Get statistics for a conversation."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return {}

            messages = await self.get_conversation_messages(conversation_id, limit=1000)
            
            user_messages = [m for m in messages if m.role == MessageRole.USER]
            assistant_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
            
            total_characters = sum(len(m.content) for m in messages)
            avg_processing_time = (
                sum(m.processing_time for m in assistant_messages if m.processing_time) /
                len(assistant_messages) if assistant_messages else 0
            )

            return {
                "conversation_id": conversation_id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "status": conversation.status.value,
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "total_characters": total_characters,
                "average_processing_time": avg_processing_time,
                "tools_used": list(set(
                    tool for message in messages 
                    for tool in (message.tools_used or [])
                ))
            }

        except Exception as e:
            logger.error(f"Error getting conversation statistics: {str(e)}")
            return {}

    async def get_recent_context(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Message]:
        """Get recent messages for context."""
        try:
            messages = await self._message_repository.get_messages_by_conversation_id(
                conversation_id=conversation_id,
                limit=limit,
                offset=0
            )
            
            # Return in chronological order (oldest first)
            return sorted(messages, key=lambda m: m.timestamp)

        except Exception as e:
            logger.error(f"Error getting recent context: {str(e)}")
            return []

    async def export_conversation(
        self, 
        conversation_id: str, 
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export a conversation in specified format."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            messages = await self.get_conversation_messages(conversation_id, limit=10000)
            
            export_data = {
                "conversation": conversation.to_dict(),
                "messages": [message.to_dict() for message in messages],
                "export_timestamp": datetime.now().isoformat(),
                "format": format
            }

            logger.info(f"Exported conversation {conversation_id} in {format} format")
            return export_data

        except Exception as e:
            logger.error(f"Error exporting conversation {conversation_id}: {str(e)}")
            raise