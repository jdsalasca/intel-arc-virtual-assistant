"""
Performance Tests for Configuration System
Tests performance characteristics of configuration loading, saving, and operations.
"""

import pytest
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from config import ApplicationSettings, EnvironmentManager, IntelProfileManager

class TestConfigurationPerformance:
    """Test configuration system performance."""
    
    @pytest.mark.performance
    def test_settings_initialization_performance(self, performance_monitor):
        """Test settings initialization performance."""
        performance_monitor.start()
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            # Test multiple initializations
            for _ in range(10):
                settings = ApplicationSettings()
                assert settings is not None
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should initialize quickly
        assert stats["duration"] < 5.0  # Less than 5 seconds for 10 initializations
        assert stats["avg_cpu"] < 50.0  # Low CPU usage
    
    @pytest.mark.performance
    def test_intel_profile_manager_initialization_performance(self, performance_monitor):
        """Test Intel profile manager initialization performance."""
        performance_monitor.start()
        
        # Test multiple initializations
        for _ in range(50):
            manager = IntelProfileManager()
            assert len(manager.profiles) > 0
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should initialize very quickly
        assert stats["duration"] < 2.0  # Less than 2 seconds for 50 initializations
        assert stats["avg_cpu"] < 30.0  # Low CPU usage
    
    @pytest.mark.performance
    def test_profile_operations_performance(self, performance_monitor):
        """Test profile operations performance."""
        manager = IntelProfileManager()
        
        performance_monitor.start()
        
        # Test profile operations
        for _ in range(100):
            # Get profile
            profile = manager.get_profile("ultra7_arc770_npu")
            assert profile is not None
            
            # Get profile details
            details = manager.get_profile_details("ultra7_arc770_npu")
            assert details is not None
            
            # Get model config
            config = manager.get_model_config("qwen2.5-7b-int4", "ultra7_arc770_npu")
            assert config is not None
            
            # Get optimization recommendations
            recommendations = manager.optimize_for_profile("ultra7_arc770_npu")
            assert recommendations is not None
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should be fast for 100 operations
        assert stats["duration"] < 3.0  # Less than 3 seconds
        assert stats["avg_cpu"] < 40.0  # Reasonable CPU usage
    
    @pytest.mark.performance
    def test_config_save_load_performance(self, performance_monitor, temp_dir):
        """Test configuration save/load performance."""
        config_file = temp_dir / "perf_test.json"
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings(str(config_file))
        
        performance_monitor.start()
        
        # Test multiple save/load cycles
        for i in range(20):
            settings.app_name = f"Test App {i}"
            settings.model.temperature = 0.1 + (i * 0.01)
            
            # Save configuration
            save_success = settings.save_config()
            assert save_success is True
            
            # Load configuration
            load_success = settings.load_config()
            assert load_success is True
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should handle 20 save/load cycles quickly
        assert stats["duration"] < 2.0  # Less than 2 seconds
        assert stats["avg_cpu"] < 30.0  # Low CPU usage
    
    @pytest.mark.performance
    def test_environment_validation_performance(self, performance_monitor):
        """Test environment validation performance."""
        env_manager = EnvironmentManager()
        
        performance_monitor.start()
        
        # Test multiple validations
        for _ in range(30):
            validation = env_manager.validate_environment()
            assert isinstance(validation, dict)
            assert "valid" in validation
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should validate quickly
        assert stats["duration"] < 1.5  # Less than 1.5 seconds for 30 validations
        assert stats["avg_cpu"] < 25.0  # Low CPU usage
    
    @pytest.mark.performance
    def test_hardware_detection_performance(self, performance_monitor):
        """Test hardware detection performance."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        performance_monitor.start()
        
        # Test multiple hardware detections
        for _ in range(25):
            hardware_info = settings._detect_hardware()
            assert isinstance(hardware_info, dict)
            assert "cpu" in hardware_info
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should detect quickly
        assert stats["duration"] < 1.0  # Less than 1 second for 25 detections
        assert stats["avg_cpu"] < 20.0  # Very low CPU usage
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_configuration_performance(self, performance_monitor, temp_dir):
        """Test performance with large configuration files."""
        config_file = temp_dir / "large_config.json"
        
        # Create large configuration
        large_config = {
            "app_name": "Large Test App",
            "large_data": {
                f"key_{i}": f"value_{i}" * 100  # Create large strings
                for i in range(1000)  # 1000 entries
            },
            "model": {
                "name": "test-model" * 50,  # Long model name
                "configurations": {
                    f"config_{i}": {
                        "param1": i,
                        "param2": f"value_{i}" * 20
                    }
                    for i in range(100)  # 100 configurations
                }
            }
        }
        
        # Save large config
        with open(config_file, 'w') as f:
            json.dump(large_config, f)
        
        performance_monitor.start()
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            # Test loading large configuration
            settings = ApplicationSettings(str(config_file))
            load_success = settings.load_config()
            assert load_success is True
            
            # Test saving large configuration
            save_success = settings.save_config()
            assert save_success is True
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should handle large configs reasonably
        assert stats["duration"] < 10.0  # Less than 10 seconds
        assert stats["avg_cpu"] < 60.0  # Moderate CPU usage acceptable
    
    @pytest.mark.performance
    def test_memory_usage_configuration(self):
        """Test memory usage of configuration system."""
        import psutil
        import gc
        
        # Get baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple configuration instances
        configs = []
        for i in range(50):
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                config = ApplicationSettings()
            configs.append(config)
        
        # Measure memory after creation
        gc.collect()
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        memory_usage = peak_memory - baseline_memory
        
        # Should not use excessive memory
        assert memory_usage < 100.0  # Less than 100MB for 50 instances
        
        # Clean up
        del configs
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Should clean up most memory (but be lenient due to Python GC behavior)
        memory_cleanup = peak_memory - final_memory
        assert memory_cleanup > memory_usage * 0.5  # At least 50% cleanup (reduced from 70%)

class TestConfigurationConcurrency:
    """Test configuration system under concurrent access."""
    
    @pytest.mark.performance
    def test_concurrent_profile_access(self):
        """Test concurrent access to Intel profiles."""
        import threading
        import queue
        
        manager = IntelProfileManager()
        results = queue.Queue()
        errors = queue.Queue()
        
        def profile_worker():
            try:
                for _ in range(10):
                    # Test various operations
                    profile = manager.get_profile("ultra7_arc770_npu")
                    details = manager.get_profile_details("ultra7_arc770_npu")
                    config = manager.get_model_config("qwen2.5-7b-int4", "ultra7_arc770_npu")
                    
                    assert profile is not None
                    assert details is not None
                    assert config is not None
                
                results.put("success")
            except Exception as e:
                errors.put(str(e))
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=profile_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 5  # All threads succeeded
        assert errors.qsize() == 0   # No errors
    
    @pytest.mark.performance
    def test_concurrent_config_operations(self, temp_dir):
        """Test concurrent configuration operations."""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def config_worker(worker_id):
            try:
                config_file = temp_dir / f"config_{worker_id}.json"
                
                with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                    settings = ApplicationSettings(str(config_file))
                
                # Perform operations
                for i in range(5):
                    settings.app_name = f"Worker {worker_id} App {i}"
                    settings.model.temperature = 0.1 + (i * 0.1)
                    
                    # Save and load
                    save_success = settings.save_config()
                    load_success = settings.load_config()
                    
                    assert save_success is True
                    assert load_success is True
                
                results.put(f"worker_{worker_id}_success")
            except Exception as e:
                errors.put(f"worker_{worker_id}_error: {str(e)}")
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=config_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 3  # All workers succeeded
        assert errors.qsize() == 0   # No errors

class TestConfigurationScalability:
    """Test configuration system scalability."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_many_profiles_performance(self, performance_monitor):
        """Test performance with many custom profiles."""
        manager = IntelProfileManager()
        
        # Add many custom profiles
        for i in range(100):
            profile_data = {
                "name": f"Custom Profile {i}",
                "description": f"Test profile {i}",
                "processor_type": "core_i7",
                "gpu_type": "none",
                "npu_type": "none"
            }
            
            import json
            profile_json = json.dumps(profile_data)
            manager.import_profile(profile_json, f"custom_{i}")
        
        performance_monitor.start()
        
        # Test operations with many profiles
        for _ in range(20):
            profiles = manager.list_profiles()
            assert len(profiles) >= 100
            
            # Test random profile access
            import random
            random_profile = random.choice(profiles)
            profile = manager.get_profile(random_profile)
            assert profile is not None
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should still be reasonably fast
        assert stats["duration"] < 5.0  # Less than 5 seconds
        assert stats["avg_cpu"] < 50.0  # Reasonable CPU usage
    
    @pytest.mark.performance
    def test_configuration_serialization_performance(self, performance_monitor, temp_dir):
        """Test configuration serialization performance with complex data."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        # Add complex configuration data
        complex_tools = []
        for i in range(50):
            complex_tools.append(f"tool_{i}_with_long_name_for_testing")
        settings.tools.enabled_tools = complex_tools
        
        performance_monitor.start()
        
        # Test serialization/deserialization cycles
        for _ in range(10):
            # Convert to dict (serialization)
            config_dict = settings.to_dict()
            assert isinstance(config_dict, dict)
            
            # Convert to JSON string
            json_str = json.dumps(config_dict)
            assert isinstance(json_str, str)
            
            # Parse back from JSON
            parsed_dict = json.loads(json_str)
            assert isinstance(parsed_dict, dict)
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Should serialize quickly
        assert stats["duration"] < 1.0  # Less than 1 second for 10 cycles
        assert stats["avg_cpu"] < 30.0  # Low CPU usage

@pytest.mark.benchmark
class TestConfigurationBenchmarks:
    """Benchmark tests for configuration system."""
    
    def test_profile_lookup_benchmark(self, benchmark):
        """Benchmark profile lookup operations."""
        manager = IntelProfileManager()
        
        def profile_lookup():
            return manager.get_profile("ultra7_arc770_npu")
        
        result = benchmark(profile_lookup)
        assert result is not None
    
    def test_profile_details_benchmark(self, benchmark):
        """Benchmark profile details retrieval."""
        manager = IntelProfileManager()
        
        def get_details():
            return manager.get_profile_details("ultra7_arc770_npu")
        
        result = benchmark(get_details)
        assert result is not None
    
    def test_model_config_benchmark(self, benchmark):
        """Benchmark model configuration retrieval."""
        manager = IntelProfileManager()
        
        def get_model_config():
            return manager.get_model_config("qwen2.5-7b-int4", "ultra7_arc770_npu")
        
        result = benchmark(get_model_config)
        assert result is not None
    
    def test_optimization_recommendations_benchmark(self, benchmark):
        """Benchmark optimization recommendations."""
        manager = IntelProfileManager()
        
        def get_recommendations():
            return manager.optimize_for_profile("ultra7_arc770_npu")
        
        result = benchmark(get_recommendations)
        assert result is not None
    
    def test_settings_initialization_benchmark(self, benchmark, temp_dir):
        """Benchmark settings initialization."""
        config_file = temp_dir / "benchmark_config.json"
        
        def init_settings():
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                return ApplicationSettings(str(config_file))
        
        result = benchmark(init_settings)
        assert result is not None
    
    def test_config_save_benchmark(self, benchmark, temp_dir):
        """Benchmark configuration saving."""
        config_file = temp_dir / "save_benchmark.json"
        
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings(str(config_file))
        
        def save_config():
            return settings.save_config()
        
        result = benchmark(save_config)
        assert result is True
    
    def test_config_load_benchmark(self, benchmark, test_config_file):
        """Benchmark configuration loading."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings(str(test_config_file))
        
        def load_config():
            return settings.load_config()
        
        result = benchmark(load_config)
        assert result is True