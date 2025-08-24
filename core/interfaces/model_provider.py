"""
Core interfaces for model providers.
Defines abstractions for different types of AI models and inference engines.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator, Union
from enum import Enum

class DeviceType(Enum):
    """Supported device types for inference."""
    CPU = "CPU"
    GPU = "GPU"
    NPU = "NPU"
    AUTO = "AUTO"

class ModelType(Enum):
    """Types of AI models supported."""
    LLM = "llm"
    TTS = "tts"
    STT = "stt"
    VISION = "vision"
    EMBEDDING = "embedding"

class IModelProvider(ABC):
    """Abstract interface for model providers."""
    
    @abstractmethod
    def load_model(self, model_path: str, device: DeviceType, **kwargs) -> bool:
        """Load a model for inference."""
        pass
    
    @abstractmethod
    def unload_model(self) -> bool:
        """Unload the current model."""
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        pass
    
    @abstractmethod
    def get_supported_devices(self) -> List[DeviceType]:
        """Get list of supported devices."""
        pass

class ITextGenerator(ABC):
    """Abstract interface for text generation models."""
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Generate text from a prompt."""
        pass
    
    @abstractmethod
    def generate_stream(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Generate text with streaming."""
        pass

class IChatModel(ABC):
    """Abstract interface for chat-based models."""
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response for chat messages."""
        pass
    
    @abstractmethod
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """Generate chat response with streaming."""
        pass

class IVisionModel(ABC):
    """Abstract interface for vision models."""
    
    @abstractmethod
    def describe_image(self, image_path: str, prompt: Optional[str] = None) -> str:
        """Generate description for an image."""
        pass
    
    @abstractmethod
    def answer_visual_question(self, image_path: str, question: str) -> str:
        """Answer questions about an image."""
        pass

class IEmbeddingModel(ABC):
    """Abstract interface for embedding models."""
    
    @abstractmethod
    def encode(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text(s)."""
        pass
    
    @abstractmethod
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        pass