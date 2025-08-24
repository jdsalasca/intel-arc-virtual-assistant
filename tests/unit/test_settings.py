"""
Unit Tests for Application Settings
Tests the main application configuration system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from config.settings import (
    ApplicationSettings,
    ModelSettings,
    VoiceSettings,
    WebSettings,
    ConversationSettings,
    ToolSettings,
    SecuritySettings,
    PerformanceSettings,
    LogLevel,
    APIProvider
)

class TestModelSettings:
    """Test ModelSettings dataclass."""
    
    def test_default_initialization(self):
        """Test default initialization of ModelSettings."""
        settings = ModelSettings()
        
        assert settings.name == "phi-3-mini-int4"
        assert settings.provider == APIProvider.LOCAL_OPENVINO
        assert settings.device == "CPU"
        assert settings.precision == "FP16"
        assert settings.max_tokens == 256
        assert settings.temperature == 0.7
        assert settings.batch_size == 1
        assert settings.context_length == 2048
        assert settings.enable_streaming is True
    
    def test_custom_initialization(self):
        """Test custom initialization with parameters."""
        settings = ModelSettings(
            name="custom-model",
            provider=APIProvider.OPENAI,
            device="GPU",
            precision="INT4",
            max_tokens=512,
            temperature=0.5
        )
        
        assert settings.name == "custom-model"
        assert settings.provider == APIProvider.OPENAI
        assert settings.device == "GPU"
        assert settings.precision == "INT4"
        assert settings.max_tokens == 512
        assert settings.temperature == 0.5

class TestVoiceSettings:
    """Test VoiceSettings dataclass."""
    
    def test_default_initialization(self):
        """Test default voice settings."""
        settings = VoiceSettings()
        
        assert settings.tts_enabled is True
        assert settings.tts_model == "speecht5-tts"
        assert settings.tts_device == "NPU"
        assert settings.stt_enabled is True
        assert settings.stt_model == "whisper-base"
        assert settings.stt_device == "NPU"
        assert settings.sample_rate == 16000

class TestApplicationSettings:
    """Test ApplicationSettings main class."""
    
    def test_initialization_without_config_file(self, temp_dir):
        """Test initialization without existing config file."""
        config_file = temp_dir / "test_config.json"
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings(str(config_file))
        
        assert settings.app_name == "Intel AI Assistant"
        assert settings.app_version == "1.0.0"
        assert settings.log_level == LogLevel.INFO
        assert settings.current_intel_profile is None
        assert settings.auto_detect_hardware is True
    
    def test_initialization_with_config_file(self, test_config_file):
        """Test initialization with existing config file."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings(str(test_config_file))
        
        assert settings.app_name == "Test Assistant"
        assert settings.app_version == "0.1.0"
        assert settings.model.name == "test-model"
        assert settings.web.port == 8001
    
    @patch('config.settings.ApplicationSettings._detect_hardware')
    @patch('config.settings.IntelProfileManager')
    def test_auto_configure_intel_hardware(self, mock_profile_manager, mock_detect_hardware):
        """Test auto-configuration of Intel hardware."""
        # Setup mocks
        mock_hardware = {
            "cpu": {"threads": 16},
            "arc_gpu": {"available": True, "memory": 8192},
            "npu": {"available": False}
        }
        mock_detect_hardware.return_value = mock_hardware
        
        mock_manager_instance = Mock()
        mock_manager_instance.auto_detect_profile.return_value = "ultra7_arc750_npu"
        mock_profile_manager.return_value = mock_manager_instance
        
        with patch('config.settings.ApplicationSettings.apply_intel_profile') as mock_apply:
            settings = ApplicationSettings()
            mock_apply.assert_called_once_with("ultra7_arc750_npu")
    
    def test_detect_hardware(self):
        """Test hardware detection method."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        with patch('os.cpu_count', return_value=8):
            hardware_info = settings._detect_hardware()
        
        assert "cpu" in hardware_info
        assert "arc_gpu" in hardware_info
        assert "npu" in hardware_info
        assert hardware_info["cpu"]["threads"] == 8
        assert hardware_info["cpu"]["architecture"] == "x86_64"
    
    def test_detect_hardware_with_env_vars(self):
        """Test hardware detection with environment variables."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        with patch.dict('os.environ', {
            'INTEL_ARC_GPU_AVAILABLE': 'true',
            'INTEL_ARC_GPU_MEMORY': '16384',
            'INTEL_NPU_AVAILABLE': 'true'
        }):
            with patch('os.cpu_count', return_value=16):
                hardware_info = settings._detect_hardware()
        
        assert hardware_info["arc_gpu"]["available"] is True
        assert hardware_info["arc_gpu"]["memory"] == 16384
        assert hardware_info["npu"]["available"] is True
    
    @patch('config.settings.IntelProfileManager')
    def test_apply_intel_profile_success(self, mock_profile_manager):
        """Test successful Intel profile application."""
        # Setup mock profile manager
        mock_manager_instance = Mock()
        mock_profile = Mock()
        mock_manager_instance.get_profile.return_value = mock_profile
        mock_manager_instance.optimize_for_profile.return_value = {
            "models": {"primary": "qwen2.5-7b-int4"},
            "settings": {"voice_device": "NPU", "performance_mode": "balanced"}
        }
        mock_manager_instance.get_model_config.return_value = {
            "preferred_device": "GPU",
            "batch_size": 2,
            "precision": "INT4"
        }
        mock_profile_manager.return_value = mock_manager_instance
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        success = settings.apply_intel_profile("ultra7_arc770_npu")
        
        assert success is True
        assert settings.current_intel_profile == "ultra7_arc770_npu"
        assert settings.model.name == "qwen2.5-7b-int4"
        assert settings.model.device == "GPU"
        assert settings.model.precision == "INT4"
        assert settings.voice.tts_device == "NPU"
    
    @patch('config.settings.IntelProfileManager')
    def test_apply_intel_profile_failure(self, mock_profile_manager):
        """Test failed Intel profile application."""
        mock_manager_instance = Mock()
        mock_manager_instance.get_profile.return_value = None
        mock_profile_manager.return_value = mock_manager_instance
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        success = settings.apply_intel_profile("nonexistent_profile")
        
        assert success is False
    
    def test_apply_performance_mode(self):
        """Test applying different performance modes."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        # Test max performance mode
        settings._apply_performance_mode("max_performance")
        assert settings.performance.memory_pool_size_mb == 2048
        assert settings.performance.cache_size_mb == 1024
        assert settings.performance.enable_intel_optimizations is True
        
        # Test balanced mode
        settings._apply_performance_mode("balanced")
        assert settings.performance.memory_pool_size_mb == 1024
        assert settings.performance.cache_size_mb == 512
        
        # Test power efficient mode
        settings._apply_performance_mode("power_efficient")
        assert settings.performance.memory_pool_size_mb == 512
        assert settings.performance.cache_size_mb == 256
        assert settings.performance.enable_openvino_optimizations is False
    
    @patch('config.settings.IntelProfileManager')
    def test_get_intel_profile_info(self, mock_profile_manager):
        """Test getting Intel profile information."""
        mock_manager_instance = Mock()
        mock_profile_info = {"name": "Test Profile", "description": "Test"}
        mock_manager_instance.get_profile_details.return_value = mock_profile_info
        mock_profile_manager.return_value = mock_manager_instance
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        settings.current_intel_profile = "test_profile"
        info = settings.get_intel_profile_info()
        
        assert info == mock_profile_info
        
        # Test without current profile
        settings.current_intel_profile = None
        info = settings.get_intel_profile_info()
        assert info is None
    
    def test_load_config_nonexistent_file(self, temp_dir):
        """Test loading config from nonexistent file."""
        config_file = temp_dir / "nonexistent.json"
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            with patch('config.settings.ApplicationSettings.save_config') as mock_save:
                settings = ApplicationSettings(str(config_file))
                success = settings.load_config()
        
        assert success is True
        mock_save.assert_called_once()
    
    def test_load_config_existing_file(self, test_config_file):
        """Test loading config from existing file."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings(str(test_config_file))
            success = settings.load_config()
        
        assert success is True
        assert settings.app_name == "Test Assistant"
    
    def test_load_config_invalid_json(self, temp_dir):
        """Test loading config from invalid JSON file."""
        config_file = temp_dir / "invalid.json"
        config_file.write_text("invalid json content")
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings(str(config_file))
            success = settings.load_config()
        
        assert success is False
    
    def test_save_config(self, temp_dir):
        """Test saving configuration to file."""
        config_file = temp_dir / "save_test.json"
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings(str(config_file))
            settings.app_name = "Test Save"
            success = settings.save_config()
        
        assert success is True
        assert config_file.exists()
        
        # Verify saved content
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["app_name"] == "Test Save"
    
    def test_to_dict(self):
        """Test converting settings to dictionary."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        config_dict = settings.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "app_name" in config_dict
        assert "model" in config_dict
        assert "voice" in config_dict
        assert "web" in config_dict
        assert "conversation" in config_dict
        assert "tools" in config_dict
        assert "performance" in config_dict
        
        # Test nested structure
        assert isinstance(config_dict["model"], dict)
        assert "name" in config_dict["model"]
        assert "provider" in config_dict["model"]
    
    def test_update_setting_success(self):
        """Test successfully updating a setting."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        success = settings.update_setting("model", "temperature", 0.5)
        assert success is True
        assert settings.model.temperature == 0.5
        
        success = settings.update_setting("web", "port", 9000)
        assert success is True
        assert settings.web.port == 9000
    
    def test_update_setting_failure(self):
        """Test failed setting update."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        # Invalid category
        success = settings.update_setting("invalid_category", "key", "value")
        assert success is False
        
        # Invalid key
        success = settings.update_setting("model", "invalid_key", "value")
        assert success is False
    
    def test_get_setting_success(self):
        """Test successfully getting a setting."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        value = settings.get_setting("model", "temperature")
        assert value == 0.7
        
        value = settings.get_setting("web", "port")
        assert value == 8000
    
    def test_get_setting_failure(self):
        """Test failed setting retrieval."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        # Invalid category
        value = settings.get_setting("invalid_category", "key")
        assert value is None
        
        # Invalid key
        value = settings.get_setting("model", "invalid_key")
        assert value is None
    
    def test_validate_settings_valid(self):
        """Test validation with valid settings."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        issues = settings.validate_settings()
        assert isinstance(issues, list)
        # Should have no issues with default settings
        assert len(issues) == 0
    
    def test_validate_settings_invalid(self):
        """Test validation with invalid settings."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        # Set invalid values
        settings.model.name = ""
        settings.model.max_tokens = -1
        settings.model.temperature = 5.0
        settings.web.port = 70000
        
        issues = settings.validate_settings()
        assert len(issues) > 0
        
        issue_text = " ".join(issues)
        assert "Model name is required" in issue_text
        assert "Max tokens must be positive" in issue_text
        assert "Temperature must be between" in issue_text
        assert "Web port must be between" in issue_text

@pytest.mark.parametrize("log_level", [
    LogLevel.DEBUG,
    LogLevel.INFO,
    LogLevel.WARNING,
    LogLevel.ERROR,
    LogLevel.CRITICAL
])
def test_log_levels(log_level):
    """Test different log levels."""
    with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
        settings = ApplicationSettings()
        settings.log_level = log_level
        
        assert settings.log_level == log_level
        assert isinstance(settings.log_level.value, str)

@pytest.mark.parametrize("api_provider", [
    APIProvider.OPENAI,
    APIProvider.LOCAL_OPENVINO,
    APIProvider.HUGGINGFACE,
    APIProvider.INTEL_NEURAL_COMPRESSOR
])
def test_api_providers(api_provider):
    """Test different API providers."""
    with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
        settings = ApplicationSettings()
        settings.model.provider = api_provider
        
        assert settings.model.provider == api_provider
        assert isinstance(settings.model.provider.value, str)

def test_get_settings_singleton():
    """Test global settings singleton."""
    from config.settings import get_settings, settings as global_settings
    
    # Reset global instance
    import config.settings
    config.settings.settings = None
    
    with patch('config.settings.ApplicationSettings') as mock_settings:
        mock_instance = Mock()
        mock_settings.return_value = mock_instance
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should return same instance
        assert settings1 is settings2
        # Should only initialize once
        mock_settings.assert_called_once()

def test_initialize_settings():
    """Test settings initialization function."""
    from config.settings import initialize_settings
    
    with patch('config.settings.ApplicationSettings') as mock_settings:
        mock_instance = Mock()
        mock_settings.return_value = mock_instance
        
        settings = initialize_settings("test_config.json")
        
        mock_settings.assert_called_once_with("test_config.json")
        assert settings is mock_instance