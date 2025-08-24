"""
Core interfaces for storage providers.
Defines abstractions for data persistence and retrieval.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from core.models.conversation import Conversation

class IStorageProvider(ABC):
    """Abstract interface for storage providers."""
    
    @abstractmethod
    def connect(self, connection_string: Optional[str] = None) -> bool:
        """Connect to storage."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from storage."""
        pass
    
    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> bool:
        """Save a conversation."""
        pass
    
    @abstractmethod
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation."""
        pass
    
    @abstractmethod
    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations."""
        pass
    
    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        pass
    
    @abstractmethod
    def save_setting(self, key: str, value: str) -> bool:
        """Save a setting."""
        pass
    
    @abstractmethod
    def load_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Load a setting."""
        pass
    
    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information and statistics."""
        pass
