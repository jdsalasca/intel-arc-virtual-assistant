"""
Intel Hardware Profile Configurations
Defines optimized settings for different Intel hardware combinations.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)

class IntelProcessorType(Enum):
    """Intel processor types."""
    CORE_ULTRA_7 = "core_ultra_7"
    CORE_I7 = "core_i7"
    CORE_I5 = "core_i5"
    CORE_I3 = "core_i3"
    XEON = "xeon"
    ATOM = "atom"

class IntelGPUType(Enum):
    """Intel GPU types."""
    ARC_A770 = "arc_a770"
    ARC_A750 = "arc_a750"
    ARC_A580 = "arc_a580"
    ARC_A380 = "arc_a380"
    IRIS_XE = "iris_xe"
    UHD_GRAPHICS = "uhd_graphics"
    NONE = "none"

class IntelNPUType(Enum):
    """Intel NPU types."""
    AI_BOOST_NPU = "ai_boost_npu"
    NEURAL_ENGINE = "neural_engine"
    NONE = "none"

@dataclass
class HardwareCapabilities:
    """Hardware capabilities for a specific component."""
    available: bool = False
    memory_mb: int = 0
    compute_units: int = 0
    max_performance: str = "medium"  # low, medium, high, ultra
    power_efficiency: str = "medium"  # low, medium, high, ultra
    supported_precisions: List[str] = None
    
    def __post_init__(self):
        if self.supported_precisions is None:
            self.supported_precisions = ["FP32", "FP16"]

@dataclass
class IntelHardwareProfile:
    """Complete Intel hardware profile."""
    name: str
    description: str
    processor_type: IntelProcessorType
    gpu_type: IntelGPUType
    npu_type: IntelNPUType
    
    # Component capabilities
    cpu_capabilities: HardwareCapabilities
    gpu_capabilities: HardwareCapabilities
    npu_capabilities: HardwareCapabilities
    
    # System specifications
    total_memory_gb: int = 16
    storage_type: str = "SSD"  # SSD, HDD, NVME
    
    # Optimization settings
    model_configurations: Dict[str, Dict[str, Any]] = None
    performance_presets: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.model_configurations is None:
            self.model_configurations = {}
        if self.performance_presets is None:
            self.performance_presets = {}

class IntelProfileManager:
    """Manager for Intel hardware profiles."""
    
    def __init__(self):
        self.profiles = self._initialize_profiles()
        self.current_profile: Optional[IntelHardwareProfile] = None
        self.detected_profile: Optional[IntelHardwareProfile] = None
    
    def _initialize_profiles(self) -> Dict[str, IntelHardwareProfile]:
        """Initialize predefined Intel hardware profiles."""
        profiles = {}
        
        # Core Ultra 7 + Arc A770 + NPU (High-end)
        profiles["ultra7_arc770_npu"] = IntelHardwareProfile(
            name="Intel Core Ultra 7 + Arc A770 + NPU",
            description="High-performance setup with Arc GPU and AI Boost NPU",
            processor_type=IntelProcessorType.CORE_ULTRA_7,
            gpu_type=IntelGPUType.ARC_A770,
            npu_type=IntelNPUType.AI_BOOST_NPU,
            cpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=16384,  # 16GB system RAM
                compute_units=16,  # 16 cores/threads
                max_performance="ultra",
                power_efficiency="high",
                supported_precisions=["FP32", "FP16", "INT8", "INT4"]
            ),
            gpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=16384,  # 16GB VRAM
                compute_units=512,  # Xe cores
                max_performance="ultra",
                power_efficiency="medium",
                supported_precisions=["FP32", "FP16", "INT8", "INT4"]
            ),
            npu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=2048,  # Shared memory
                compute_units=8,  # NPU units
                max_performance="high",
                power_efficiency="ultra",
                supported_precisions=["FP16", "INT8", "INT4"]
            ),
            total_memory_gb=32,
            storage_type="NVME",
            model_configurations={
                "qwen2.5-7b-int4": {
                    "preferred_device": "GPU",
                    "batch_size": 4,
                    "max_tokens": 512,
                    "temperature": 0.7,
                    "precision": "INT4"
                },
                "phi-3-mini-int4": {
                    "preferred_device": "GPU",
                    "batch_size": 8,
                    "max_tokens": 256,
                    "temperature": 0.8,
                    "precision": "INT4"
                },
                "whisper-base": {
                    "preferred_device": "NPU",
                    "batch_size": 1,
                    "precision": "FP16"
                },
                "speecht5-tts": {
                    "preferred_device": "NPU",
                    "batch_size": 1,
                    "precision": "FP16"
                }
            },
            performance_presets={
                "max_performance": {
                    "gpu_memory_fraction": 0.9,
                    "enable_mixed_precision": True,
                    "enable_graph_optimization": True,
                    "parallel_inference": True
                },
                "balanced": {
                    "gpu_memory_fraction": 0.7,
                    "enable_mixed_precision": True,
                    "enable_graph_optimization": True,
                    "parallel_inference": False
                },
                "power_efficient": {
                    "gpu_memory_fraction": 0.5,
                    "enable_mixed_precision": True,
                    "enable_graph_optimization": False,
                    "parallel_inference": False
                }
            }
        )
        
        # Core Ultra 7 + Arc A750 + NPU (Mid-high)
        profiles["ultra7_arc750_npu"] = IntelHardwareProfile(
            name="Intel Core Ultra 7 + Arc A750 + NPU",
            description="Mid-high performance with Arc A750 GPU and AI Boost NPU",
            processor_type=IntelProcessorType.CORE_ULTRA_7,
            gpu_type=IntelGPUType.ARC_A750,
            npu_type=IntelNPUType.AI_BOOST_NPU,
            cpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=16384,
                compute_units=16,
                max_performance="ultra",
                power_efficiency="high",
                supported_precisions=["FP32", "FP16", "INT8", "INT4"]
            ),
            gpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=8192,  # 8GB VRAM
                compute_units=448,  # Xe cores
                max_performance="high",
                power_efficiency="medium",
                supported_precisions=["FP32", "FP16", "INT8", "INT4"]
            ),
            npu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=2048,
                compute_units=8,
                max_performance="high",
                power_efficiency="ultra",
                supported_precisions=["FP16", "INT8", "INT4"]
            ),
            total_memory_gb=32,
            storage_type="NVME",
            model_configurations={
                "qwen2.5-7b-int4": {
                    "preferred_device": "GPU",
                    "batch_size": 2,
                    "max_tokens": 256,
                    "temperature": 0.7,
                    "precision": "INT4"
                },
                "phi-3-mini-int4": {
                    "preferred_device": "GPU",
                    "batch_size": 4,
                    "max_tokens": 256,
                    "temperature": 0.8,
                    "precision": "INT4"
                }
            }
        )
        
        # Core i7 + Iris Xe + No NPU (Mid-range)
        profiles["i7_irisxe"] = IntelHardwareProfile(
            name="Intel Core i7 + Iris Xe Graphics",
            description="Mid-range setup with integrated Iris Xe graphics",
            processor_type=IntelProcessorType.CORE_I7,
            gpu_type=IntelGPUType.IRIS_XE,
            npu_type=IntelNPUType.NONE,
            cpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=16384,
                compute_units=12,
                max_performance="high",
                power_efficiency="high",
                supported_precisions=["FP32", "FP16", "INT8"]
            ),
            gpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=4096,  # Shared system memory
                compute_units=96,  # Xe cores
                max_performance="medium",
                power_efficiency="high",
                supported_precisions=["FP32", "FP16"]
            ),
            npu_capabilities=HardwareCapabilities(
                available=False
            ),
            total_memory_gb=16,
            storage_type="SSD",
            model_configurations={
                "phi-3-mini-int4": {
                    "preferred_device": "GPU",
                    "batch_size": 1,
                    "max_tokens": 128,
                    "temperature": 0.7,
                    "precision": "FP16"
                },
                "qwen2.5-7b-int4": {
                    "preferred_device": "CPU",
                    "batch_size": 1,
                    "max_tokens": 256,
                    "temperature": 0.7,
                    "precision": "INT8"
                }
            }
        )
        
        # Core i5 + UHD Graphics (Entry-level)
        profiles["i5_uhd"] = IntelHardwareProfile(
            name="Intel Core i5 + UHD Graphics",
            description="Entry-level setup with integrated UHD graphics",
            processor_type=IntelProcessorType.CORE_I5,
            gpu_type=IntelGPUType.UHD_GRAPHICS,
            npu_type=IntelNPUType.NONE,
            cpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=8192,
                compute_units=8,
                max_performance="medium",
                power_efficiency="high",
                supported_precisions=["FP32", "FP16"]
            ),
            gpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=2048,  # Shared system memory
                compute_units=32,  # Execution units
                max_performance="low",
                power_efficiency="ultra",
                supported_precisions=["FP32", "FP16"]
            ),
            npu_capabilities=HardwareCapabilities(
                available=False
            ),
            total_memory_gb=16,
            storage_type="SSD",
            model_configurations={
                "phi-3-mini-int4": {
                    "preferred_device": "CPU",
                    "batch_size": 1,
                    "max_tokens": 128,
                    "temperature": 0.7,
                    "precision": "FP16"
                },
                "tinyllama-1.1b-int4": {
                    "preferred_device": "CPU",
                    "batch_size": 1,
                    "max_tokens": 256,
                    "temperature": 0.8,
                    "precision": "FP16"
                }
            }
        )
        
        # CPU-only profile (Fallback)
        profiles["cpu_only"] = IntelHardwareProfile(
            name="Intel CPU Only",
            description="CPU-only configuration for systems without dedicated GPU/NPU",
            processor_type=IntelProcessorType.CORE_I7,  # Generic
            gpu_type=IntelGPUType.NONE,
            npu_type=IntelNPUType.NONE,
            cpu_capabilities=HardwareCapabilities(
                available=True,
                memory_mb=8192,
                compute_units=8,
                max_performance="medium",
                power_efficiency="medium",
                supported_precisions=["FP32", "FP16", "INT8"]
            ),
            gpu_capabilities=HardwareCapabilities(
                available=False
            ),
            npu_capabilities=HardwareCapabilities(
                available=False
            ),
            total_memory_gb=16,
            storage_type="SSD",
            model_configurations={
                "phi-3-mini-int4": {
                    "preferred_device": "CPU",
                    "batch_size": 1,
                    "max_tokens": 128,
                    "temperature": 0.7,
                    "precision": "INT8"
                },
                "tinyllama-1.1b-int4": {
                    "preferred_device": "CPU",
                    "batch_size": 1,
                    "max_tokens": 256,
                    "temperature": 0.8,
                    "precision": "FP16"
                }
            }
        )
        
        return profiles
    
    def get_profile(self, profile_name: str) -> Optional[IntelHardwareProfile]:
        """Get a profile by name."""
        return self.profiles.get(profile_name)
    
    def list_profiles(self) -> List[str]:
        """List available profile names."""
        return list(self.profiles.keys())
    
    def get_profile_details(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a profile."""
        profile = self.profiles.get(profile_name)
        if not profile:
            return None
        
        return {
            "name": profile.name,
            "description": profile.description,
            "processor": profile.processor_type.value,
            "gpu": profile.gpu_type.value,
            "npu": profile.npu_type.value,
            "capabilities": {
                "cpu": {
                    "available": profile.cpu_capabilities.available,
                    "cores": profile.cpu_capabilities.compute_units,
                    "performance": profile.cpu_capabilities.max_performance,
                    "efficiency": profile.cpu_capabilities.power_efficiency
                },
                "gpu": {
                    "available": profile.gpu_capabilities.available,
                    "memory_mb": profile.gpu_capabilities.memory_mb,
                    "compute_units": profile.gpu_capabilities.compute_units,
                    "performance": profile.gpu_capabilities.max_performance
                },
                "npu": {
                    "available": profile.npu_capabilities.available,
                    "compute_units": profile.npu_capabilities.compute_units,
                    "performance": profile.npu_capabilities.max_performance if profile.npu_capabilities.available else "none"
                }
            },
            "system": {
                "memory_gb": profile.total_memory_gb,
                "storage": profile.storage_type
            },
            "supported_models": list(profile.model_configurations.keys())
        }
    
    def auto_detect_profile(self, hardware_info: Dict[str, Any]) -> Optional[str]:
        """Auto-detect the best profile based on hardware information."""
        try:
            # Extract hardware capabilities
            has_arc_gpu = hardware_info.get("arc_gpu", {}).get("available", False)
            has_npu = hardware_info.get("npu", {}).get("available", False)
            cpu_cores = hardware_info.get("cpu", {}).get("threads", 8)
            
            # Determine best profile
            if has_arc_gpu and has_npu:
                # Check GPU type based on memory or compute units
                gpu_memory = hardware_info.get("arc_gpu", {}).get("memory", 0)
                if gpu_memory >= 12000:  # >= 12GB
                    return "ultra7_arc770_npu"
                elif gpu_memory >= 6000:  # >= 6GB
                    return "ultra7_arc750_npu"
                else:
                    return "ultra7_arc750_npu"  # Default Arc profile
            elif has_arc_gpu:
                return "ultra7_arc750_npu"  # Arc without NPU
            elif has_npu:
                # NPU without dedicated GPU - use high-end CPU with NPU
                if cpu_cores >= 12:
                    return "i7_irisxe"  # High-end CPU with integrated graphics
                else:
                    return "i5_uhd"  # Mid-range CPU with integrated graphics
            else:
                # No dedicated GPU or NPU - check for integrated graphics hint
                # If hardware_info explicitly says no GPU at all, use cpu_only
                gpu_info = hardware_info.get("arc_gpu", {})
                if gpu_info.get("available") is False:
                    # Explicitly no GPU available
                    return "cpu_only"
                elif cpu_cores >= 12:
                    return "i7_irisxe"  # High-end CPU (likely has integrated graphics)
                elif cpu_cores >= 6:
                    return "i5_uhd"  # Mid-range CPU (likely has integrated graphics)
                else:
                    return "cpu_only"  # Low-end CPU or explicitly CPU-only
                
        except Exception as e:
            logger.error(f"Profile auto-detection failed: {e}")
            return "cpu_only"
    
    def set_current_profile(self, profile_name: str) -> bool:
        """Set the current active profile."""
        profile = self.profiles.get(profile_name)
        if profile:
            self.current_profile = profile
            logger.info(f"Set current profile to: {profile_name}")
            return True
        return False
    
    def get_model_config(self, model_name: str, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get model configuration for a specific profile."""
        profile = self.profiles.get(profile_name) if profile_name else self.current_profile
        
        if not profile:
            # Return default configuration
            return {
                "preferred_device": "CPU",
                "batch_size": 1,
                "max_tokens": 256,
                "temperature": 0.7,
                "precision": "FP16"
            }
        
        return profile.model_configurations.get(model_name, {
            "preferred_device": "CPU",
            "batch_size": 1,
            "max_tokens": 128,
            "temperature": 0.7,
            "precision": "FP16"
        })
    
    def get_performance_preset(self, preset_name: str, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance preset for a profile."""
        profile = self.profiles.get(profile_name) if profile_name else self.current_profile
        
        if not profile:
            return {}
        
        return profile.performance_presets.get(preset_name, {})
    
    def optimize_for_profile(self, profile_name: str) -> Dict[str, Any]:
        """Get optimization recommendations for a profile."""
        profile = self.profiles.get(profile_name)
        if not profile:
            return {}
        
        recommendations = {
            "models": {},
            "settings": {},
            "warnings": []
        }
        
        # Model recommendations
        if profile.gpu_capabilities.available and profile.gpu_capabilities.memory_mb >= 8192:
            recommendations["models"]["primary"] = "qwen2.5-7b-int4"
            recommendations["models"]["fallback"] = "phi-3-mini-int4"
        elif profile.gpu_capabilities.available:
            recommendations["models"]["primary"] = "phi-3-mini-int4"
            recommendations["models"]["fallback"] = "tinyllama-1.1b-int4"
        else:
            recommendations["models"]["primary"] = "phi-3-mini-int4"
            recommendations["models"]["fallback"] = "tinyllama-1.1b-int4"
        
        # Voice model recommendations
        if profile.npu_capabilities.available:
            recommendations["models"]["tts"] = "speecht5-tts"
            recommendations["models"]["stt"] = "whisper-base"
            recommendations["settings"]["voice_device"] = "NPU"
        else:
            recommendations["models"]["tts"] = "web_speech_api"
            recommendations["models"]["stt"] = "web_speech_api"
            recommendations["settings"]["voice_device"] = "CPU"
        
        # Performance settings
        if profile.gpu_capabilities.max_performance == "ultra":
            recommendations["settings"]["performance_mode"] = "max_performance"
            recommendations["settings"]["parallel_processing"] = True
        elif profile.gpu_capabilities.max_performance == "high":
            recommendations["settings"]["performance_mode"] = "balanced"
            recommendations["settings"]["parallel_processing"] = False
        else:
            recommendations["settings"]["performance_mode"] = "power_efficient"
            recommendations["settings"]["parallel_processing"] = False
        
        # Warnings
        if profile.total_memory_gb < 16:
            recommendations["warnings"].append("Low system memory - consider reducing model size")
        
        if not profile.gpu_capabilities.available:
            recommendations["warnings"].append("No GPU detected - performance may be limited")
        
        if not profile.npu_capabilities.available:
            recommendations["warnings"].append("No NPU detected - using CPU for voice processing")
        
        return recommendations
    
    def export_profile(self, profile_name: str) -> Optional[str]:
        """Export a profile to JSON format."""
        profile = self.profiles.get(profile_name)
        if not profile:
            return None
        
        # Convert to serializable format
        profile_dict = {
            "name": profile.name,
            "description": profile.description,
            "processor_type": profile.processor_type.value,
            "gpu_type": profile.gpu_type.value,
            "npu_type": profile.npu_type.value,
            "total_memory_gb": profile.total_memory_gb,
            "storage_type": profile.storage_type,
            "model_configurations": profile.model_configurations,
            "performance_presets": profile.performance_presets
        }
        
        return json.dumps(profile_dict, indent=2)
    
    def import_profile(self, profile_json: str, profile_name: str) -> bool:
        """Import a profile from JSON format."""
        try:
            profile_dict = json.loads(profile_json)
            
            # Create profile from dict (simplified - would need full conversion)
            # This is a basic implementation
            self.profiles[profile_name] = profile_dict
            
            logger.info(f"Imported profile: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import profile: {e}")
            return False