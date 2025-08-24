"""
Service Interfaces for Intel Virtual Assistant Backend
Defines contracts for business logic operations following SOLID principles.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator
from ..models.domain import (
    ChatRequest, ChatResponse, VoiceRequest, VoiceResponse,
    Conversation, Message, ModelInfo, HardwareInfo, ToolResult
)


class IChatService(ABC):
    """Interface for chat operations."""

    @abstractmethod
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return response."""
        pass

    @abstractmethod
    async def stream_chat_response(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """Stream chat response tokens."""
        pass

    @abstractmethod
    async def get_conversation_context(
        self, conversation_id: str, limit: int = 10
    ) -> List[Message]:
        """Get recent conversation context."""
        pass


class IModelService(ABC):
    """Interface for AI model management."""

    @abstractmethod
    async def load_model(self, model_id: str, device: Optional[str] = None) -> bool:
        """Load an AI model."""
        pass

    @abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        """Unload an AI model."""
        pass

    @abstractmethod
    async def get_loaded_models(self) -> List[ModelInfo]:
        """Get information about loaded models."""
        pass

    @abstractmethod
    async def get_available_models(self) -> List[ModelInfo]:
        """Get information about available models."""
        pass

    @abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using a loaded model."""
        pass


class IVoiceService(ABC):
    """Interface for voice operations."""

    @abstractmethod
    async def synthesize_speech(self, request: VoiceRequest) -> VoiceResponse:
        """Convert text to speech."""
        pass

    @abstractmethod
    async def recognize_speech(self, audio_data: bytes) -> str:
        """Convert speech to text."""
        pass

    @abstractmethod
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get available voice models."""
        pass

    @abstractmethod
    async def is_voice_available(self) -> bool:
        """Check if voice services are available."""
        pass


class IToolService(ABC):
    """Interface for tool execution operations."""

    @abstractmethod
    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute a tool with given parameters."""
        pass

    @abstractmethod
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        pass

    @abstractmethod
    async def register_tool(
        self, tool_name: str, tool_handler: Any
    ) -> bool:
        """Register a new tool."""
        pass

    @abstractmethod
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        pass


class IHardwareService(ABC):
    """Interface for hardware optimization operations."""

    @abstractmethod
    async def get_hardware_info(self) -> HardwareInfo:
        """Get current hardware information."""
        pass

    @abstractmethod
    async def optimize_for_device(
        self, device_type: str, model_id: str
    ) -> Dict[str, Any]:
        """Get optimization parameters for a device."""
        pass

    @abstractmethod
    async def get_optimal_device(self, task_type: str) -> str:
        """Get the optimal device for a task type."""
        pass

    @abstractmethod
    async def benchmark_device(self, device_type: str) -> Dict[str, Any]:
        """Run benchmark on a device."""
        pass


class IConversationService(ABC):
    """Interface for conversation management."""

    @abstractmethod
    async def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        pass

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        pass

    @abstractmethod
    async def get_conversations(
        self, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """Get list of conversations."""
        pass

    @abstractmethod
    async def add_message(
        self, conversation_id: str, message: Message
    ) -> Message:
        """Add a message to a conversation."""
        pass

    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update a conversation."""
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        pass

    @abstractmethod
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages from a conversation."""
        pass


class IHealthService(ABC):
    """Interface for system health monitoring."""

    @abstractmethod
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        pass

    @abstractmethod
    async def get_component_status(self, component: str) -> Dict[str, Any]:
        """Get status of a specific component."""
        pass

    @abstractmethod
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        pass