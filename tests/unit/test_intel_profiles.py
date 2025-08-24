"""
Unit Tests for Intel Profiles Configuration
Tests the Intel hardware profile management system.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from config.intel_profiles import (
    IntelProfileManager,
    IntelHardwareProfile,
    IntelProcessorType,
    IntelGPUType,
    IntelNPUType,
    HardwareCapabilities
)

class TestHardwareCapabilities:
    """Test HardwareCapabilities dataclass."""
    
    def test_default_initialization(self):
        """Test default initialization of HardwareCapabilities."""
        caps = HardwareCapabilities()
        
        assert caps.available is False
        assert caps.memory_mb == 0
        assert caps.compute_units == 0
        assert caps.max_performance == "medium"
        assert caps.power_efficiency == "medium"
        assert caps.supported_precisions == ["FP32", "FP16"]
    
    def test_custom_initialization(self):
        """Test custom initialization with parameters."""
        caps = HardwareCapabilities(
            available=True,
            memory_mb=8192,
            compute_units=512,
            max_performance="ultra",
            power_efficiency="high",
            supported_precisions=["FP32", "FP16", "INT8", "INT4"]
        )
        
        assert caps.available is True
        assert caps.memory_mb == 8192
        assert caps.compute_units == 512
        assert caps.max_performance == "ultra"
        assert caps.power_efficiency == "high"
        assert caps.supported_precisions == ["FP32", "FP16", "INT8", "INT4"]

class TestIntelHardwareProfile:
    """Test IntelHardwareProfile dataclass."""
    
    def test_profile_creation(self):
        """Test creating a hardware profile."""
        profile = IntelHardwareProfile(
            name="Test Profile",
            description="Test description",
            processor_type=IntelProcessorType.CORE_ULTRA_7,
            gpu_type=IntelGPUType.ARC_A770,
            npu_type=IntelNPUType.AI_BOOST_NPU,
            cpu_capabilities=HardwareCapabilities(available=True, compute_units=16),
            gpu_capabilities=HardwareCapabilities(available=True, memory_mb=16384),
            npu_capabilities=HardwareCapabilities(available=True, compute_units=8)
        )
        
        assert profile.name == "Test Profile"
        assert profile.description == "Test description"
        assert profile.processor_type == IntelProcessorType.CORE_ULTRA_7
        assert profile.gpu_type == IntelGPUType.ARC_A770
        assert profile.npu_type == IntelNPUType.AI_BOOST_NPU
        assert profile.cpu_capabilities.available is True
        assert profile.gpu_capabilities.memory_mb == 16384
        assert profile.npu_capabilities.compute_units == 8

class TestIntelProfileManager:
    """Test IntelProfileManager functionality."""
    
    def test_initialization(self):
        """Test profile manager initialization."""
        manager = IntelProfileManager()
        
        assert manager.profiles is not None
        assert len(manager.profiles) > 0
        assert manager.current_profile is None
        assert manager.detected_profile is None
    
    def test_predefined_profiles_exist(self):
        """Test that predefined profiles are available."""
        manager = IntelProfileManager()
        
        expected_profiles = [
            "ultra7_arc770_npu",
            "ultra7_arc750_npu", 
            "i7_irisxe",
            "i5_uhd",
            "cpu_only"
        ]
        
        for profile_name in expected_profiles:
            assert profile_name in manager.profiles
            profile = manager.get_profile(profile_name)
            assert profile is not None
            assert isinstance(profile, IntelHardwareProfile)
    
    def test_get_profile(self):
        """Test getting a profile by name."""
        manager = IntelProfileManager()
        
        # Test valid profile
        profile = manager.get_profile("ultra7_arc770_npu")
        assert profile is not None
        assert profile.name == "Intel Core Ultra 7 + Arc A770 + NPU"
        assert profile.gpu_type == IntelGPUType.ARC_A770
        assert profile.npu_type == IntelNPUType.AI_BOOST_NPU
        
        # Test invalid profile
        invalid_profile = manager.get_profile("nonexistent_profile")
        assert invalid_profile is None
    
    def test_list_profiles(self):
        """Test listing available profiles."""
        manager = IntelProfileManager()
        profiles = manager.list_profiles()
        
        assert isinstance(profiles, list)
        assert len(profiles) > 0
        assert "ultra7_arc770_npu" in profiles
        assert "cpu_only" in profiles
    
    def test_get_profile_details(self):
        """Test getting detailed profile information."""
        manager = IntelProfileManager()
        
        details = manager.get_profile_details("ultra7_arc770_npu")
        assert details is not None
        assert "name" in details
        assert "description" in details
        assert "capabilities" in details
        assert "cpu" in details["capabilities"]
        assert "gpu" in details["capabilities"]
        assert "npu" in details["capabilities"]
        assert "system" in details
        assert "supported_models" in details
        
        # Test invalid profile
        invalid_details = manager.get_profile_details("nonexistent")
        assert invalid_details is None
    
    def test_auto_detect_profile_cpu_only(self):
        """Test auto-detection with CPU-only hardware."""
        manager = IntelProfileManager()
        
        hardware_info = {
            "cpu": {"threads": 8},
            "arc_gpu": {"available": False},
            "npu": {"available": False}
        }
        
        profile_name = manager.auto_detect_profile(hardware_info)
        assert profile_name == "cpu_only"
    
    def test_auto_detect_profile_with_gpu(self):
        """Test auto-detection with Arc GPU."""
        manager = IntelProfileManager()
        
        hardware_info = {
            "cpu": {"threads": 16},
            "arc_gpu": {"available": True, "memory": 8192},
            "npu": {"available": False}
        }
        
        profile_name = manager.auto_detect_profile(hardware_info)
        assert profile_name == "ultra7_arc750_npu"
    
    def test_auto_detect_profile_with_gpu_and_npu(self):
        """Test auto-detection with Arc GPU and NPU."""
        manager = IntelProfileManager()
        
        hardware_info = {
            "cpu": {"threads": 16},
            "arc_gpu": {"available": True, "memory": 16384},
            "npu": {"available": True}
        }
        
        profile_name = manager.auto_detect_profile(hardware_info)
        assert profile_name == "ultra7_arc770_npu"
    
    def test_auto_detect_profile_error_handling(self):
        """Test auto-detection error handling."""
        manager = IntelProfileManager()
        
        # Test with invalid hardware info
        invalid_hardware = {"invalid": "data"}
        profile_name = manager.auto_detect_profile(invalid_hardware)
        assert profile_name == "cpu_only"  # Should fallback
    
    def test_set_current_profile(self):
        """Test setting current profile."""
        manager = IntelProfileManager()
        
        # Test valid profile
        success = manager.set_current_profile("ultra7_arc770_npu")
        assert success is True
        assert manager.current_profile is not None
        assert manager.current_profile.name == "Intel Core Ultra 7 + Arc A770 + NPU"
        
        # Test invalid profile
        failure = manager.set_current_profile("nonexistent")
        assert failure is False
    
    def test_get_model_config_with_profile(self):
        """Test getting model configuration for a profile."""
        manager = IntelProfileManager()
        
        config = manager.get_model_config("qwen2.5-7b-int4", "ultra7_arc770_npu")
        assert config is not None
        assert "preferred_device" in config
        assert "batch_size" in config
        assert "max_tokens" in config
        assert "temperature" in config
        assert "precision" in config
        
        assert config["preferred_device"] == "GPU"
        assert config["precision"] == "INT4"
    
    def test_get_model_config_without_profile(self):
        """Test getting model configuration without profile."""
        manager = IntelProfileManager()
        
        # Should return default config
        config = manager.get_model_config("unknown_model")
        assert config is not None
        assert config["preferred_device"] == "CPU"
        assert config["precision"] == "FP16"
    
    def test_get_model_config_with_current_profile(self):
        """Test getting model config using current profile."""
        manager = IntelProfileManager()
        manager.set_current_profile("ultra7_arc770_npu")
        
        config = manager.get_model_config("qwen2.5-7b-int4")
        assert config["preferred_device"] == "GPU"
    
    def test_get_performance_preset(self):
        """Test getting performance presets."""
        manager = IntelProfileManager()
        
        preset = manager.get_performance_preset("max_performance", "ultra7_arc770_npu")
        assert preset is not None
        assert "gpu_memory_fraction" in preset
        assert "enable_mixed_precision" in preset
        assert preset["gpu_memory_fraction"] == 0.9
        assert preset["enable_mixed_precision"] is True
    
    def test_optimize_for_profile(self):
        """Test optimization recommendations."""
        manager = IntelProfileManager()
        
        recommendations = manager.optimize_for_profile("ultra7_arc770_npu")
        assert recommendations is not None
        assert "models" in recommendations
        assert "settings" in recommendations
        assert "warnings" in recommendations
        
        # Check model recommendations
        models = recommendations["models"]
        assert "primary" in models
        assert "fallback" in models
        assert models["primary"] == "qwen2.5-7b-int4"
        
        # Check settings recommendations
        settings = recommendations["settings"]
        assert "performance_mode" in settings
        assert settings["performance_mode"] == "max_performance"
    
    def test_optimize_for_cpu_only_profile(self):
        """Test optimization for CPU-only profile."""
        manager = IntelProfileManager()
        
        recommendations = manager.optimize_for_profile("cpu_only")
        warnings = recommendations["warnings"]
        
        assert any("No GPU detected" in warning for warning in warnings)
        assert any("No NPU detected" in warning for warning in warnings)
    
    def test_export_profile(self):
        """Test exporting profile to JSON."""
        manager = IntelProfileManager()
        
        json_str = manager.export_profile("ultra7_arc770_npu")
        assert json_str is not None
        
        import json
        profile_dict = json.loads(json_str)
        assert "name" in profile_dict
        assert "description" in profile_dict
        assert "processor_type" in profile_dict
        assert "model_configurations" in profile_dict
        
        # Test invalid profile
        invalid_export = manager.export_profile("nonexistent")
        assert invalid_export is None
    
    @patch('config.intel_profiles.logger')
    def test_import_profile(self, mock_logger):
        """Test importing profile from JSON."""
        manager = IntelProfileManager()
        
        # Create test profile data
        test_profile = {
            "name": "Test Imported Profile",
            "description": "Test description",
            "processor_type": "core_i7",
            "gpu_type": "none",
            "npu_type": "none"
        }
        
        import json
        profile_json = json.dumps(test_profile)
        
        success = manager.import_profile(profile_json, "test_imported")
        assert success is True
        assert "test_imported" in manager.profiles
        
        # Test invalid JSON
        invalid_success = manager.import_profile("invalid json", "test_invalid")
        assert invalid_success is False

@pytest.mark.parametrize("profile_name,expected_gpu,expected_npu", [
    ("ultra7_arc770_npu", True, True),
    ("ultra7_arc750_npu", True, True),
    ("i7_irisxe", True, False),
    ("i5_uhd", True, False),
    ("cpu_only", False, False)
])
def test_profile_capabilities(profile_name: str, expected_gpu: bool, expected_npu: bool):
    """Test profile capabilities match expectations."""
    manager = IntelProfileManager()
    profile = manager.get_profile(profile_name)
    
    assert profile is not None
    assert profile.gpu_capabilities.available == expected_gpu
    assert profile.npu_capabilities.available == expected_npu

@pytest.mark.intel
def test_intel_profile_model_configurations():
    """Test that Intel profiles have proper model configurations."""
    manager = IntelProfileManager()
    
    for profile_name in manager.list_profiles():
        profile = manager.get_profile(profile_name)
        assert profile is not None
        
        # All profiles should have some model configuration
        assert isinstance(profile.model_configurations, dict)
        
        # Check that configurations have required fields
        for model_name, config in profile.model_configurations.items():
            assert "preferred_device" in config
            assert "precision" in config
            assert config["preferred_device"] in ["CPU", "GPU", "NPU"]
            assert config["precision"] in ["FP32", "FP16", "INT8", "INT4"]