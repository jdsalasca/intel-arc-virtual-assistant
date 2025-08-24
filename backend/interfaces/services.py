"""
Service Interfaces for Intel Virtual Assistant Backend
Defines contracts for business logic operations following SOLID principles.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator
from ..models.dto import ChatRequest, ChatResponse
from ..models.domain import (
    VoiceRequest, VoiceResponse, Conversation, Message, 
    ModelInfo, HardwareInfo, ToolResult
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

    @abstractmethod
    async def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """Get status of a specific model."""
        pass

    @abstractmethod
    async def optimize_model(self, model_id: str, optimization_level: str) -> bool:
        """Optimize a model for better performance."""
        pass

    @abstractmethod
    async def validate_model(self, model_id: str) -> Dict[str, Any]:
        """Validate model integrity and performance."""
        pass

    @abstractmethod
    async def get_model_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics for loaded models."""
        pass

    @abstractmethod
    async def warmup_model(self, model_id: str) -> bool:
        """Warm up a model with a test inference."""
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

    @abstractmethod
    async def get_voice_status(self) -> Dict[str, Any]:
        """Get detailed status of voice services."""
        pass

    @abstractmethod
    async def preload_voices(self, voice_ids: List[str]) -> Dict[str, bool]:
        """Preload specific voices for faster synthesis."""
        pass

    @abstractmethod
    async def set_voice_settings(self, settings: Dict[str, Any]) -> bool:
        """Update voice service settings."""
        pass

    @abstractmethod
    async def clear_cache(self) -> bool:
        """Clear the voice response cache."""
        pass

    @abstractmethod
    async def benchmark_voice(self, test_text: str, voice_id: Optional[str] = None) -> Dict[str, Any]:
        """Benchmark voice synthesis performance."""
        pass

    @abstractmethod
    async def get_synthesis_metadata(self) -> Dict[str, Any]:
        """Get metadata from last synthesis."""
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

    @abstractmethod
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool."""
        pass

    @abstractmethod
    async def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool."""
        pass

    @abstractmethod
    async def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool."""
        pass

    @abstractmethod
    async def get_execution_statistics(self) -> Dict[str, Any]:
        """Get overall tool execution statistics."""
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

    @abstractmethod
    async def get_conversation_messages(
        self, conversation_id: str, limit: int = 50, offset: int = 0
    ) -> List[Message]:
        """Get messages from a conversation."""
        pass

    @abstractmethod
    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation."""
        pass

    @abstractmethod
    async def restore_conversation(self, conversation_id: str) -> bool:
        """Restore an archived conversation."""
        pass

    @abstractmethod
    async def search_conversations(self, query: str, limit: int = 20) -> List[Conversation]:
        """Search conversations by title or content."""
        pass

    @abstractmethod
    async def search_messages(
        self, query: str, conversation_id: Optional[str] = None, limit: int = 50
    ) -> List[Message]:
        """Search messages by content."""
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

    @abstractmethod
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        pass

    @abstractmethod
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        pass

    @abstractmethod
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics."""
        pass

    @abstractmethod
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current system alerts."""
        pass