"""
Configuration Management for Intel Virtual Assistant Backend
Handles application settings and environment-specific configurations.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: str = "sqlite"
    url: str = "sqlite:///./assistant.db"
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 0


@dataclass
class ModelConfig:
    """AI model configuration."""
    default_model: str = "mistralai/Mistral-7B-Instruct-v0.3"
    cache_dir: str = "./models"
    device: str = "AUTO:CPU,NPU"
    optimization_level: str = "balanced"
    quantization: str = "int4"
    max_tokens: int = 256
    temperature: float = 0.7


@dataclass
class VoiceConfig:
    """Voice service configuration."""
    tts_model: str = "microsoft/speecht5_tts"
    vocoder_model: str = "microsoft/speecht5_hifigan"
    cache_enabled: bool = True
    max_cache_size: int = 100
    default_voice: str = "default"
    sample_rate: int = 16000


@dataclass
class HardwareConfig:
    """Hardware optimization configuration."""
    preferred_device: str = "AUTO"
    cpu_threads: int = 0  # 0 = auto-detect
    enable_gpu: bool = True
    enable_npu: bool = True
    optimization_level: str = "balanced"
    benchmark_on_startup: bool = False


@dataclass
class ToolsConfig:
    """Tools configuration."""
    enabled_tools: list = field(default_factory=lambda: ["web_search", "system_info"])
    web_search_api_key: Optional[str] = None
    gmail_credentials_path: Optional[str] = None
    timeout: float = 30.0


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    workers: int = 1
    log_level: str = "info"
    cors_origins: list = field(default_factory=lambda: ["http://localhost:3000"])


@dataclass
class SecurityConfig:
    """Security configuration."""
    api_key: Optional[str] = None
    enable_authentication: bool = False
    jwt_secret: Optional[str] = None
    jwt_expiry_minutes: int = 60


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "info"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: str = "10MB"
    backup_count: int = 5
    enable_json_logs: bool = False


@dataclass
class AppConfig:
    """Main application configuration."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Environment
    environment: str = "development"
    version: str = "1.0.0"
    app_name: str = "Intel Virtual Assistant"


class ConfigManager:
    """Configuration manager for loading and managing application settings."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        self._config_path = Path(config_path) if config_path else None
        self._config: Optional[AppConfig] = None
        
    def load_config(self) -> AppConfig:
        """Load configuration from various sources."""
        if self._config is not None:
            return self._config
            
        # Start with default configuration
        config_data = self._get_default_config()
        
        # Override with file configuration
        if self._config_path and self._config_path.exists():
            file_config = self._load_config_file(self._config_path)
            config_data = self._merge_configs(config_data, file_config)
        
        # Override with environment variables
        env_config = self._load_env_config()
        config_data = self._merge_configs(config_data, env_config)
        
        # Create configuration object
        self._config = self._create_config_object(config_data)
        
        return self._config
    
    def get_config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> AppConfig:
        """Reload configuration from sources."""
        self._config = None
        return self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        default_config = AppConfig()
        return self._config_to_dict(default_config)
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    return yaml.safe_load(f) or {}
                elif config_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
            return {}
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Server configuration
        if os.getenv("HOST"):
            env_config.setdefault("server", {})["host"] = os.getenv("HOST")
        if os.getenv("PORT"):
            env_config.setdefault("server", {})["port"] = int(os.getenv("PORT"))
        if os.getenv("DEBUG"):
            env_config.setdefault("server", {})["debug"] = os.getenv("DEBUG").lower() == "true"
        if os.getenv("LOG_LEVEL"):
            env_config.setdefault("logging", {})["level"] = os.getenv("LOG_LEVEL")
        
        # Model configuration
        if os.getenv("DEFAULT_MODEL"):
            env_config.setdefault("model", {})["default_model"] = os.getenv("DEFAULT_MODEL")
        if os.getenv("MODEL_CACHE_DIR"):
            env_config.setdefault("model", {})["cache_dir"] = os.getenv("MODEL_CACHE_DIR")
        if os.getenv("DEVICE"):
            env_config.setdefault("model", {})["device"] = os.getenv("DEVICE")
        
        # Hardware configuration
        if os.getenv("PREFERRED_DEVICE"):
            env_config.setdefault("hardware", {})["preferred_device"] = os.getenv("PREFERRED_DEVICE")
        if os.getenv("CPU_THREADS"):
            env_config.setdefault("hardware", {})["cpu_threads"] = int(os.getenv("CPU_THREADS"))
        
        # Security configuration
        if os.getenv("API_KEY"):
            env_config.setdefault("security", {})["api_key"] = os.getenv("API_KEY")
        if os.getenv("JWT_SECRET"):
            env_config.setdefault("security", {})["jwt_secret"] = os.getenv("JWT_SECRET")
        
        # Tools configuration
        if os.getenv("WEB_SEARCH_API_KEY"):
            env_config.setdefault("tools", {})["web_search_api_key"] = os.getenv("WEB_SEARCH_API_KEY")
        if os.getenv("GMAIL_CREDENTIALS_PATH"):
            env_config.setdefault("tools", {})["gmail_credentials_path"] = os.getenv("GMAIL_CREDENTIALS_PATH")
        
        # Database configuration
        if os.getenv("DATABASE_URL"):
            env_config.setdefault("database", {})["url"] = os.getenv("DATABASE_URL")
        
        # Environment
        if os.getenv("ENVIRONMENT"):
            env_config["environment"] = os.getenv("ENVIRONMENT")
        
        return env_config
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """Convert configuration object to dictionary."""
        return {
            "database": {
                "type": config.database.type,
                "url": config.database.url,
                "echo": config.database.echo,
                "pool_size": config.database.pool_size,
                "max_overflow": config.database.max_overflow
            },
            "model": {
                "default_model": config.model.default_model,
                "cache_dir": config.model.cache_dir,
                "device": config.model.device,
                "optimization_level": config.model.optimization_level,
                "quantization": config.model.quantization,
                "max_tokens": config.model.max_tokens,
                "temperature": config.model.temperature
            },
            "voice": {
                "tts_model": config.voice.tts_model,
                "vocoder_model": config.voice.vocoder_model,
                "cache_enabled": config.voice.cache_enabled,
                "max_cache_size": config.voice.max_cache_size,
                "default_voice": config.voice.default_voice,
                "sample_rate": config.voice.sample_rate
            },
            "hardware": {
                "preferred_device": config.hardware.preferred_device,
                "cpu_threads": config.hardware.cpu_threads,
                "enable_gpu": config.hardware.enable_gpu,
                "enable_npu": config.hardware.enable_npu,
                "optimization_level": config.hardware.optimization_level,
                "benchmark_on_startup": config.hardware.benchmark_on_startup
            },
            "tools": {
                "enabled_tools": config.tools.enabled_tools,
                "web_search_api_key": config.tools.web_search_api_key,
                "gmail_credentials_path": config.tools.gmail_credentials_path,
                "timeout": config.tools.timeout
            },
            "server": {
                "host": config.server.host,
                "port": config.server.port,
                "debug": config.server.debug,
                "reload": config.server.reload,
                "workers": config.server.workers,
                "log_level": config.server.log_level,
                "cors_origins": config.server.cors_origins
            },
            "security": {
                "api_key": config.security.api_key,
                "enable_authentication": config.security.enable_authentication,
                "jwt_secret": config.security.jwt_secret,
                "jwt_expiry_minutes": config.security.jwt_expiry_minutes
            },
            "logging": {
                "level": config.logging.level,
                "format": config.logging.format,
                "file_path": config.logging.file_path,
                "max_file_size": config.logging.max_file_size,
                "backup_count": config.logging.backup_count,
                "enable_json_logs": config.logging.enable_json_logs
            },
            "environment": config.environment,
            "version": config.version,
            "app_name": config.app_name
        }
    
    def _create_config_object(self, config_data: Dict[str, Any]) -> AppConfig:
        """Create configuration object from dictionary."""
        return AppConfig(
            database=DatabaseConfig(**config_data.get("database", {})),
            model=ModelConfig(**config_data.get("model", {})),
            voice=VoiceConfig(**config_data.get("voice", {})),
            hardware=HardwareConfig(**config_data.get("hardware", {})),
            tools=ToolsConfig(**config_data.get("tools", {})),
            server=ServerConfig(**config_data.get("server", {})),
            security=SecurityConfig(**config_data.get("security", {})),
            logging=LoggingConfig(**config_data.get("logging", {})),
            environment=config_data.get("environment", "development"),
            version=config_data.get("version", "1.0.0"),
            app_name=config_data.get("app_name", "Intel Virtual Assistant")
        )


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    
    return _config_manager


def get_config() -> AppConfig:
    """Get current application configuration."""
    return get_config_manager().get_config()


def reload_config() -> AppConfig:
    """Reload application configuration."""
    return get_config_manager().reload_config()