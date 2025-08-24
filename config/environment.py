"""
Environment Configuration
Manages environment variables and external service configurations.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class OpenVINOConfig:
    """OpenVINO environment configuration."""
    # Model paths
    model_cache_dir: str = "models"
    openvino_cache_dir: str = "cache/openvino"
    
    # Device preferences
    inference_device: str = "AUTO"  # AUTO, CPU, GPU, NPU
    gpu_device_id: int = 0
    
    # Performance settings
    num_streams: int = 1
    inference_num_threads: int = 0  # 0 = auto
    enable_profiling: bool = False
    
    # Memory settings
    enable_cpu_pinning: bool = False
    enable_memory_pool: bool = True

@dataclass
class IntelOptimizationConfig:
    """Intel-specific optimization configuration."""
    # Intel MKL settings
    mkl_num_threads: int = 0  # 0 = auto
    mkl_enable_instructions: str = "AUTO"  # AUTO, SSE4_2, AVX, AVX2, AVX512
    
    # Intel OpenMP settings
    omp_num_threads: int = 0  # 0 = auto
    omp_dynamic: bool = True
    
    # Intel GPU settings
    gpu_backend: str = "ocl"  # ocl (OpenCL), level_zero
    gpu_memory_pool_size: int = 1024  # MB
    
    # Intel NPU settings
    npu_compiler_type: str = "DRIVER"  # DRIVER, MLIR
    npu_execution_mode: str = "SYNC"  # SYNC, ASYNC

@dataclass
class ExternalServicesConfig:
    """External services configuration."""
    # OpenAI API (for comparison/fallback)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"
    
    # HuggingFace Hub
    huggingface_token: str = ""
    huggingface_cache_dir: str = "cache/huggingface"
    
    # Google APIs (for Gmail integration)
    google_credentials_file: str = "credentials/google_credentials.json"
    google_token_file: str = "credentials/google_token.json"
    
    # Web search APIs
    search_api_key: str = ""
    search_engine_id: str = ""

class EnvironmentManager:
    """Manages environment variables and configurations."""
    
    def __init__(self):
        self.openvino = OpenVINOConfig()
        self.intel_optimization = IntelOptimizationConfig()
        self.external_services = ExternalServicesConfig()
        
        # Load environment variables
        self.load_environment()
        
        # Apply Intel optimizations
        self.setup_intel_environment()
    
    def load_environment(self):
        """Load configuration from environment variables."""
        # OpenVINO configuration
        self.openvino.model_cache_dir = os.getenv("MODEL_CACHE_DIR", self.openvino.model_cache_dir)
        self.openvino.openvino_cache_dir = os.getenv("OPENVINO_CACHE_DIR", self.openvino.openvino_cache_dir)
        self.openvino.inference_device = os.getenv("OPENVINO_DEVICE", self.openvino.inference_device)
        self.openvino.gpu_device_id = int(os.getenv("OPENVINO_GPU_ID", str(self.openvino.gpu_device_id)))
        self.openvino.num_streams = int(os.getenv("OPENVINO_NUM_STREAMS", str(self.openvino.num_streams)))
        
        # Intel optimization configuration
        self.intel_optimization.mkl_num_threads = int(os.getenv("MKL_NUM_THREADS", str(self.intel_optimization.mkl_num_threads)))
        self.intel_optimization.omp_num_threads = int(os.getenv("OMP_NUM_THREADS", str(self.intel_optimization.omp_num_threads)))
        self.intel_optimization.gpu_backend = os.getenv("INTEL_GPU_BACKEND", self.intel_optimization.gpu_backend)
        
        # External services
        self.external_services.openai_api_key = os.getenv("OPENAI_API_KEY", self.external_services.openai_api_key)
        self.external_services.openai_base_url = os.getenv("OPENAI_BASE_URL", self.external_services.openai_base_url)
        self.external_services.huggingface_token = os.getenv("HUGGINGFACE_TOKEN", self.external_services.huggingface_token)
        self.external_services.search_api_key = os.getenv("SEARCH_API_KEY", self.external_services.search_api_key)
        
        logger.info("Environment configuration loaded")
    
    def setup_intel_environment(self):
        """Set up Intel-specific environment variables."""
        try:
            # Intel MKL optimizations
            if self.intel_optimization.mkl_num_threads > 0:
                os.environ["MKL_NUM_THREADS"] = str(self.intel_optimization.mkl_num_threads)
            
            # Intel OpenMP optimizations
            if self.intel_optimization.omp_num_threads > 0:
                os.environ["OMP_NUM_THREADS"] = str(self.intel_optimization.omp_num_threads)
            
            if self.intel_optimization.omp_dynamic:
                os.environ["OMP_DYNAMIC"] = "TRUE"
            
            # Intel GPU optimizations
            os.environ["INTEL_GPU_BACKEND"] = self.intel_optimization.gpu_backend
            
            # OpenVINO optimizations
            os.environ["OPENVINO_DEVICE"] = self.openvino.inference_device
            
            if self.openvino.enable_cpu_pinning:
                os.environ["OV_CPU_BIND_THREAD"] = "HYBRID_AWARE"
            
            # Create necessary directories
            self._create_directories()
            
            logger.info("Intel environment optimizations applied")
            
        except Exception as e:
            logger.error(f"Failed to setup Intel environment: {e}")
    
    def _create_directories(self):
        """Create necessary directories."""
        directories = [
            self.openvino.model_cache_dir,
            self.openvino.openvino_cache_dir,
            self.external_services.huggingface_cache_dir,
            "cache",
            "data/conversations",
            "logs",
            "credentials"
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create directory {directory}: {e}")
    
    def get_openvino_config(self) -> Dict[str, Any]:
        """Get OpenVINO configuration dictionary."""
        return {
            "model_cache_dir": self.openvino.model_cache_dir,
            "cache_dir": self.openvino.openvino_cache_dir,
            "device": self.openvino.inference_device,
            "gpu_device_id": self.openvino.gpu_device_id,
            "num_streams": self.openvino.num_streams,
            "inference_num_threads": self.openvino.inference_num_threads,
            "enable_profiling": self.openvino.enable_profiling,
            "enable_cpu_pinning": self.openvino.enable_cpu_pinning,
            "enable_memory_pool": self.openvino.enable_memory_pool
        }
    
    def get_model_path(self, model_name: str) -> str:
        """Get the full path for a model."""
        return os.path.join(self.openvino.model_cache_dir, model_name)
    
    def is_model_cached(self, model_name: str) -> bool:
        """Check if a model is already cached."""
        model_path = self.get_model_path(model_name)
        return os.path.exists(model_path)
    
    def get_huggingface_config(self) -> Dict[str, Any]:
        """Get HuggingFace configuration."""
        return {
            "token": self.external_services.huggingface_token,
            "cache_dir": self.external_services.huggingface_cache_dir
        }
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return {
            "api_key": self.external_services.openai_api_key,
            "base_url": self.external_services.openai_base_url,
            "model": self.external_services.openai_model
        }
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate environment configuration."""
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "info": []
        }
        
        # Check critical directories
        critical_dirs = [self.openvino.model_cache_dir]
        for dir_path in critical_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    validation_results["info"].append(f"Created directory: {dir_path}")
                except Exception as e:
                    validation_results["errors"].append(f"Cannot create directory {dir_path}: {e}")
                    validation_results["valid"] = False
        
        # Check OpenVINO installation
        try:
            import openvino
            validation_results["info"].append(f"OpenVINO version: {openvino.__version__}")
        except ImportError:
            validation_results["errors"].append("OpenVINO not installed")
            validation_results["valid"] = False
        
        # Check Intel optimizations
        if self.intel_optimization.mkl_num_threads == 0:
            validation_results["warnings"].append("MKL_NUM_THREADS not set - using auto detection")
        
        # Check external services
        if not self.external_services.openai_api_key:
            validation_results["warnings"].append("OpenAI API key not configured")
        
        if not self.external_services.huggingface_token:
            validation_results["warnings"].append("HuggingFace token not configured")
        
        return validation_results
    
    def export_environment_file(self, file_path: str = ".env") -> bool:
        """Export current configuration to .env file."""
        try:
            with open(file_path, 'w') as f:
                f.write("# Intel AI Assistant Environment Configuration\n\n")
                
                f.write("# OpenVINO Configuration\n")
                f.write(f"MODEL_CACHE_DIR={self.openvino.model_cache_dir}\n")
                f.write(f"OPENVINO_CACHE_DIR={self.openvino.openvino_cache_dir}\n")
                f.write(f"OPENVINO_DEVICE={self.openvino.inference_device}\n")
                f.write(f"OPENVINO_GPU_ID={self.openvino.gpu_device_id}\n")
                f.write(f"OPENVINO_NUM_STREAMS={self.openvino.num_streams}\n\n")
                
                f.write("# Intel Optimization\n")
                f.write(f"MKL_NUM_THREADS={self.intel_optimization.mkl_num_threads}\n")
                f.write(f"OMP_NUM_THREADS={self.intel_optimization.omp_num_threads}\n")
                f.write(f"INTEL_GPU_BACKEND={self.intel_optimization.gpu_backend}\n\n")
                
                f.write("# External Services\n")
                f.write(f"OPENAI_API_KEY={self.external_services.openai_api_key}\n")
                f.write(f"OPENAI_BASE_URL={self.external_services.openai_base_url}\n")
                f.write(f"HUGGINGFACE_TOKEN={self.external_services.huggingface_token}\n")
                f.write(f"SEARCH_API_KEY={self.external_services.search_api_key}\n\n")
                
                f.write("# Development Settings\n")
                f.write("ENVIRONMENT=development\n")
                f.write("LOG_LEVEL=INFO\n")
                f.write("DEBUG=false\n")
            
            logger.info(f"Environment file exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export environment file: {e}")
            return False
    
    def load_from_env_file(self, file_path: str = ".env") -> bool:
        """Load configuration from .env file."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Environment file not found: {file_path}")
                return False
            
            from dotenv import load_dotenv
            load_dotenv(file_path)
            
            # Reload environment after loading .env file
            self.load_environment()
            
            logger.info(f"Environment loaded from: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load environment file: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for diagnostics."""
        import platform
        import psutil
        
        try:
            return {
                "platform": {
                    "system": platform.system(),
                    "platform": platform.platform(),
                    "processor": platform.processor(),
                    "architecture": platform.architecture(),
                    "python_version": platform.python_version()
                },
                "hardware": {
                    "cpu_count": psutil.cpu_count(),
                    "cpu_count_logical": psutil.cpu_count(logical=True),
                    "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
                },
                "environment": {
                    "openvino_device": self.openvino.inference_device,
                    "mkl_threads": self.intel_optimization.mkl_num_threads,
                    "omp_threads": self.intel_optimization.omp_num_threads,
                    "model_cache_dir": self.openvino.model_cache_dir
                }
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}

# Global environment manager instance
env_manager: Optional[EnvironmentManager] = None

def get_env_manager() -> EnvironmentManager:
    """Get the global environment manager instance."""
    global env_manager
    if env_manager is None:
        env_manager = EnvironmentManager()
    return env_manager

def initialize_environment() -> EnvironmentManager:
    """Initialize the global environment manager."""
    global env_manager
    env_manager = EnvironmentManager()
    return env_manager