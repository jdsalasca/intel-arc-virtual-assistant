"""
Repository Interfaces for Intel Virtual Assistant Backend
Defines contracts for data persistence operations following clean architecture principles.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models.domain import Message, Conversation, ModelInfo


class IMessageRepository(ABC):
    """Interface for message persistence operations."""

    @abstractmethod
    async def create_message(self, message: Message) -> Message:
        """Create a new message."""
        pass

    @abstractmethod
    async def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Retrieve a message by its ID."""
        pass

    @abstractmethod
    async def get_messages_by_conversation(
        self, 
        conversation_id: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """Retrieve messages for a conversation with pagination."""
        pass

    @abstractmethod
    async def update_message(self, message: Message) -> Message:
        """Update an existing message."""
        pass

    @abstractmethod
    async def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID."""
        pass


class IConversationRepository(ABC):
    """Interface for conversation persistence operations."""

    @abstractmethod
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        pass

    @abstractmethod
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation by its ID."""
        pass

    @abstractmethod
    async def get_conversations(
        self, 
        limit: Optional[int] = None,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Conversation]:
        """Retrieve conversations with optional filtering."""
        pass

    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update an existing conversation."""
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID."""
        pass

    @abstractmethod
    async def get_conversation_with_messages(
        self, 
        conversation_id: str,
        message_limit: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get conversation with its messages."""
        pass


class IModelRepository(ABC):
    """Interface for model information persistence."""

    @abstractmethod
    async def save_model_info(self, model_info: ModelInfo) -> ModelInfo:
        """Save model information."""
        pass

    @abstractmethod
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Retrieve model information by ID."""
        pass

    @abstractmethod
    async def get_all_models(self) -> List[ModelInfo]:
        """Retrieve all model information."""
        pass

    @abstractmethod
    async def update_model_status(self, model_id: str, loaded: bool) -> bool:
        """Update model load status."""
        pass

    @abstractmethod
    async def delete_model_info(self, model_id: str) -> bool:
        """Delete model information."""
        pass


class IConfigRepository(ABC):
    """Interface for configuration persistence."""

    @abstractmethod
    async def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value by key."""
        pass

    @abstractmethod
    async def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value."""
        pass

    @abstractmethod
    async def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values."""
        pass

    @abstractmethod
    async def delete_config(self, key: str) -> bool:
        """Delete configuration by key."""
        pass