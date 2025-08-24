"""
Custom exception classes for the virtual assistant.
"""

class AssistantException(Exception):
    """Base exception for the virtual assistant."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

class ModelException(AssistantException):
    """Exception related to model operations."""
    pass

class ModelLoadException(ModelException):
    """Exception when model loading fails."""
    pass

class ModelInferenceException(ModelException):
    """Exception during model inference."""
    pass

class ModelNotLoadedException(ModelException):
    """Exception when trying to use unloaded model."""
    pass

class VoiceException(AssistantException):
    """Exception related to voice operations."""
    pass

class TTSException(VoiceException):
    """Exception during text-to-speech operations."""
    pass

class STTException(VoiceException):
    """Exception during speech-to-text operations."""
    pass

class AudioFormatException(VoiceException):
    """Exception related to audio format issues."""
    pass

class ToolException(AssistantException):
    """Exception related to tool operations."""
    pass

class ToolNotFound(ToolException):
    """Exception when tool is not found."""
    pass

class ToolExecutionException(ToolException):
    """Exception during tool execution."""
    pass

class ToolAuthenticationException(ToolException):
    """Exception during tool authentication."""
    pass

class ToolTimeoutException(ToolException):
    """Exception when tool execution times out."""
    pass

class StorageException(AssistantException):
    """Exception related to storage operations."""
    pass

class ConversationNotFound(StorageException):
    """Exception when conversation is not found."""
    pass

class MessageNotFound(StorageException):
    """Exception when message is not found."""
    pass

class StorageConnectionException(StorageException):
    """Exception when storage connection fails."""
    pass

class ConfigurationException(AssistantException):
    """Exception related to configuration issues."""
    pass

class ValidationException(AssistantException):
    """Exception for validation errors."""
    pass

class AuthenticationException(AssistantException):
    """Exception for authentication errors."""
    pass

class AuthorizationException(AssistantException):
    """Exception for authorization errors."""
    pass

class RateLimitException(AssistantException):
    """Exception when rate limit is exceeded."""
    pass

class IntelHardwareException(AssistantException):
    """Exception related to Intel hardware optimization."""
    pass