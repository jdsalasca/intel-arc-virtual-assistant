"""
Intel AI Assistant System Benchmarks
Comprehensive benchmarks for measuring system performance across different Intel hardware profiles.
"""

import pytest
import time
import asyncio
import threading
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

from config import ApplicationSettings, IntelProfileManager

class TestSystemBenchmarks:
    """System-wide performance benchmarks."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Mock model manager for benchmarking."""
        mock_manager = Mock()
        mock_manager.load_model = Mock(return_value=True)
        mock_manager.generate_text = Mock(return_value="Benchmark response text")
        mock_manager.get_loaded_models = Mock(return_value=["qwen2.5-7b-int4"])
        return mock_manager
    
    @pytest.fixture
    def mock_conversation_manager(self):
        """Mock conversation manager for benchmarking."""
        mock_manager = Mock()
        mock_manager.create_conversation = Mock(return_value="conv-123")
        mock_manager.add_message = Mock(return_value=True)
        mock_manager.get_context = Mock(return_value="Previous conversation context")
        return mock_manager
    
    @pytest.mark.benchmark
    def test_configuration_system_benchmark(self, benchmark):
        """Benchmark complete configuration system initialization."""
        def init_config_system():
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                settings = ApplicationSettings()
                profile_manager = IntelProfileManager()
                
                # Apply optimal profile
                settings.apply_intel_profile("ultra7_arc770_npu")
                
                return settings, profile_manager
        
        result = benchmark(init_config_system)
        assert result[0] is not None
        assert result[1] is not None
    
    @pytest.mark.benchmark
    def test_intel_profile_optimization_benchmark(self, benchmark):
        """Benchmark Intel profile optimization recommendations."""
        manager = IntelProfileManager()
        
        def get_optimizations():
            recommendations = {}
            for profile_name in manager.list_profiles():
                recommendations[profile_name] = manager.optimize_for_profile(profile_name)
            return recommendations
        
        result = benchmark(get_optimizations)
        assert len(result) > 0
        assert all(isinstance(rec, dict) for rec in result.values())
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_conversation_processing_benchmark(self, benchmark, mock_model_manager, mock_conversation_manager):
        """Benchmark conversation processing pipeline."""
        def process_conversation():
            # Simulate conversation processing
            conv_id = mock_conversation_manager.create_conversation()
            
            # Add user message
            mock_conversation_manager.add_message(conv_id, "user", "Hello, how are you?")
            
            # Get context
            context = mock_conversation_manager.get_context(conv_id)
            
            # Generate response
            response = mock_model_manager.generate_text("Hello, how are you?", context=context)
            
            # Add assistant message
            mock_conversation_manager.add_message(conv_id, "assistant", response)
            
            return conv_id, response
        
        result = benchmark(process_conversation)
        assert result[0] is not None
        assert result[1] is not None

class TestHardwareProfileBenchmarks:
    """Benchmarks for different Intel hardware profiles."""
    
    @pytest.fixture(params=[
        "ultra7_arc770_npu",
        "ultra7_arc750_npu", 
        "i7_irisxe",
        "i5_uhd",
        "cpu_only"
    ])
    def intel_profile(self, request):
        """Parametrized Intel profiles for benchmarking."""
        return request.param
    
    @pytest.mark.benchmark
    @pytest.mark.intel
    def test_profile_model_config_benchmark(self, benchmark, intel_profile):
        """Benchmark model configuration for different Intel profiles."""
        manager = IntelProfileManager()
        
        def get_model_configs():
            configs = {}
            models = ["qwen2.5-7b-int4", "phi-3-mini-int4", "whisper-base", "speecht5-tts"]
            
            for model in models:
                configs[model] = manager.get_model_config(model, intel_profile)
            
            return configs
        
        result = benchmark(get_model_configs)
        assert len(result) > 0
        assert all(isinstance(config, dict) for config in result.values())
    
    @pytest.mark.benchmark
    @pytest.mark.intel
    def test_profile_performance_presets_benchmark(self, benchmark, intel_profile):
        """Benchmark performance presets for Intel profiles."""
        manager = IntelProfileManager()
        
        def get_performance_presets():
            presets = {}
            preset_names = ["max_performance", "balanced", "power_efficient"]
            
            for preset in preset_names:
                presets[preset] = manager.get_performance_preset(preset, intel_profile)
            
            return presets
        
        result = benchmark(get_performance_presets)
        assert isinstance(result, dict)

class TestConcurrencyBenchmarks:
    """Benchmarks for concurrent operations."""
    
    @pytest.mark.benchmark
    @pytest.mark.performance
    def test_concurrent_profile_access_benchmark(self, benchmark):
        """Benchmark concurrent profile access."""
        manager = IntelProfileManager()
        
        def concurrent_profile_access():
            results = []
            threads = []
            
            def worker():
                for _ in range(10):
                    profile = manager.get_profile("ultra7_arc770_npu")
                    details = manager.get_profile_details("ultra7_arc770_npu")
                    results.append((profile, details))
            
            # Create 5 concurrent workers
            for _ in range(5):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            return results
        
        result = benchmark(concurrent_profile_access)
        assert len(result) == 50  # 5 threads * 10 operations each
    
    @pytest.mark.benchmark
    @pytest.mark.performance
    def test_concurrent_configuration_benchmark(self, benchmark, temp_dir):
        """Benchmark concurrent configuration operations."""
        def concurrent_config_ops():
            results = []
            threads = []
            
            def config_worker(worker_id):
                config_file = temp_dir / f"bench_config_{worker_id}.json"
                
                with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                    settings = ApplicationSettings(str(config_file))
                
                for i in range(5):
                    settings.app_name = f"Benchmark Worker {worker_id} - {i}"
                    save_success = settings.save_config()
                    load_success = settings.load_config()
                    results.append((save_success, load_success))
            
            # Create 3 concurrent workers
            for i in range(3):
                thread = threading.Thread(target=config_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            return results
        
        result = benchmark(concurrent_config_ops)
        assert len(result) == 15  # 3 workers * 5 operations each
        assert all(save and load for save, load in result)

class TestMemoryBenchmarks:
    """Memory usage and efficiency benchmarks."""
    
    @pytest.mark.benchmark
    def test_memory_efficiency_benchmark(self, benchmark):
        """Benchmark memory efficiency of configuration system."""
        import psutil
        import gc
        
        def measure_memory_usage():
            gc.collect()
            initial_memory = psutil.Process().memory_info().rss
            
            # Create configuration objects
            configs = []
            for i in range(20):
                with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                    config = ApplicationSettings()
                    config.app_name = f"Memory Test {i}"
                configs.append(config)
            
            gc.collect()
            peak_memory = psutil.Process().memory_info().rss
            
            # Clean up
            del configs
            gc.collect()
            final_memory = psutil.Process().memory_info().rss
            
            return {
                "initial_mb": initial_memory / 1024 / 1024,
                "peak_mb": peak_memory / 1024 / 1024,
                "final_mb": final_memory / 1024 / 1024,
                "usage_mb": (peak_memory - initial_memory) / 1024 / 1024,
                "cleanup_mb": (peak_memory - final_memory) / 1024 / 1024
            }
        
        result = benchmark(measure_memory_usage)
        
        # Verify reasonable memory usage
        assert result["usage_mb"] < 50.0  # Less than 50MB for 20 configs
        assert result["cleanup_mb"] > result["usage_mb"] * 0.5  # At least 50% cleanup
    
    @pytest.mark.benchmark
    def test_profile_manager_memory_benchmark(self, benchmark):
        """Benchmark memory usage of Intel profile manager."""
        import psutil
        import gc
        
        def measure_profile_memory():
            gc.collect()
            initial_memory = psutil.Process().memory_info().rss
            
            # Create multiple profile managers
            managers = []
            for _ in range(10):
                manager = IntelProfileManager()
                
                # Perform operations to load all profiles
                for profile_name in manager.list_profiles():
                    manager.get_profile_details(profile_name)
                
                managers.append(manager)
            
            gc.collect()
            peak_memory = psutil.Process().memory_info().rss
            
            # Clean up
            del managers
            gc.collect()
            final_memory = psutil.Process().memory_info().rss
            
            return {
                "initial_mb": initial_memory / 1024 / 1024,
                "peak_mb": peak_memory / 1024 / 1024,
                "final_mb": final_memory / 1024 / 1024,
                "usage_mb": (peak_memory - initial_memory) / 1024 / 1024
            }
        
        result = benchmark(measure_profile_memory)
        
        # Verify reasonable memory usage
        assert result["usage_mb"] < 30.0  # Less than 30MB for 10 managers

class TestScalabilityBenchmarks:
    """Scalability benchmarks for large configurations."""
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_large_configuration_benchmark(self, benchmark, temp_dir):
        """Benchmark performance with large configuration files."""
        def large_config_ops():
            config_file = temp_dir / "large_benchmark.json"
            
            # Create large configuration data
            import json
            large_config = {
                "app_name": "Large Configuration Benchmark",
                "large_array": [f"item_{i}" for i in range(10000)],
                "large_dict": {f"key_{i}": f"value_{i}" * 100 for i in range(1000)},
                "nested_config": {
                    "level1": {
                        "level2": {
                            "level3": {
                                f"deep_key_{i}": f"deep_value_{i}"
                                for i in range(500)
                            }
                        }
                    }
                }
            }
            
            # Save large config
            with open(config_file, 'w') as f:
                json.dump(large_config, f)
            
            # Benchmark loading and operations
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                settings = ApplicationSettings(str(config_file))
                load_success = settings.load_config()
                
                # Perform operations
                settings.app_name = "Modified Large Config"
                save_success = settings.save_config()
                
                return load_success, save_success
        
        result = benchmark(large_config_ops)
        assert result[0] is True
        assert result[1] is True
    
    @pytest.mark.benchmark
    def test_many_profiles_benchmark(self, benchmark):
        """Benchmark performance with many custom profiles."""
        def many_profiles_ops():
            manager = IntelProfileManager()
            
            # Add many custom profiles
            import json
            for i in range(100):
                profile_data = {
                    "name": f"Benchmark Profile {i}",
                    "description": f"Generated profile for benchmark {i}",
                    "processor_type": "core_i7",
                    "gpu_type": "none",
                    "npu_type": "none",
                    "custom_data": {f"param_{j}": f"value_{j}" for j in range(50)}
                }
                profile_json = json.dumps(profile_data)
                manager.import_profile(profile_json, f"benchmark_{i}")
            
            # Test operations with many profiles
            all_profiles = manager.list_profiles()
            
            # Get details for a subset
            details = []
            for profile_name in all_profiles[:20]:  # First 20 profiles
                detail = manager.get_profile_details(profile_name)
                if detail:
                    details.append(detail)
            
            return len(all_profiles), len(details)
        
        result = benchmark(many_profiles_ops)
        assert result[0] >= 100  # At least 100 profiles
        assert result[1] > 0     # Got some details

class TestRealtimeBenchmarks:
    """Real-time performance benchmarks."""
    
    @pytest.mark.benchmark
    def test_configuration_lookup_latency(self, benchmark):
        """Benchmark configuration lookup latency."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        def single_config_lookup():
            # Simulate rapid configuration lookups
            return (
                settings.get_setting("model", "temperature"),
                settings.get_setting("voice", "tts_enabled"),
                settings.get_setting("web", "port"),
                settings.get_setting("performance", "enable_intel_optimizations")
            )
        
        result = benchmark(single_config_lookup)
        assert len(result) == 4
        assert all(val is not None for val in result)
    
    @pytest.mark.benchmark
    def test_profile_switch_latency(self, benchmark):
        """Benchmark Intel profile switching latency."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        def profile_switch():
            # Simulate switching between profiles
            profiles = ["ultra7_arc770_npu", "cpu_only", "i7_irisxe"]
            results = []
            
            for profile in profiles:
                success = settings.apply_intel_profile(profile)
                current = settings.current_intel_profile
                results.append((success, current))
            
            return results
        
        result = benchmark(profile_switch)
        assert len(result) == 3
        assert all(success for success, _ in result)
    
    @pytest.mark.benchmark
    def test_rapid_validation_benchmark(self, benchmark):
        """Benchmark rapid configuration validation."""
        with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
            settings = ApplicationSettings()
        
        def rapid_validation():
            # Perform rapid validations
            validations = []
            for i in range(10):
                # Modify settings slightly
                settings.model.temperature = 0.1 + (i * 0.1)
                settings.web.port = 8000 + i
                
                # Validate
                issues = settings.validate_settings()
                validations.append(len(issues))
            
            return validations
        
        result = benchmark(rapid_validation)
        assert len(result) == 10
        assert all(isinstance(count, int) for count in result)

@pytest.mark.gpu
class TestGPUOptimizedBenchmarks:
    """Benchmarks for GPU-optimized configurations."""
    
    @pytest.mark.benchmark
    @pytest.mark.intel
    def test_gpu_profile_optimization_benchmark(self, benchmark):
        """Benchmark GPU profile optimization."""
        manager = IntelProfileManager()
        
        def gpu_optimization():
            gpu_profiles = ["ultra7_arc770_npu", "ultra7_arc750_npu", "i7_irisxe"]
            optimizations = {}
            
            for profile in gpu_profiles:
                recommendations = manager.optimize_for_profile(profile)
                
                # Extract GPU-specific optimizations
                gpu_settings = {}
                if "settings" in recommendations:
                    for key, value in recommendations["settings"].items():
                        if "gpu" in key.lower() or "performance" in key.lower():
                            gpu_settings[key] = value
                
                optimizations[profile] = gpu_settings
            
            return optimizations
        
        result = benchmark(gpu_optimization)
        assert len(result) == 3
        assert all(isinstance(opts, dict) for opts in result.values())

@pytest.mark.npu
class TestNPUOptimizedBenchmarks:
    """Benchmarks for NPU-optimized configurations."""
    
    @pytest.mark.benchmark
    @pytest.mark.intel
    def test_npu_profile_optimization_benchmark(self, benchmark):
        """Benchmark NPU profile optimization."""
        manager = IntelProfileManager()
        
        def npu_optimization():
            npu_profiles = ["ultra7_arc770_npu", "ultra7_arc750_npu"]
            optimizations = {}
            
            for profile in npu_profiles:
                recommendations = manager.optimize_for_profile(profile)
                
                # Extract NPU-specific configurations
                npu_models = {}
                if "models" in recommendations:
                    models = recommendations["models"]
                    if "tts" in models:
                        npu_models["tts"] = models["tts"]
                    if "stt" in models:
                        npu_models["stt"] = models["stt"]
                
                optimizations[profile] = npu_models
            
            return optimizations
        
        result = benchmark(npu_optimization)
        assert len(result) == 2
        assert all(isinstance(opts, dict) for opts in result.values())