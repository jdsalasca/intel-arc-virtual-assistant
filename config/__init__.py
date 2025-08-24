"""
Configuration Package
Provides centralized configuration management for the Intel AI Assistant.
"""

from .settings import (
    ApplicationSettings,
    ModelSettings,
    VoiceSettings,
    WebSettings,
    ConversationSettings,
    ToolSettings,
    SecuritySettings,
    PerformanceSettings,
    get_settings,
    initialize_settings
)

from .environment import (
    EnvironmentManager,
    OpenVINOConfig,
    IntelOptimizationConfig,
    ExternalServicesConfig,
    get_env_manager,
    initialize_environment
)

from .intel_profiles import (
    IntelProfileManager,
    IntelHardwareProfile,
    IntelProcessorType,
    IntelGPUType,
    IntelNPUType,
    HardwareCapabilities
)

__all__ = [
    # Settings classes
    "ApplicationSettings",
    "ModelSettings", 
    "VoiceSettings",
    "WebSettings",
    "ConversationSettings",
    "ToolSettings",
    "SecuritySettings",
    "PerformanceSettings",
    "get_settings",
    "initialize_settings",
    
    # Environment classes
    "EnvironmentManager",
    "OpenVINOConfig",
    "IntelOptimizationConfig", 
    "ExternalServicesConfig",
    "get_env_manager",
    "initialize_environment",
    
    # Intel profile classes
    "IntelProfileManager",
    "IntelHardwareProfile",
    "IntelProcessorType",
    "IntelGPUType", 
    "IntelNPUType",
    "HardwareCapabilities"
]