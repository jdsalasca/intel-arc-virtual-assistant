"""
Hardware Service Implementation
Business logic for Intel hardware optimization and device management.
"""

import asyncio
import psutil
from typing import Dict, Any
from ..interfaces.services import IHardwareService
from ..interfaces.providers import IHardwareProvider
from ..models.domain import HardwareInfo, HardwareType, ModelType


class HardwareService(IHardwareService):
    """Implementation of hardware optimization service."""

    def __init__(self, hardware_provider: IHardwareProvider):
        self.hardware_provider = hardware_provider
        self._cached_hardware_info: Optional[HardwareInfo] = None
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes

    async def get_hardware_info(self) -> HardwareInfo:
        """Get current hardware information with caching."""
        import time
        current_time = time.time()
        
        # Return cached info if still valid
        if (self._cached_hardware_info and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._cached_hardware_info
        
        # Detect hardware
        hardware_data = self.hardware_provider.detect_hardware()
        
        # Get system memory
        memory = psutil.virtual_memory()
        
        # Create hardware info object
        hardware_info = HardwareInfo(
            cpu_available=hardware_data.get("cpu_available", True),
            gpu_available=hardware_data.get("gpu_available", False),
            npu_available=hardware_data.get("npu_available", False),
            cpu_cores=psutil.cpu_count(logical=False),
            total_memory=memory.total,
            gpu_memory=hardware_data.get("gpu_memory"),
            npu_tops=hardware_data.get("npu_tops"),
            metadata={
                "cpu_model": hardware_data.get("cpu_model"),
                "gpu_model": hardware_data.get("gpu_model"),
                "npu_model": hardware_data.get("npu_model"),
                "memory_usage": memory.percent,
                "cpu_usage": psutil.cpu_percent()
            }
        )
        
        # Cache the result
        self._cached_hardware_info = hardware_info
        self._cache_timestamp = current_time
        
        return hardware_info

    async def optimize_for_device(
        self, device_type: str, model_id: str
    ) -> Dict[str, Any]:
        """Get optimization parameters for a device."""
        try:
            device = HardwareType(device_type)
        except ValueError:
            raise ValueError(f"Invalid device type: {device_type}")
        
        # Get model type (simplified - in reality, you'd look this up)
        model_type = ModelType.LLM  # Default assumption
        
        return self.hardware_provider.get_optimization_config(device, model_type)

    async def get_optimal_device(self, task_type: str) -> str:
        """Get the optimal device for a task type."""
        # Map task types to model types
        task_to_model_type = {
            "text_generation": ModelType.LLM,
            "speech_synthesis": ModelType.TTS,
            "speech_recognition": ModelType.STT,
            "embedding": ModelType.EMBEDDING
        }
        
        model_type = task_to_model_type.get(task_type, ModelType.LLM)
        
        # Get hardware info to determine model size (simplified)
        hardware_info = await self.get_hardware_info()
        estimated_model_size = self._estimate_model_size(model_type)
        
        optimal_device = self.hardware_provider.get_optimal_device(
            model_type, estimated_model_size
        )
        
        return optimal_device.value

    async def benchmark_device(self, device_type: str) -> Dict[str, Any]:
        """Run benchmark on a device."""
        try:
            device = HardwareType(device_type)
        except ValueError:
            raise ValueError(f"Invalid device type: {device_type}")
        
        # Run benchmark asynchronously to avoid blocking
        loop = asyncio.get_event_loop()
        benchmark_result = await loop.run_in_executor(
            None, self.hardware_provider.benchmark_device, device
        )
        
        return benchmark_result

    def _estimate_model_size(self, model_type: ModelType) -> int:
        """Estimate model size based on type (simplified)."""
        # These are rough estimates - in reality, you'd have a model registry
        size_estimates = {
            ModelType.LLM: 7_000_000_000,  # 7B parameters
            ModelType.TTS: 300_000_000,    # 300M parameters
            ModelType.STT: 244_000_000,    # 244M parameters (Whisper base)
            ModelType.EMBEDDING: 100_000_000  # 100M parameters
        }
        
        return size_estimates.get(model_type, 1_000_000_000)


class IntelHardwareProvider(IHardwareProvider):
    """Intel-specific hardware detection and optimization provider."""

    def __init__(self):
        self._device_info_cache = {}

    def detect_hardware(self) -> Dict[str, Any]:
        """Detect available Intel hardware components."""
        hardware_info = {
            "cpu_available": True,  # Always available
            "gpu_available": False,
            "npu_available": False,
            "cpu_model": None,
            "gpu_model": None,
            "npu_model": None,
            "gpu_memory": None,
            "npu_tops": None
        }

        # Detect CPU
        try:
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            hardware_info["cpu_model"] = cpu_info.get("brand_raw", "Unknown CPU")
        except ImportError:
            # Fallback to system detection
            hardware_info["cpu_model"] = "Intel CPU"

        # Detect Intel Arc GPU
        try:
            # This would use Intel GPU detection libraries
            # For now, we'll use a simplified approach
            import subprocess
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True, text=True, timeout=5
            )
            if "Intel" in result.stdout and ("Arc" in result.stdout or "Xe" in result.stdout):
                hardware_info["gpu_available"] = True
                hardware_info["gpu_model"] = "Intel Arc GPU"
                hardware_info["gpu_memory"] = 2 * 1024 * 1024 * 1024  # Estimate 2GB
        except Exception:
            pass  # GPU detection failed

        # Detect Intel NPU (AI Boost)
        try:
            # Check for Intel AI Boost NPU in device manager
            import subprocess
            result = subprocess.run(
                ["wmic", "path", "win32_PnPEntity", "where", "name like '%Intel%AI%'", "get", "name"],
                capture_output=True, text=True, timeout=5
            )
            if "Intel" in result.stdout and "AI" in result.stdout:
                hardware_info["npu_available"] = True
                hardware_info["npu_model"] = "Intel AI Boost NPU"
                hardware_info["npu_tops"] = 10.0  # Approximate TOPS for Core Ultra
        except Exception:
            pass  # NPU detection failed

        return hardware_info

    def get_optimal_device(
        self, model_type: ModelType, model_size: int
    ) -> HardwareType:
        """Get optimal device for a model based on Intel hardware."""
        hardware_info = self.detect_hardware()
        
        # For large LLMs, prefer GPU if available, otherwise CPU
        if model_type == ModelType.LLM:
            if model_size > 3_000_000_000:  # > 3B parameters
                if hardware_info["gpu_available"]:
                    return HardwareType.GPU
                else:
                    return HardwareType.CPU
            else:
                # Smaller models can use NPU if available
                if hardware_info["npu_available"]:
                    return HardwareType.NPU
                else:
                    return HardwareType.CPU
        
        # For TTS/STT, prefer NPU for efficiency
        elif model_type in [ModelType.TTS, ModelType.STT]:
            if hardware_info["npu_available"]:
                return HardwareType.NPU
            else:
                return HardwareType.CPU
        
        # Default to AUTO for mixed workloads
        return HardwareType.AUTO

    def get_optimization_config(
        self, device: HardwareType, model_type: ModelType
    ) -> Dict[str, Any]:
        """Get optimization configuration for Intel devices."""
        base_config = {
            "precision": "int8",
            "batch_size": 1,
            "num_threads": 1,
            "enable_turbo": True
        }

        if device == HardwareType.CPU:
            base_config.update({
                "num_threads": min(8, psutil.cpu_count()),
                "precision": "int8",
                "use_mkldnn": True
            })
        
        elif device == HardwareType.GPU:
            base_config.update({
                "precision": "fp16",
                "use_gpu_memory_fraction": 0.8,
                "enable_gpu_inference": True
            })
        
        elif device == HardwareType.NPU:
            base_config.update({
                "precision": "int8",
                "npu_tile_size": 1024,
                "enable_npu_turbo": True
            })
        
        elif device == HardwareType.AUTO:
            base_config.update({
                "auto_device_selection": True,
                "fallback_device": "CPU"
            })

        # Model-specific optimizations
        if model_type == ModelType.LLM:
            base_config.update({
                "kv_cache_precision": "int8",
                "attention_optimization": True
            })
        elif model_type == ModelType.TTS:
            base_config.update({
                "audio_sample_rate": 16000,
                "enable_audio_optimization": True
            })

        return base_config

    def benchmark_device(self, device: HardwareType) -> Dict[str, Any]:
        """Run benchmark on Intel device."""
        import time
        import numpy as np
        
        benchmark_results = {
            "device": device.value,
            "timestamp": time.time(),
            "tests": {}
        }

        try:
            # Simple matrix multiplication benchmark
            if device in [HardwareType.CPU, HardwareType.AUTO]:
                start_time = time.time()
                
                # CPU benchmark
                a = np.random.rand(1000, 1000).astype(np.float32)
                b = np.random.rand(1000, 1000).astype(np.float32)
                result = np.dot(a, b)
                
                cpu_time = time.time() - start_time
                benchmark_results["tests"]["matrix_mult_1000x1000"] = {
                    "time_seconds": cpu_time,
                    "gflops": (2 * 1000**3) / (cpu_time * 1e9)
                }

            # Memory bandwidth test
            start_time = time.time()
            data = np.random.rand(10_000_000).astype(np.float32)
            result = np.sum(data)
            memory_time = time.time() - start_time
            
            benchmark_results["tests"]["memory_bandwidth"] = {
                "time_seconds": memory_time,
                "gb_per_second": (10_000_000 * 4) / (memory_time * 1e9)  # 4 bytes per float32
            }

        except Exception as e:
            benchmark_results["error"] = str(e)

        return benchmark_results