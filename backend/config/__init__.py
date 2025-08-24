"""
Configuration Package for Intel Virtual Assistant Backend
Contains configuration management and dependency injection.
"""

from .settings import (
    AppConfig, DatabaseConfig, ModelConfig, VoiceConfig, HardwareConfig,
    ToolsConfig, ServerConfig, SecurityConfig, LoggingConfig,
    ConfigManager, get_config_manager, get_config, reload_config
)

from .container import (
    DIContainer, get_container, reset_container,
    get_chat_service, get_model_service, get_voice_service,
    get_tool_service, get_conversation_service, get_hardware_service,
    get_health_service, initialize_services, shutdown_services,
    override_dependencies
)

__all__ = [
    # Configuration
    "AppConfig", "DatabaseConfig", "ModelConfig", "VoiceConfig", "HardwareConfig",
    "ToolsConfig", "ServerConfig", "SecurityConfig", "LoggingConfig",
    "ConfigManager", "get_config_manager", "get_config", "reload_config",
    # Dependency Injection
    "DIContainer", "get_container", "reset_container",
    "get_chat_service", "get_model_service", "get_voice_service",
    "get_tool_service", "get_conversation_service", "get_hardware_service",
    "get_health_service", "initialize_services", "shutdown_services",
    "override_dependencies"
]