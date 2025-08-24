"""
Intel Hardware Provider for Intel Virtual Assistant Backend
Implements hardware detection and optimization for Intel Core Ultra 7, Arc GPU, and AI Boost NPU.
"""

import logging
import platform
import subprocess
import asyncio
from typing import Dict, Any, Optional
import psutil

from ..interfaces.providers import IHardwareProvider

logger = logging.getLogger(__name__)


class IntelHardwareProvider(IHardwareProvider):
    """Hardware provider specialized for Intel hardware detection and optimization."""

    def __init__(self):
        """Initialize Intel hardware provider."""
        self._hardware_info_cache: Optional[Dict[str, Any]] = None
        self._cache_timeout = 60  # Cache for 60 seconds
        self._last_cache_time = 0
        
        # Intel-specific detection patterns
        self._intel_cpu_families = {
            "Core Ultra": ["Core(TM) Ultra", "Core Ultra"],
            "Core i": ["Core(TM) i3", "Core(TM) i5", "Core(TM) i7", "Core(TM) i9"],
            "Lunar Lake": ["Core(TM) Ultra 7 258V", "Lunar Lake"],
            "Meteor Lake": ["Core(TM) Ultra", "Meteor Lake"]
        }
        
        self._intel_gpu_patterns = [
            "Intel(R) Arc(TM)",
            "Intel Arc Graphics",
            "Intel(R) Iris(R) Xe",
            "Intel(R) UHD Graphics"
        ]
        
        self._intel_npu_patterns = [
            "Intel(R) AI Boost",
            "Intel NPU",
            "Neural Processing Unit",
            "VPU"
        ]

    async def detect_hardware(self) -> Dict[str, Any]:
        """Detect Intel hardware components."""
        try:
            # Check cache first
            current_time = asyncio.get_event_loop().time()
            if (self._hardware_info_cache and 
                current_time - self._last_cache_time < self._cache_timeout):
                return self._hardware_info_cache

            logger.info("Detecting Intel hardware")
            
            hardware_info = {
                "cpu": await self._detect_intel_cpu(),
                "gpu": await self._detect_intel_gpu(), 
                "npu": await self._detect_intel_npu(),
                "memory": await self._detect_memory(),
                "system": await self._detect_system_info(),
                "optimization_features": await self._detect_optimization_features()
            }
            
            # Cache the results
            self._hardware_info_cache = hardware_info
            self._last_cache_time = current_time
            
            logger.info("Hardware detection completed")
            return hardware_info

        except Exception as e:
            logger.error(f"Error detecting hardware: {e}")
            return {}

    async def get_optimization_config(self, device_type: str) -> Dict[str, Any]:
        """Get optimization configuration for Intel hardware."""
        try:
            hardware_info = await self.detect_hardware()
            
            if device_type.upper() == "CPU":
                return await self._get_cpu_optimization_config(hardware_info["cpu"])
            elif device_type.upper() == "GPU":
                return await self._get_gpu_optimization_config(hardware_info["gpu"])
            elif device_type.upper() == "NPU":
                return await self._get_npu_optimization_config(hardware_info["npu"])
            else:
                return {}

        except Exception as e:
            logger.error(f"Error getting optimization config: {e}")
            return {}

    async def benchmark_device(self, device_type: str) -> Dict[str, Any]:
        """Run benchmark on Intel hardware."""
        try:
            logger.info(f"Benchmarking Intel {device_type}")
            
            if device_type.upper() == "CPU":
                return await self._benchmark_cpu()
            elif device_type.upper() == "GPU":
                return await self._benchmark_gpu()
            elif device_type.upper() == "NPU":
                return await self._benchmark_npu()
            else:
                return {"error": f"Unknown device type: {device_type}"}

        except Exception as e:
            logger.error(f"Error benchmarking {device_type}: {e}")
            return {"error": str(e)}

    async def get_power_profile(self) -> Dict[str, Any]:
        """Get Intel power management profile."""
        try:
            return {
                "profile": "balanced_performance",
                "cpu_power_policy": "performance",
                "gpu_power_policy": "adaptive",
                "npu_power_policy": "efficiency",
                "thermal_design_power": await self._get_tdp_info()
            }

        except Exception as e:
            logger.error(f"Error getting power profile: {e}")
            return {}

    # Private detection methods

    async def _detect_intel_cpu(self) -> Dict[str, Any]:
        """Detect Intel CPU information."""
        try:
            cpu_info = {
                "detected": False,
                "family": "unknown",
                "model": "unknown",
                "cores": 0,
                "threads": 0,
                "frequency": {"base": 0, "max": 0},
                "features": [],
                "intel_specific": {}
            }

            # Get basic CPU info
            cpu_info["cores"] = psutil.cpu_count(logical=False)
            cpu_info["threads"] = psutil.cpu_count(logical=True)
            
            # Get CPU frequency
            freq = psutil.cpu_freq()
            if freq:
                cpu_info["frequency"]["base"] = freq.current
                cpu_info["frequency"]["max"] = freq.max

            # Get processor name
            processor_name = platform.processor()
            cpu_info["model"] = processor_name

            # Check if it's Intel
            if "Intel" in processor_name:
                cpu_info["detected"] = True
                
                # Detect Intel CPU family
                for family, patterns in self._intel_cpu_families.items():
                    if any(pattern in processor_name for pattern in patterns):
                        cpu_info["family"] = family
                        break

                # Detect Intel-specific features
                cpu_info["features"] = await self._detect_cpu_features()
                cpu_info["intel_specific"] = await self._detect_intel_cpu_specific()

            return cpu_info

        except Exception as e:
            logger.error(f"Error detecting CPU: {e}")
            return {"detected": False, "error": str(e)}

    async def _detect_intel_gpu(self) -> Dict[str, Any]:
        """Detect Intel GPU information."""
        try:
            gpu_info = {
                "detected": False,
                "model": "unknown",
                "memory": 0,
                "driver_version": "unknown",
                "opencl_support": False,
                "vulkan_support": False,
                "intel_specific": {}
            }

            # Try multiple methods to detect GPU
            gpu_detected = False
            
            # Method 1: Windows Device Manager (via wmic)
            if platform.system() == "Windows":
                gpu_info.update(await self._detect_gpu_windows())
                gpu_detected = gpu_info.get("detected", False)
            
            # Method 2: Check for Intel GPU drivers
            if not gpu_detected:
                gpu_info.update(await self._detect_gpu_drivers())

            return gpu_info

        except Exception as e:
            logger.error(f"Error detecting GPU: {e}")
            return {"detected": False, "error": str(e)}

    async def _detect_intel_npu(self) -> Dict[str, Any]:
        """Detect Intel NPU (AI Boost) information."""
        try:
            npu_info = {
                "detected": False,
                "model": "unknown",
                "tops_performance": 0,
                "driver_version": "unknown",
                "openvino_support": False,
                "intel_specific": {}
            }

            # Check for Intel AI Boost NPU
            if platform.system() == "Windows":
                npu_info.update(await self._detect_npu_windows())

            # Check for NPU driver and support
            if npu_info.get("detected", False):
                npu_info["openvino_support"] = await self._check_openvino_npu_support()
                npu_info["intel_specific"] = await self._detect_npu_specific()

            return npu_info

        except Exception as e:
            logger.error(f"Error detecting NPU: {e}")
            return {"detected": False, "error": str(e)}

    async def _detect_memory(self) -> Dict[str, Any]:
        """Detect memory information."""
        try:
            memory = psutil.virtual_memory()
            
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "type": await self._detect_memory_type(),
                "speed": await self._detect_memory_speed(),
                "channels": await self._detect_memory_channels()
            }

        except Exception as e:
            logger.error(f"Error detecting memory: {e}")
            return {}

    async def _detect_system_info(self) -> Dict[str, Any]:
        """Detect system information."""
        try:
            return {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "hostname": platform.node(),
                "python_version": platform.python_version()
            }

        except Exception as e:
            logger.error(f"Error detecting system info: {e}")
            return {}

    async def _detect_optimization_features(self) -> Dict[str, Any]:
        """Detect Intel optimization features."""
        try:
            features = {
                "avx": False,
                "avx2": False,
                "avx512": False,
                "mkl_available": False,
                "openvino_available": False,
                "oneapi_available": False
            }

            # Check CPU features
            cpu_features = await self._detect_cpu_features()
            features["avx"] = "AVX" in cpu_features
            features["avx2"] = "AVX2" in cpu_features
            features["avx512"] = "AVX512" in cpu_features

            # Check Intel software availability
            features["mkl_available"] = await self._check_mkl_availability()
            features["openvino_available"] = await self._check_openvino_availability()
            features["oneapi_available"] = await self._check_oneapi_availability()

            return features

        except Exception as e:
            logger.error(f"Error detecting optimization features: {e}")
            return {}

    # Windows-specific detection methods

    async def _detect_gpu_windows(self) -> Dict[str, Any]:
        """Detect GPU on Windows using wmic."""
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                for line in output.split('\n'):
                    line = line.strip()
                    if any(pattern in line for pattern in self._intel_gpu_patterns):
                        return {
                            "detected": True,
                            "model": line,
                            "memory": await self._get_gpu_memory_windows(line)
                        }

        except Exception as e:
            logger.warning(f"Error detecting GPU on Windows: {e}")

        return {"detected": False}

    async def _detect_npu_windows(self) -> Dict[str, Any]:
        """Detect NPU on Windows."""
        try:
            # Check device manager for NPU
            result = subprocess.run(
                ["wmic", "path", "win32_PnPEntity", "get", "name"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                for line in output.split('\n'):
                    line = line.strip()
                    if any(pattern in line for pattern in self._intel_npu_patterns):
                        return {
                            "detected": True,
                            "model": line,
                            "tops_performance": await self._estimate_npu_performance(line)
                        }

        except Exception as e:
            logger.warning(f"Error detecting NPU on Windows: {e}")

        return {"detected": False}

    # Helper methods

    async def _detect_cpu_features(self) -> list:
        """Detect CPU features."""
        try:
            if platform.system() == "Windows":
                # Use wmic to get CPU features
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    # Extract features from CPU name (simplified)
                    features = []
                    output = result.stdout.lower()
                    if "avx" in output:
                        features.append("AVX")
                    if "avx2" in output:
                        features.append("AVX2")
                    if "avx512" in output or "avx-512" in output:
                        features.append("AVX512")
                    return features
        except Exception:
            pass
        
        return []

    async def _detect_intel_cpu_specific(self) -> Dict[str, Any]:
        """Detect Intel CPU-specific information."""
        return {
            "generation": "unknown",
            "code_name": "unknown",
            "microarchitecture": "unknown",
            "manufacturing_process": "unknown"
        }

    async def _detect_gpu_drivers(self) -> Dict[str, Any]:
        """Detect GPU drivers."""
        # Placeholder implementation
        return {"detected": False}

    async def _get_gpu_memory_windows(self, gpu_name: str) -> int:
        """Get GPU memory on Windows."""
        # Placeholder - would query WMI for actual memory
        return 2048  # 2GB estimate for integrated Intel GPU

    async def _check_openvino_npu_support(self) -> bool:
        """Check if OpenVINO supports NPU."""
        try:
            import openvino as ov
            core = ov.Core()
            available_devices = core.available_devices
            return any("NPU" in device for device in available_devices)
        except Exception:
            return False

    async def _detect_npu_specific(self) -> Dict[str, Any]:
        """Detect NPU-specific information."""
        return {
            "architecture": "unknown",
            "compute_units": 0,
            "supported_precisions": ["int8", "int4"]
        }

    async def _detect_memory_type(self) -> str:
        """Detect memory type."""
        # Placeholder - would need more sophisticated detection
        return "LPDDR5X"  # Common for Intel Core Ultra 7

    async def _detect_memory_speed(self) -> int:
        """Detect memory speed."""
        # Placeholder - would query DMI/SMBIOS
        return 8533  # LPDDR5X-8533 for Core Ultra 7

    async def _detect_memory_channels(self) -> int:
        """Detect memory channels."""
        # Placeholder
        return 2  # Dual channel common

    async def _estimate_npu_performance(self, npu_name: str) -> float:
        """Estimate NPU performance in TOPS."""
        # NPU 3720 in Core Ultra 7 provides ~10-13 TOPS
        if "AI Boost" in npu_name:
            return 10.0
        return 0.0

    async def _check_mkl_availability(self) -> bool:
        """Check if Intel MKL is available."""
        try:
            import mkl
            return True
        except ImportError:
            return False

    async def _check_openvino_availability(self) -> bool:
        """Check if OpenVINO is available."""
        try:
            import openvino
            return True
        except ImportError:
            return False

    async def _check_oneapi_availability(self) -> bool:
        """Check if Intel oneAPI is available."""
        # Check for oneAPI environment variables or tools
        import os
        return "ONEAPI_ROOT" in os.environ

    async def _get_tdp_info(self) -> Dict[str, Any]:
        """Get TDP information."""
        return {
            "cpu_tdp": 28,  # Core Ultra 7 258V TDP
            "gpu_tdp": 15,  # Estimated for integrated GPU
            "npu_tdp": 3    # Estimated for NPU
        }

    # Benchmark methods

    async def _benchmark_cpu(self) -> Dict[str, Any]:
        """Benchmark CPU performance."""
        try:
            import time
            
            # Simple CPU benchmark
            start_time = time.time()
            
            # CPU-intensive task
            result = sum(i * i for i in range(1000000))
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            return {
                "device": "CPU",
                "execution_time": execution_time,
                "score": 1000000 / execution_time,  # Operations per second
                "result": result,
                "test_type": "integer_arithmetic"
            }

        except Exception as e:
            logger.error(f"CPU benchmark error: {e}")
            return {"error": str(e)}

    async def _benchmark_gpu(self) -> Dict[str, Any]:
        """Benchmark GPU performance."""
        # Placeholder - would use OpenCL or GPU-specific benchmarks
        return {
            "device": "GPU",
            "score": 0,
            "note": "GPU benchmark not implemented"
        }

    async def _benchmark_npu(self) -> Dict[str, Any]:
        """Benchmark NPU performance."""
        # Placeholder - would use OpenVINO NPU benchmark
        return {
            "device": "NPU", 
            "score": 0,
            "note": "NPU benchmark not implemented"
        }

    # Optimization configuration methods

    async def _get_cpu_optimization_config(self, cpu_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get CPU optimization configuration."""
        cores = cpu_info.get("cores", 1)
        
        return {
            "device": "CPU",
            "threads": cores,
            "performance_hint": "LATENCY",
            "cpu_bind_thread": "YES",
            "cpu_threads_num": str(cores),
            "enable_cpu_pinning": True,
            "precision": "int8"
        }

    async def _get_gpu_optimization_config(self, gpu_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get GPU optimization configuration."""
        return {
            "device": "GPU",
            "performance_hint": "THROUGHPUT",
            "gpu_disable_winograd_convolution": "NO",
            "precision": "fp16"
        }

    async def _get_npu_optimization_config(self, npu_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get NPU optimization configuration."""
        return {
            "device": "NPU",
            "performance_hint": "LATENCY", 
            "npu_use_fast_compile": "YES",
            "precision": "int8"
        }