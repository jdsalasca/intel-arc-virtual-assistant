"""
Core interfaces for storage providers.
Defines abstractions for data persistence and retrieval.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

class StorageType(Enum):
    """Types of storage backends."""
    SQLITE = "sqlite"
    REDIS = "redis"
    MEMORY = "memory"
    FILE = "file"
    POSTGRES = "postgres"

class IStorageProvider(ABC):
    """Abstract interface for storage providers."""
    
    @abstractmethod
    def connect(self, connection_string: str, **kwargs) -> bool:
        """Connect to the storage backend."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the storage backend."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to storage."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Perform a health check on the storage."""
        pass

class IConversationStorage(ABC):
    """Abstract interface for conversation storage."""
    
    @abstractmethod
    def create_conversation(
        self, 
        user_id: str, 
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new conversation and return its ID."""
        pass
    
    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        pass
    
    @abstractmethod
    def list_conversations(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List conversations for a user."""
        pass
    
    @abstractmethod
    def update_conversation(
        self, 
        conversation_id: str, 
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update conversation metadata."""
        pass
    
    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        pass
    
    @abstractmethod
    def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to a conversation."""
        pass
    
    @abstractmethod
    def get_messages(
        self, 
        conversation_id: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation."""
        pass
    
    @abstractmethod
    def update_message(
        self, 
        message_id: str, 
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a message."""
        pass
    
    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        """Delete a message."""
        pass
    
    @abstractmethod
    def search_conversations(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search conversations by content."""
        pass

class ICacheStorage(ABC):
    """Abstract interface for cache storage."""
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache."""
        pass
    
    @abstractmethod
    def get(self, key: str) -> Any:
        """Get a value from cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        pass
    
    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        pass
    
    @abstractmethod
    def increment(self, key: str, delta: int = 1) -> int:
        """Increment a numeric value."""
        pass
    
    @abstractmethod
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        pass

class IModelStorage(ABC):
    """Abstract interface for model metadata storage."""
    
    @abstractmethod
    def save_model_info(
        self, 
        model_id: str, 
        model_path: str, 
        model_type: str,
        device: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Save model information."""
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model information."""
        pass
    
    @abstractmethod
    def list_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available models."""
        pass
    
    @abstractmethod
    def delete_model_info(self, model_id: str) -> bool:
        """Delete model information."""
        pass
    
    @abstractmethod
    def update_model_usage(self, model_id: str, usage_data: Dict[str, Any]) -> bool:
        """Update model usage statistics."""
        pass

class IConfigStorage(ABC):
    """Abstract interface for configuration storage."""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def delete_config(self, key: str) -> bool:
        """Delete configuration value."""
        pass
    
    @abstractmethod
    def list_configs(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """List configuration values."""
        pass
    
    @abstractmethod
    def export_configs(self) -> Dict[str, Any]:
        """Export all configurations."""
        pass
    
    @abstractmethod
    def import_configs(self, configs: Dict[str, Any]) -> bool:
        """Import configurations."""
        pass