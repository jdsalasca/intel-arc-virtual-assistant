"""
Application Settings Configuration
Manages all application settings with Intel hardware optimization.
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

from .intel_profiles import IntelProfileManager, IntelHardwareProfile

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class APIProvider(Enum):
    """API providers for various services."""
    OPENAI = "openai"
    LOCAL_OPENVINO = "local_openvino"
    MISTRAL = "mistral"
    HUGGINGFACE = "huggingface"
    INTEL_NEURAL_COMPRESSOR = "intel_neural_compressor"

@dataclass
class ModelSettings:
    """Model configuration settings."""
    name: str = "mistral-7b-instruct"
    provider: APIProvider = APIProvider.LOCAL_OPENVINO
    model_path: str = ""
    device: str = "CPU"  # CPU, GPU, NPU, AUTO
    precision: str = "FP16"  # FP32, FP16, INT8, INT4
    max_tokens: int = 256
    temperature: float = 0.7
    batch_size: int = 1
    context_length: int = 2048
    enable_streaming: bool = True

@dataclass
class VoiceSettings:
    """Voice processing settings."""
    # Text-to-Speech
    tts_enabled: bool = True
    tts_model: str = "speecht5-tts"
    tts_device: str = "NPU"
    tts_voice: str = "default"
    tts_speed: float = 1.0
    tts_pitch: float = 1.0
    
    # Speech-to-Text
    stt_enabled: bool = True
    stt_model: str = "whisper-base"
    stt_device: str = "NPU"
    stt_language: str = "auto"
    stt_threshold: float = 0.5
    
    # Audio settings
    sample_rate: int = 16000
    audio_format: str = "wav"

@dataclass
class WebSettings:
    """Web interface settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    auto_reload: bool = False
    workers: int = 1
    max_connections: int = 100
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    static_path: str = "web/static"
    templates_path: str = "web/templates"

@dataclass
class ConversationSettings:
    """Conversation management settings."""
    max_history: int = 50
    context_strategy: str = "sliding_window"  # sliding_window, summarization, hybrid
    summary_threshold: int = 10
    save_conversations: bool = True
    conversations_path: str = "data/conversations"
    auto_save_interval: int = 30  # seconds

@dataclass
class ToolSettings:
    """Tool integration settings."""
    enabled_tools: List[str] = field(default_factory=lambda: ["web_search", "file_operations"])
    
    # Web search
    search_provider: str = "duckduckgo"
    max_search_results: int = 5
    
    # Gmail integration
    gmail_enabled: bool = False
    gmail_credentials_path: str = "credentials/gmail.json"
    gmail_scopes: List[str] = field(default_factory=lambda: ["https://www.googleapis.com/auth/gmail.readonly"])
    
    # File operations
    file_operations_enabled: bool = True
    allowed_file_types: List[str] = field(default_factory=lambda: [".txt", ".md", ".json", ".csv"])
    max_file_size_mb: int = 10

@dataclass
class SecuritySettings:
    """Security and privacy settings."""
    api_key_required: bool = False
    api_key: str = ""
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    
    # Data privacy
    log_conversations: bool = True
    encrypt_conversations: bool = False
    data_retention_days: int = 30

@dataclass
class PerformanceSettings:
    """Performance optimization settings."""
    enable_caching: bool = True
    cache_size_mb: int = 512
    
    # Intel optimizations
    enable_intel_optimizations: bool = True
    use_intel_mkl: bool = True
    use_intel_mkl_dnn: bool = True
    
    # OpenVINO optimizations
    enable_openvino_optimizations: bool = True
    openvino_cache_dir: str = "cache/openvino"
    enable_dynamic_shapes: bool = True
    
    # Memory management
    memory_pool_size_mb: int = 1024
    gc_threshold: int = 100

class ApplicationSettings:
    """Main application settings manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/app_settings.json"
        self.config_dir = Path(self.config_file).parent
        
        # Initialize Intel profile manager
        self.intel_profile_manager = IntelProfileManager()
        
        # Default settings
        self.model = ModelSettings()
        self.voice = VoiceSettings()
        self.web = WebSettings()
        self.conversation = ConversationSettings()
        self.tools = ToolSettings()
        self.security = SecuritySettings()
        self.performance = PerformanceSettings()
        
        # Application settings
        self.app_name = "Intel AI Assistant"
        self.app_version = "1.0.0"
        self.log_level = LogLevel.INFO
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Intel profile settings
        self.current_intel_profile: Optional[str] = None
        self.auto_detect_hardware: bool = True

        # Track whether a default config has been saved to avoid repeated writes
        self._default_config_saved: bool = False

        # Load configuration
        self.load_config()
        
        # Apply Intel profile optimizations
        if self.auto_detect_hardware:
            self._auto_configure_intel_hardware()
    
    def _auto_configure_intel_hardware(self):
        """Auto-configure settings based on detected Intel hardware."""
        try:
            # This would normally use actual hardware detection
            # For now, we'll use a simulated detection
            hardware_info = self._detect_hardware()
            
            # Auto-detect optimal profile
            profile_name = self.intel_profile_manager.auto_detect_profile(hardware_info)
            if profile_name:
                self.apply_intel_profile(profile_name)
                logger.info(f"Auto-configured for Intel profile: {profile_name}")
        except Exception as e:
            logger.error(f"Hardware auto-configuration failed: {e}")
            # Fallback to CPU-only profile
            self.apply_intel_profile("cpu_only")
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """Detect available hardware capabilities."""
        # This is a simplified simulation
        # In a real implementation, this would use platform-specific detection
        hardware_info = {
            "cpu": {
                "threads": os.cpu_count() or 8,
                "architecture": "x86_64"
            },
            "arc_gpu": {
                "available": False,  # Would be detected via OpenVINO or system queries
                "memory": 0
            },
            "npu": {
                "available": False   # Would be detected via Intel AI tools
            }
        }
        
        # Check environment variables for testing
        if os.getenv("INTEL_ARC_GPU_AVAILABLE") == "true":
            hardware_info["arc_gpu"]["available"] = True
            hardware_info["arc_gpu"]["memory"] = int(os.getenv("INTEL_ARC_GPU_MEMORY", "8192"))
        
        if os.getenv("INTEL_NPU_AVAILABLE") == "true":
            hardware_info["npu"]["available"] = True
        
        return hardware_info
    
    def apply_intel_profile(self, profile_name: str) -> bool:
        """Apply Intel hardware profile settings."""
        profile = self.intel_profile_manager.get_profile(profile_name)
        if not profile:
            logger.error(f"Intel profile not found: {profile_name}")
            return False
        
        # Apply model settings
        recommendations = self.intel_profile_manager.optimize_for_profile(profile_name)
        
        if "models" in recommendations:
            models = recommendations["models"]
            if "primary" in models:
                self.model.name = models["primary"]
            
            # Configure voice models
            if "tts" in models:
                self.voice.tts_model = models["tts"]
            if "stt" in models:
                self.voice.stt_model = models["stt"]
        
        # Apply device preferences
        model_config = self.intel_profile_manager.get_model_config(self.model.name, profile_name)
        if model_config:
            self.model.device = model_config.get("preferred_device", "CPU")
            self.model.batch_size = model_config.get("batch_size", 1)
            self.model.max_tokens = model_config.get("max_tokens", 256)
            self.model.temperature = model_config.get("temperature", 0.7)
            self.model.precision = model_config.get("precision", "FP16")
        
        # Apply voice device settings
        if "settings" in recommendations:
            settings = recommendations["settings"]
            if "voice_device" in settings:
                self.voice.tts_device = settings["voice_device"]
                self.voice.stt_device = settings["voice_device"]
            
            if "performance_mode" in settings:
                self._apply_performance_mode(settings["performance_mode"])
        
        # Update current profile
        self.current_intel_profile = profile_name
        self.intel_profile_manager.set_current_profile(profile_name)
        
        logger.info(f"Applied Intel profile: {profile_name}")
        return True
    
    def _apply_performance_mode(self, mode: str):
        """Apply performance mode settings."""
        if mode == "max_performance":
            self.performance.enable_intel_optimizations = True
            self.performance.enable_openvino_optimizations = True
            self.performance.memory_pool_size_mb = 2048
            self.performance.cache_size_mb = 1024
        elif mode == "balanced":
            self.performance.enable_intel_optimizations = True
            self.performance.enable_openvino_optimizations = True
            self.performance.memory_pool_size_mb = 1024
            self.performance.cache_size_mb = 512
        elif mode == "power_efficient":
            self.performance.enable_intel_optimizations = True
            self.performance.enable_openvino_optimizations = False
            self.performance.memory_pool_size_mb = 512
            self.performance.cache_size_mb = 256
    
    def get_intel_profile_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current Intel profile."""
        if not self.current_intel_profile:
            return None
        
        return self.intel_profile_manager.get_profile_details(self.current_intel_profile)
    
    def list_available_intel_profiles(self) -> List[str]:
        """List available Intel profiles."""
        return self.intel_profile_manager.list_profiles()
    
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load settings from config data
                self._apply_config_data(config_data)
                logger.info(f"Configuration loaded from: {self.config_file}")
                return True
            else:
                logger.info(f"Configuration file not found: {self.config_file}")
                # Create default config only once
                if not self._default_config_saved:
                    self.save_config()
                    self._default_config_saved = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to settings."""
        # Apply top-level settings
        if "app_name" in config_data:
            self.app_name = config_data["app_name"]
        if "app_version" in config_data:
            self.app_version = config_data["app_version"]
        if "log_level" in config_data:
            # Handle both string and enum values
            log_level = config_data["log_level"]
            if isinstance(log_level, str):
                self.log_level = LogLevel(log_level)
            else:
                self.log_level = log_level
        if "environment" in config_data:
            self.environment = config_data["environment"]
        if "auto_detect_hardware" in config_data:
            self.auto_detect_hardware = config_data["auto_detect_hardware"]
        
        # Apply Intel profile first so explicit config values can override recommendations
        profile_name = config_data.get("current_intel_profile")
        if profile_name:
            self.apply_intel_profile(profile_name)

        # Apply model settings
        if "model" in config_data:
            model_data = config_data["model"]
            for key, value in model_data.items():
                if hasattr(self.model, key):
                    # Handle enum fields
                    if key == "provider" and isinstance(value, str):
                        try:
                            self.model.provider = APIProvider(value)
                        except ValueError:
                            logger.warning(f"Unknown provider '{value}', using LOCAL_OPENVINO")
                            self.model.provider = APIProvider.LOCAL_OPENVINO
                    else:
                        setattr(self.model, key, value)
        
        # Apply voice settings
        if "voice" in config_data:
            voice_data = config_data["voice"]
            for key, value in voice_data.items():
                if hasattr(self.voice, key):
                    setattr(self.voice, key, value)
        
        # Apply web settings
        if "web" in config_data:
            web_data = config_data["web"]
            for key, value in web_data.items():
                if hasattr(self.web, key):
                    setattr(self.web, key, value)
        
        # Apply conversation settings
        if "conversation" in config_data:
            conv_data = config_data["conversation"]
            for key, value in conv_data.items():
                if hasattr(self.conversation, key):
                    setattr(self.conversation, key, value)
        
        # Apply tools settings
        if "tools" in config_data:
            tools_data = config_data["tools"]
            for key, value in tools_data.items():
                if hasattr(self.tools, key):
                    setattr(self.tools, key, value)
        
        # Apply performance settings
        if "performance" in config_data:
            perf_data = config_data["performance"]
            for key, value in perf_data.items():
                if hasattr(self.performance, key):
                    setattr(self.performance, key, value)
        
        # Apply Intel profile
        if "current_intel_profile" in config_data:
            profile_name = config_data["current_intel_profile"]
            self.apply_intel_profile(profile_name)
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            # Ensure config directory exists
            os.makedirs(self.config_dir, exist_ok=True)
            
            config_data = self.to_dict()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logger.info(f"Configuration saved to: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary format."""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "log_level": self.log_level.value,
            "environment": self.environment,
            "current_intel_profile": self.current_intel_profile,
            "auto_detect_hardware": self.auto_detect_hardware,
            "model": {
                "name": self.model.name,
                "provider": getattr(self.model.provider, "value", self.model.provider),
                "device": self.model.device,
                "precision": self.model.precision,
                "max_tokens": self.model.max_tokens,
                "temperature": self.model.temperature,
                "batch_size": self.model.batch_size,
                "context_length": self.model.context_length,
                "enable_streaming": self.model.enable_streaming
            },
            "voice": {
                "tts_enabled": self.voice.tts_enabled,
                "tts_model": self.voice.tts_model,
                "tts_device": self.voice.tts_device,
                "stt_enabled": self.voice.stt_enabled,
                "stt_model": self.voice.stt_model,
                "stt_device": self.voice.stt_device
            },
            "web": {
                "host": self.web.host,
                "port": self.web.port,
                "debug": self.web.debug,
                "workers": self.web.workers
            },
            "conversation": {
                "max_history": self.conversation.max_history,
                "context_strategy": self.conversation.context_strategy,
                "save_conversations": self.conversation.save_conversations
            },
            "tools": {
                "enabled_tools": self.tools.enabled_tools,
                "gmail_enabled": self.tools.gmail_enabled
            },
            "performance": {
                "enable_intel_optimizations": self.performance.enable_intel_optimizations,
                "enable_openvino_optimizations": self.performance.enable_openvino_optimizations,
                "memory_pool_size_mb": self.performance.memory_pool_size_mb
            }
        }
    
    def update_setting(self, category: str, key: str, value: Any) -> bool:
        """Update a specific setting."""
        try:
            if hasattr(self, category):
                setting_obj = getattr(self, category)
                if hasattr(setting_obj, key):
                    setattr(setting_obj, key, value)
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to update setting {category}.{key}: {e}")
            return False
    
    def get_setting(self, category: str, key: str) -> Any:
        """Get a specific setting value."""
        try:
            if hasattr(self, category):
                setting_obj = getattr(self, category)
                if hasattr(setting_obj, key):
                    return getattr(setting_obj, key)
            return None
        except Exception as e:
            logger.error(f"Failed to get setting {category}.{key}: {e}")
            return None
    
    def validate_settings(self) -> List[str]:
        """Validate current settings and return any issues."""
        issues = []
        
        # Validate model settings
        if not self.model.name:
            issues.append("Model name is required")
        
        if self.model.max_tokens <= 0:
            issues.append("Max tokens must be positive")
        
        if not (0.0 <= self.model.temperature <= 2.0):
            issues.append("Temperature must be between 0.0 and 2.0")
        
        # Validate web settings
        if not (1 <= self.web.port <= 65535):
            issues.append("Web port must be between 1 and 65535")
        
        # Validate paths
        if self.conversation.save_conversations:
            directory = os.path.dirname(self.conversation.conversations_path)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        return issues

# Global settings instance
settings: Optional[ApplicationSettings] = None

def get_settings() -> ApplicationSettings:
    """Get the global settings instance."""
    global settings
    if settings is None:
        settings = ApplicationSettings()
    return settings

def initialize_settings(config_file: Optional[str] = None) -> ApplicationSettings:
    """Initialize the global settings instance."""
    global settings
    settings = ApplicationSettings(config_file)
    return settings