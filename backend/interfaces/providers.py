"""
Provider Interfaces for Intel Virtual Assistant Backend
Defines contracts for external integrations and hardware providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from ..models.domain import HardwareType, ModelType


class IModelProvider(ABC):
    """Interface for AI model providers."""

    @abstractmethod
    async def load_model(
        self, 
        model_path: str, 
        device: HardwareType = HardwareType.AUTO,
        **kwargs
    ) -> Any:
        """Load a model from path."""
        pass

    @abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        """Unload a model."""
        pass

    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        model_id: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text using the model."""
        pass

    @abstractmethod
    async def stream_generate(
        self, 
        prompt: str, 
        model_id: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generated text tokens."""
        pass

    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model."""
        pass

    @abstractmethod
    def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is loaded."""
        pass


class IVoiceProvider(ABC):
    """Interface for voice synthesis and recognition providers."""

    @abstractmethod
    async def synthesize(
        self, 
        text: str,
        voice_id: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """Synthesize speech from text."""
        pass

    @abstractmethod
    async def recognize(self, audio_data: bytes) -> str:
        """Recognize speech from audio data."""
        pass

    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if voice provider is available."""
        pass


class IToolProvider(ABC):
    """Interface for tool providers (web search, email, etc.)."""

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get the tool's description."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool is available."""
        pass


class IHardwareProvider(ABC):
    """Interface for hardware optimization providers."""

    @abstractmethod
    def detect_hardware(self) -> Dict[str, Any]:
        """Detect available hardware components."""
        pass

    @abstractmethod
    def get_optimal_device(
        self, 
        model_type: ModelType,
        model_size: int
    ) -> HardwareType:
        """Get optimal device for a model."""
        pass

    @abstractmethod
    def get_optimization_config(
        self, 
        device: HardwareType,
        model_type: ModelType
    ) -> Dict[str, Any]:
        """Get optimization configuration for device and model."""
        pass

    @abstractmethod
    def benchmark_device(self, device: HardwareType) -> Dict[str, Any]:
        """Run benchmark on a device."""
        pass


class IStorageProvider(ABC):
    """Interface for data storage providers."""

    @abstractmethod
    async def connect(self, connection_string: str) -> bool:
        """Connect to storage."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from storage."""
        pass

    @abstractmethod
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> bool:
        """Create a table with given schema."""
        pass

    @abstractmethod
    async def insert(
        self, 
        table_name: str, 
        data: Dict[str, Any]
    ) -> Optional[str]:
        """Insert data into table."""
        pass

    @abstractmethod
    async def query(
        self, 
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query data from table."""
        pass

    @abstractmethod
    async def update(
        self, 
        table_name: str,
        conditions: Dict[str, Any],
        data: Dict[str, Any]
    ) -> bool:
        """Update data in table."""
        pass

    @abstractmethod
    async def delete(
        self, 
        table_name: str,
        conditions: Dict[str, Any]
    ) -> bool:
        """Delete data from table."""
        pass


class ICacheProvider(ABC):
    """Interface for caching providers."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache."""
        pass


class IEventProvider(ABC):
    """Interface for event publishing/subscribing."""

    @abstractmethod
    async def publish(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Publish an event."""
        pass

    @abstractmethod
    async def subscribe(
        self, 
        event_type: str, 
        handler: callable
    ) -> str:
        """Subscribe to an event type."""
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from an event."""
        pass