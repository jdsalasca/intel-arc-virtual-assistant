"""
Core data models for conversation management.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid

class MessageRole(str, Enum):
    """Message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class MessageType(str, Enum):
    """Types of messages."""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    FILE = "file"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

class ConversationStatus(str, Enum):
    """Status of a conversation."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Message(BaseModel):
    """A single message in a conversation."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Audio/file specific fields
    audio_url: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    
    # Tool specific fields
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Generation metadata
    model_used: Optional[str] = None
    generation_time: Optional[float] = None
    token_count: Optional[int] = None

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class Conversation(BaseModel):
    """A conversation containing multiple messages."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Conversation settings
    conversation_model_config: Dict[str, Any] = Field(default_factory=dict)
    context_window: int = 4000
    max_tokens: int = 256
    temperature: float = 0.7
    
    # Statistics
    message_count: int = 0
    total_tokens: int = 0
    
    # Messages (not always loaded)
    messages: List[Message] = Field(default_factory=list)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class ConversationSummary(BaseModel):
    """Summary of a conversation for list views."""
    
    id: str
    title: Optional[str]
    status: ConversationStatus
    created_at: datetime
    last_activity: datetime
    message_count: int
    preview: str  # Last few words or summary
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationContext(BaseModel):
    """Context for conversation processing."""
    
    conversation_id: str
    messages: List[Message]
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    session_data: Dict[str, Any] = Field(default_factory=dict)
    active_tools: List[str] = Field(default_factory=list)
    
    # Context management
    max_context_messages: int = 20
    context_strategy: str = "sliding_window"  # sliding_window, summarize, hybrid
    
    def get_context_messages(self) -> List[Message]:
        """Get messages that fit within context window."""
        if self.context_strategy == "sliding_window":
            return self.messages[-self.max_context_messages:]
        return self.messages
    
    def add_message(self, message: Message) -> None:
        """Add a message to the context."""
        self.messages.append(message)
    
    def get_system_messages(self) -> List[Message]:
        """Get all system messages."""
        return [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history in OpenAI format."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.get_context_messages()
        ]

class UserProfile(BaseModel):
    """User profile and preferences."""
    
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
    
    # Preferences
    preferred_model: str = "qwen2.5-7b-int4"
    default_temperature: float = 0.7
    default_max_tokens: int = 256
    voice_enabled: bool = True
    preferred_voice: Optional[str] = None
    language: str = "en"
    
    # UI preferences
    theme: str = "dark"
    font_size: str = "medium"
    show_timestamps: bool = True
    auto_scroll: bool = True
    
    # Privacy settings
    save_conversations: bool = True
    share_analytics: bool = False
    
    # Tool permissions
    enabled_tools: List[str] = Field(default_factory=list)
    tool_permissions: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }