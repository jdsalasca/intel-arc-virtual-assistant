"""
Integration Tests for Configuration System
Tests the complete configuration system integration including API endpoints.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from config import ApplicationSettings, EnvironmentManager

class TestConfigurationAPI:
    """Test configuration API endpoints."""
    
    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app with configuration routes."""
        from fastapi import FastAPI
        from api.routes.health import router
        
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/health")
        
        return app
    
    @pytest.fixture
    def client(self, mock_app):
        """Create test client."""
        return TestClient(mock_app)
    
    @pytest.fixture
    def mock_settings(self):
        """Mock application settings."""
        settings = Mock(spec=ApplicationSettings)
        settings.current_intel_profile = "ultra7_arc770_npu"
        settings.app_version = "1.0.0"
        settings.model.name = "qwen2.5-7b-int4"
        settings.model.device = "GPU"
        settings.voice.tts_enabled = True
        settings.voice.stt_enabled = True
        settings.tools.enabled_tools = ["web_search", "file_operations"]
        settings.list_available_intel_profiles.return_value = [
            "ultra7_arc770_npu", "ultra7_arc750_npu", "cpu_only"
        ]
        settings.get_intel_profile_info.return_value = {
            "name": "Intel Core Ultra 7 + Arc A770 + NPU",
            "description": "High-performance setup",
            "capabilities": {
                "cpu": {"performance": "ultra"},
                "gpu": {"performance": "ultra"},
                "npu": {"performance": "high"}
            }
        }
        return settings
    
    @pytest.fixture
    def mock_env_manager(self):
        """Mock environment manager."""
        env_manager = Mock(spec=EnvironmentManager)
        env_manager.get_system_info.return_value = {
            "hardware": {
                "cpu_count": 16,
                "cpu_count_logical": 32,
                "memory_total_gb": 32.0,
                "memory_available_gb": 16.0
            },
            "platform": {
                "platform": "Windows-10",
                "architecture": ["AMD64", "WindowsPE"],
                "processor": "Intel64 Family 6 Model 183 Stepping 1, GenuineIntel",
                "python_version": "3.11.0"
            },
            "environment": {
                "openvino_device": "GPU",
                "mkl_threads": 0
            }
        }
        env_manager.validate_environment.return_value = {
            "valid": True,
            "errors": [],
            "warnings": ["HuggingFace token not configured"],
            "info": ["OpenVINO version: 2024.0.0"]
        }
        return env_manager
    
    @patch('api.routes.health.get_settings')
    @patch('api.routes.health.get_env_manager')
    def test_health_status_endpoint(self, mock_get_env, mock_get_settings, client, mock_settings, mock_env_manager):
        """Test health status endpoint."""
        mock_get_settings.return_value = mock_settings
        mock_get_env.return_value = mock_env_manager
        
        response = client.get("/api/v1/health/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert "hardware" in data
        assert "configuration" in data
        
        # Check hardware info
        hardware = data["hardware"]
        assert hardware["cpu"]["available"] is True
        assert hardware["cpu"]["cores"] == 16
        assert hardware["memory"]["total_gb"] == 32.0
        
        # Check configuration info
        config = data["configuration"]
        assert config["current_profile"] == "ultra7_arc770_npu"
        assert config["model"] == "qwen2.5-7b-int4"
        assert config["voice_enabled"] is True
    
    @patch('api.routes.health.get_env_manager')
    def test_hardware_info_endpoint(self, mock_get_env, client, mock_env_manager):
        """Test hardware info endpoint."""
        mock_get_env.return_value = mock_env_manager
        
        response = client.get("/api/v1/health/hardware")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cpu" in data
        assert "gpu" in data
        assert "npu" in data
        assert "memory" in data
        assert "system" in data
        
        # Check CPU info
        cpu = data["cpu"]
        assert cpu["cores"] == 16
        assert cpu["threads"] == 32
        assert "architecture" in cpu
        
        # Check memory info
        memory = data["memory"]
        assert memory["total_gb"] == 32.0
        assert memory["available_gb"] == 16.0
        assert memory["usage_percent"] == 50.0
    
    @patch('api.routes.health.get_settings')
    def test_configuration_endpoint(self, mock_get_settings, client, mock_settings):
        """Test configuration endpoint."""
        mock_get_settings.return_value = mock_settings
        
        response = client.get("/api/v1/health/configuration")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["current_profile"] == "ultra7_arc770_npu"
        assert "ultra7_arc770_npu" in data["available_profiles"]
        assert "model_settings" in data
        assert "voice_settings" in data
        assert "performance_settings" in data
        
        # Check model settings
        model = data["model_settings"]
        assert model["name"] == "qwen2.5-7b-int4"
        assert model["device"] == "GPU"
    
    @patch('api.routes.health.get_settings')
    def test_list_profiles_endpoint(self, mock_get_settings, client, mock_settings):
        """Test list profiles endpoint."""
        mock_get_settings.return_value = mock_settings
        
        response = client.get("/api/v1/health/profiles")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "profiles" in data
        profiles = data["profiles"]
        assert len(profiles) == 3
        
        # Check profile structure
        for profile in profiles:
            assert "name" in profile
            assert "description" in profile
            assert "current" in profile
    
    @patch('api.routes.health.get_settings')
    def test_get_profile_details_endpoint(self, mock_get_settings, client, mock_settings):
        """Test get profile details endpoint."""
        mock_settings.intel_profile_manager.get_profile_details.return_value = {
            "name": "Intel Core Ultra 7 + Arc A770 + NPU",
            "description": "High-performance setup",
            "capabilities": {"cpu": {"performance": "ultra"}}
        }
        mock_get_settings.return_value = mock_settings
        
        response = client.get("/api/v1/health/profiles/ultra7_arc770_npu")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Intel Core Ultra 7 + Arc A770 + NPU"
        assert data["description"] == "High-performance setup"
        assert "capabilities" in data
    
    @patch('api.routes.health.get_settings')
    def test_get_profile_details_not_found(self, mock_get_settings, client, mock_settings):
        """Test get profile details for non-existent profile."""
        mock_settings.intel_profile_manager.get_profile_details.return_value = None
        mock_get_settings.return_value = mock_settings
        
        response = client.get("/api/v1/health/profiles/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "Profile not found" in data["detail"]
    
    @patch('api.routes.health.get_settings')
    def test_apply_profile_endpoint_success(self, mock_get_settings, client, mock_settings):
        """Test successful profile application."""
        mock_settings.apply_intel_profile.return_value = True
        mock_settings.save_config.return_value = True
        mock_get_settings.return_value = mock_settings
        
        response = client.post("/api/v1/health/profiles/ultra7_arc770_npu/apply")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "Successfully applied profile" in data["message"]
        assert data["current_profile"] == "ultra7_arc770_npu"
        
        mock_settings.apply_intel_profile.assert_called_once_with("ultra7_arc770_npu")
        mock_settings.save_config.assert_called_once()
    
    @patch('api.routes.health.get_settings')
    def test_apply_profile_endpoint_failure(self, mock_get_settings, client, mock_settings):
        """Test failed profile application."""
        mock_settings.apply_intel_profile.return_value = False
        mock_get_settings.return_value = mock_settings
        
        response = client.post("/api/v1/health/profiles/invalid_profile/apply")
        
        assert response.status_code == 400
        data = response.json()
        assert "Failed to apply profile" in data["detail"]
    
    @patch('api.routes.health.get_settings')
    def test_update_setting_endpoint_success(self, mock_get_settings, client, mock_settings):
        """Test successful setting update."""
        mock_settings.update_setting.return_value = True
        mock_settings.save_config.return_value = True
        mock_get_settings.return_value = mock_settings
        
        request_data = {
            "category": "model",
            "key": "temperature",
            "value": 0.5
        }
        
        response = client.put("/api/v1/health/settings", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "Setting updated" in data["message"]
        assert data["value"] == 0.5
        
        mock_settings.update_setting.assert_called_once_with("model", "temperature", 0.5)
        mock_settings.save_config.assert_called_once()
    
    @patch('api.routes.health.get_settings')
    def test_update_setting_endpoint_failure(self, mock_get_settings, client, mock_settings):
        """Test failed setting update."""
        mock_settings.update_setting.return_value = False
        mock_get_settings.return_value = mock_settings
        
        request_data = {
            "category": "invalid",
            "key": "invalid",
            "value": "invalid"
        }
        
        response = client.put("/api/v1/health/settings", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Failed to update setting" in data["detail"]
    
    @patch('api.routes.health.get_settings')
    def test_get_setting_endpoint_success(self, mock_get_settings, client, mock_settings):
        """Test successful setting retrieval."""
        mock_settings.get_setting.return_value = 0.7
        mock_get_settings.return_value = mock_settings
        
        response = client.get("/api/v1/health/settings/model/temperature")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["category"] == "model"
        assert data["key"] == "temperature"
        assert data["value"] == 0.7
        
        mock_settings.get_setting.assert_called_once_with("model", "temperature")
    
    @patch('api.routes.health.get_settings')
    def test_get_setting_endpoint_not_found(self, mock_get_settings, client, mock_settings):
        """Test setting retrieval for non-existent setting."""
        mock_settings.get_setting.return_value = None
        mock_get_settings.return_value = mock_settings
        
        response = client.get("/api/v1/health/settings/invalid/invalid")
        
        assert response.status_code == 404
        data = response.json()
        assert "Setting not found" in data["detail"]
    
    @patch('api.routes.health.get_settings')
    @patch('api.routes.health.get_env_manager')
    def test_validate_configuration_endpoint(self, mock_get_env, mock_get_settings, client, mock_settings, mock_env_manager):
        """Test configuration validation endpoint."""
        mock_settings.validate_settings.return_value = ["Model name is required"]
        mock_env_manager.validate_environment.return_value = {
            "valid": False,
            "errors": ["OpenVINO not installed"],
            "warnings": ["GPU not detected"],
            "info": ["Using CPU device"]
        }
        mock_get_settings.return_value = mock_settings
        mock_get_env.return_value = mock_env_manager
        
        response = client.post("/api/v1/health/validate")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False
        assert "Model name is required" in data["settings_issues"]
        assert "OpenVINO not installed" in data["environment_issues"]
        assert "GPU not detected" in data["warnings"]
        assert "Using CPU device" in data["info"]
    
    @patch('api.routes.health.get_settings')
    @patch('api.routes.health.get_env_manager')
    def test_export_configuration_endpoint(self, mock_get_env, mock_get_settings, client, mock_settings, mock_env_manager):
        """Test configuration export endpoint."""
        mock_config_dict = {
            "app_name": "Intel AI Assistant",
            "model": {"name": "qwen2.5-7b-int4"}
        }
        mock_settings.to_dict.return_value = mock_config_dict
        mock_env_manager.export_environment_file.return_value = True
        mock_get_settings.return_value = mock_settings
        mock_get_env.return_value = mock_env_manager
        
        response = client.post("/api/v1/health/export")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["configuration"] == mock_config_dict
        assert data["environment_exported"] is True
        assert "timestamp" in data
        
        mock_settings.to_dict.assert_called_once()
        mock_env_manager.export_environment_file.assert_called_once_with(".env.exported")

class TestConfigurationIntegration:
    """Test complete configuration system integration."""
    
    def test_settings_and_environment_integration(self, temp_dir):
        """Test integration between settings and environment manager."""
        config_file = temp_dir / "integration_test.json"
        
        # Create test environment
        import os
        with patch.dict(os.environ, {
            'MODEL_CACHE_DIR': str(temp_dir / 'models'),
            'OPENVINO_DEVICE': 'GPU',
            'MKL_NUM_THREADS': '8'
        }):
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                from config import initialize_settings, initialize_environment
                
                # Initialize both systems
                env_manager = initialize_environment()
                settings = initialize_settings(str(config_file))
                
                # Test integration
                assert env_manager.openvino.inference_device == "GPU"
                assert env_manager.intel_optimization.mkl_num_threads == 8
                assert settings.config_file == str(config_file)
    
    def test_intel_profile_model_configuration_integration(self):
        """Test integration between Intel profiles and model configuration."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        # Apply a profile and check model configuration
        with patch.object(settings.intel_profile_manager, 'get_profile') as mock_get_profile:
            mock_profile = Mock()
            mock_get_profile.return_value = mock_profile
            
            with patch.object(settings.intel_profile_manager, 'optimize_for_profile') as mock_optimize:
                mock_optimize.return_value = {
                    "models": {"primary": "qwen2.5-7b-int4"},
                    "settings": {"voice_device": "NPU"}
                }
                
                with patch.object(settings.intel_profile_manager, 'get_model_config') as mock_get_config:
                    mock_get_config.return_value = {
                        "preferred_device": "GPU",
                        "precision": "INT4",
                        "batch_size": 4
                    }
                    
                    success = settings.apply_intel_profile("ultra7_arc770_npu")
                    
                    assert success is True
                    assert settings.model.name == "qwen2.5-7b-int4"
                    assert settings.model.device == "GPU"
                    assert settings.model.precision == "INT4"
                    assert settings.model.batch_size == 4
                    assert settings.voice.tts_device == "NPU"
    
    def test_configuration_persistence_integration(self, temp_dir):
        """Test configuration persistence and loading."""
        config_file = temp_dir / "persistence_test.json"
        
        # Create and configure settings
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings1 = ApplicationSettings(str(config_file))
            settings1.app_name = "Test Persistence"
            settings1.model.temperature = 0.8
            settings1.web.port = 9000
            settings1.current_intel_profile = "ultra7_arc770_npu"
            
            # Save configuration
            success = settings1.save_config()
            assert success is True
        
        # Load configuration in new instance
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings2 = ApplicationSettings(str(config_file))
            
            assert settings2.app_name == "Test Persistence"
            assert settings2.model.temperature == 0.8
            assert settings2.web.port == 9000
            assert settings2.current_intel_profile == "ultra7_arc770_npu"
    
    def test_hardware_detection_and_profile_selection_integration(self):
        """Test integration of hardware detection and profile selection."""
        with patch('config.settings.ApplicationSettings._detect_hardware') as mock_detect:
            # Simulate high-end hardware
            mock_detect.return_value = {
                "cpu": {"threads": 16},
                "arc_gpu": {"available": True, "memory": 16384},
                "npu": {"available": True}
            }
            
            with patch('config.settings.ApplicationSettings.apply_intel_profile') as mock_apply:
                settings = ApplicationSettings()
                
                # Should auto-detect and apply the best profile
                mock_apply.assert_called_once_with("ultra7_arc770_npu")
    
    @pytest.mark.slow
    def test_full_system_initialization_integration(self, temp_dir):
        """Test full system initialization with all components."""
        config_file = temp_dir / "full_system_test.json"
        
        # Set up environment
        import os
        with patch.dict(os.environ, {
            'MODEL_CACHE_DIR': str(temp_dir / 'models'),
            'OPENVINO_CACHE_DIR': str(temp_dir / 'cache'),
            'ENVIRONMENT': 'testing'
        }):
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                # Initialize complete system
                from config import initialize_settings, initialize_environment
                
                env_manager = initialize_environment()
                settings = initialize_settings(str(config_file))
                
                # Validate integration
                validation = env_manager.validate_environment()
                settings_issues = settings.validate_settings()
                
                # Should be functional even in testing environment
                assert isinstance(validation, dict)
                assert isinstance(settings_issues, list)
                
                # Test configuration export/import cycle
                config_dict = settings.to_dict()
                assert isinstance(config_dict, dict)
                assert "app_name" in config_dict
                
                env_exported = env_manager.export_environment_file(str(temp_dir / ".env.test"))
                assert env_exported is True
                
                env_loaded = env_manager.load_from_env_file(str(temp_dir / ".env.test"))
                assert env_loaded is True

@pytest.mark.intel
class TestIntelSpecificIntegration:
    """Test Intel hardware specific integration."""
    
    def test_intel_optimizations_application(self):
        """Test Intel optimization application."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        # Test different performance modes
        test_modes = ["max_performance", "balanced", "power_efficient"]
        
        for mode in test_modes:
            settings._apply_performance_mode(mode)
            
            # Verify optimizations are properly applied
            assert isinstance(settings.performance.enable_intel_optimizations, bool)
            assert isinstance(settings.performance.memory_pool_size_mb, int)
            assert settings.performance.memory_pool_size_mb > 0
    
    def test_intel_profile_recommendations(self):
        """Test Intel profile optimization recommendations."""
        manager = settings.intel_profile_manager if 'settings' in locals() else Mock()
        
        if hasattr(manager, 'optimize_for_profile'):
            for profile_name in ["ultra7_arc770_npu", "cpu_only"]:
                recommendations = manager.optimize_for_profile(profile_name)
                
                assert isinstance(recommendations, dict)
                assert "models" in recommendations
                assert "settings" in recommendations
                assert "warnings" in recommendations