"""
Intel Hardware Optimizer for Arc GPU and NPU acceleration.
Handles device selection, model placement, and performance optimization.
"""

import os
import logging
import platform
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import psutil

from core.interfaces.model_provider import DeviceType, ModelType
from core.exceptions import IntelHardwareException

logger = logging.getLogger(__name__)

class IntelDevice(Enum):
    """Intel hardware devices."""
    CPU = "CPU"
    ARC_GPU = "GPU" 
    AI_BOOST_NPU = "NPU"

class IntelOptimizer:
    """Intel hardware optimizer for AI workloads."""
    
    def __init__(self):
        self._device_info = {}
        self._performance_profiles = {}
        self._model_configs = {}
        self._initialize_hardware_info()
        self._load_optimization_profiles()
    
    def _initialize_hardware_info(self) -> None:
        """Initialize Intel hardware information."""
        try:
            # CPU Information
            self._device_info["cpu"] = {
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "available": True
            }
            
            # Arc GPU Detection
            self._device_info["arc_gpu"] = self._detect_arc_gpu()
            
            # NPU Detection
            self._device_info["npu"] = self._detect_npu()
            
            logger.info(f"Intel hardware detected: {self._device_info}")
            
        except Exception as e:
            logger.warning(f"Failed to detect Intel hardware: {e}")
            # Fallback to CPU only
            self._device_info = {
                "cpu": {"available": True},
                "arc_gpu": {"available": False},
                "npu": {"available": False}
            }
    
    def _detect_arc_gpu(self) -> Dict[str, Any]:
        """Detect Intel Arc GPU."""
        try:
            # Try to detect Arc GPU through OpenVINO
            result = subprocess.run(
                ["python", "-c", "import openvino as ov; print([d for d in ov.Core().available_devices if 'GPU' in d])"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            gpu_devices = eval(result.stdout.strip()) if result.stdout.strip() else []
            
            if gpu_devices:
                return {
                    "available": True,
                    "devices": gpu_devices,
                    "primary_device": gpu_devices[0] if gpu_devices else None,
                    "memory": self._get_gpu_memory(),
                    "compute_units": self._get_gpu_compute_units()
                }
            
        except Exception as e:
            logger.debug(f"Arc GPU detection failed: {e}")
        
        return {"available": False}
    
    def _detect_npu(self) -> Dict[str, Any]:
        """Detect Intel AI Boost NPU."""
        try:
            # Try to detect NPU through OpenVINO
            result = subprocess.run(
                ["python", "-c", "import openvino as ov; print([d for d in ov.Core().available_devices if 'NPU' in d])"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            npu_devices = eval(result.stdout.strip()) if result.stdout.strip() else []
            
            if npu_devices:
                return {
                    "available": True,
                    "devices": npu_devices,
                    "primary_device": npu_devices[0] if npu_devices else None,
                    "version": self._get_npu_version()
                }
            
        except Exception as e:
            logger.debug(f"NPU detection failed: {e}")
        
        return {"available": False}
    
    def _get_gpu_memory(self) -> Optional[int]:
        """Get Arc GPU memory in MB."""
        try:
            # This would need platform-specific implementation
            # For now, return a reasonable default
            return 8192  # 8GB typical for Arc GPUs
        except:
            return None
    
    def _get_gpu_compute_units(self) -> Optional[int]:
        """Get Arc GPU compute units."""
        try:
            # This would need platform-specific implementation
            return 128  # Typical for Arc A770
        except:
            return None
    
    def _get_npu_version(self) -> Optional[str]:
        """Get NPU version."""
        try:
            # This would detect actual NPU version
            return "AI Boost NPU"
        except:
            return None
    
    def _load_optimization_profiles(self) -> None:
        """Load Intel optimization profiles for different models."""
        self._performance_profiles = {
            # LLM Models
            "qwen2.5-7b-int4": {
                "preferred_device": "arc_gpu",
                "fallback_device": "cpu",
                "batch_size": 1,
                "num_threads": 4,
                "memory_optimization": True,
                "precision": "INT4"
            },
            "phi-3-mini-int4": {
                "preferred_device": "arc_gpu",
                "fallback_device": "cpu",
                "batch_size": 2,
                "num_threads": 4,
                "memory_optimization": True,
                "precision": "INT4"
            },
            "tinyllama-1.1b-int4": {
                "preferred_device": "npu",
                "fallback_device": "cpu",
                "batch_size": 1,
                "num_threads": 2,
                "memory_optimization": True,
                "precision": "INT4"
            },
            
            # Voice Models
            "whisper-base": {
                "preferred_device": "npu",
                "fallback_device": "cpu",
                "batch_size": 1,
                "precision": "FP16"
            },
            "speecht5-tts": {
                "preferred_device": "npu",
                "fallback_device": "cpu",
                "batch_size": 1,
                "precision": "FP16"
            }
        }
    
    def select_optimal_device(self, model_name: str, model_type: ModelType) -> str:
        """Select the optimal device for a model."""
        profile = self._performance_profiles.get(model_name, {})
        
        # Get preferred device
        preferred = profile.get("preferred_device", "cpu")
        fallback = profile.get("fallback_device", "cpu")
        
        # Map to actual device availability
        device_map = {
            "arc_gpu": self._device_info["arc_gpu"]["available"],
            "npu": self._device_info["npu"]["available"],
            "cpu": self._device_info["cpu"]["available"]
        }
        
        if device_map.get(preferred, False):
            return preferred.upper()
        elif device_map.get(fallback, False):
            logger.warning(f"Preferred device {preferred} not available, using fallback {fallback}")
            return fallback.upper()
        else:
            logger.warning("No optimal device available, defaulting to CPU")
            return "CPU"
    
    def get_model_config(self, model_name: str, device: str) -> Dict[str, Any]:
        """Get optimized configuration for a model on a specific device."""
        profile = self._performance_profiles.get(model_name, {})
        
        base_config = {
            "device": device,
            "num_threads": profile.get("num_threads", 4),
            "batch_size": profile.get("batch_size", 1),
            "precision": profile.get("precision", "FP16"),
            "memory_optimization": profile.get("memory_optimization", True)
        }
        
        # Device-specific optimizations
        if device == "GPU":
            base_config.update({
                "enable_gpu_caching": True,
                "gpu_memory_fraction": 0.8,
                "enable_mixed_precision": True
            })
        elif device == "NPU":
            base_config.update({
                "enable_npu_optimization": True,
                "low_latency_mode": True,
                "power_efficiency": True
            })
        else:  # CPU
            base_config.update({
                "enable_cpu_extension": True,
                "cpu_threads_num": psutil.cpu_count(logical=True),
                "enable_parallel_processing": True
            })
        
        return base_config
    
    def get_hardware_summary(self) -> Dict[str, Any]:
        """Get summary of available Intel hardware."""
        return {
            "cpu": {
                "available": self._device_info["cpu"]["available"],
                "cores": self._device_info["cpu"].get("cores", 0),
                "threads": self._device_info["cpu"].get("threads", 0)
            },
            "arc_gpu": {
                "available": self._device_info["arc_gpu"]["available"],
                "memory_mb": self._device_info["arc_gpu"].get("memory", 0),
                "compute_units": self._device_info["arc_gpu"].get("compute_units", 0)
            },
            "npu": {
                "available": self._device_info["npu"]["available"],
                "version": self._device_info["npu"].get("version", "Unknown")
            }
        }
    
    def optimize_inference_params(
        self, 
        model_name: str, 
        device: str, 
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """Get optimized inference parameters."""
        config = self.get_model_config(model_name, device)
        
        # Adjust parameters based on hardware capabilities
        if device == "GPU" and self._device_info["arc_gpu"]["available"]:
            # GPU optimizations
            batch_size = min(config["batch_size"], max_tokens // 64)
            return {
                "batch_size": max(1, batch_size),
                "do_sample": True,
                "num_beams": 1,  # Faster for interactive use
                "early_stopping": True,
                "use_cache": True
            }
        elif device == "NPU" and self._device_info["npu"]["available"]:
            # NPU optimizations - focus on low latency
            return {
                "batch_size": 1,
                "do_sample": True,
                "num_beams": 1,
                "early_stopping": True,
                "use_cache": True,
                "low_latency": True
            }
        else:
            # CPU optimizations
            return {
                "batch_size": 1,
                "do_sample": True,
                "num_beams": 1,
                "early_stopping": True,
                "use_cache": True,
                "num_threads": config["num_threads"]
            }
    
    def suggest_model_for_task(self, task_type: str) -> Tuple[str, str]:
        """Suggest the best model and device for a task."""
        task_models = {
            "conversation": ("qwen2.5-7b-int4", self.select_optimal_device("qwen2.5-7b-int4", ModelType.LLM)),
            "quick_response": ("phi-3-mini-int4", self.select_optimal_device("phi-3-mini-int4", ModelType.LLM)),
            "tool_routing": ("tinyllama-1.1b-int4", self.select_optimal_device("tinyllama-1.1b-int4", ModelType.LLM)),
            "speech_to_text": ("whisper-base", self.select_optimal_device("whisper-base", ModelType.STT)),
            "text_to_speech": ("speecht5-tts", self.select_optimal_device("speecht5-tts", ModelType.TTS))
        }
        
        return task_models.get(task_type, ("qwen2.5-7b-int4", "CPU"))
    
    def monitor_performance(self) -> Dict[str, Any]:
        """Monitor hardware performance metrics."""
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "temperature": self._get_temperature(),
                "power_usage": self._get_power_usage()
            }
        except Exception as e:
            logger.warning(f"Performance monitoring failed: {e}")
            return {}
    
    def _get_temperature(self) -> Optional[float]:
        """Get system temperature."""
        try:
            # This would need platform-specific implementation
            return None
        except:
            return None
    
    def _get_power_usage(self) -> Optional[float]:
        """Get power usage."""
        try:
            # This would need platform-specific implementation
            return None
        except:
            return None