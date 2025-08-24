"""
Model Manager for loading and managing AI models.
Handles model lifecycle, inference routing, and performance optimization.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, AsyncIterator
from datetime import datetime
import time
from pathlib import Path

from core.interfaces.model_provider import (
    IModelProvider, ITextGenerator, IChatModel, DeviceType, ModelType
)
from core.models.conversation import Message, MessageRole
from core.exceptions import (
    ModelException, ModelLoadException, ModelInferenceException, 
    ModelNotLoadedException
)
from services.intel_optimizer import IntelOptimizer

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages AI models and inference operations."""
    
    def __init__(self, intel_optimizer: IntelOptimizer):
        self.intel_optimizer = intel_optimizer
        
        # Model registry
        self._providers: Dict[str, IModelProvider] = {}
        self._loaded_models: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self._inference_stats: Dict[str, Dict[str, Any]] = {}
        
        # Model configurations
        self._model_configs = {
            "qwen2.5-7b-int4": {
                "path": "Qwen2.5-7B-Instruct-int4-ov",
                "type": ModelType.LLM,
                "provider": "openvino",
                "supports_chat": True,
                "supports_streaming": True,
                "default_max_tokens": 256,
                "default_temperature": 0.7
            },
            "phi-3-mini-int4": {
                "path": "Phi-3-mini-4k-instruct-int4-ov", 
                "type": ModelType.LLM,
                "provider": "openvino",
                "supports_chat": True,
                "supports_streaming": True,
                "default_max_tokens": 256,
                "default_temperature": 0.7
            },
            "tinyllama-1.1b-int4": {
                "path": "TinyLlama-1.1B-Chat-v1.0-int4-ov",
                "type": ModelType.LLM,
                "provider": "openvino",
                "supports_chat": True,
                "supports_streaming": False,
                "default_max_tokens": 128,
                "default_temperature": 0.8
            },
            "whisper-base": {
                "path": "whisper-base",
                "type": ModelType.STT,
                "provider": "whisper",
                "supports_streaming": True
            },
            "speecht5-tts": {
                "path": "microsoft/speecht5_tts",
                "type": ModelType.TTS,
                "provider": "speecht5",
                "supports_streaming": False
            }
        }
    
    def register_provider(self, name: str, provider: IModelProvider) -> None:
        """Register a model provider."""
        self._providers[name] = provider
        logger.info(f"Registered model provider: {name}")
    
    async def load_model(
        self, 
        model_name: str, 
        device: Optional[str] = None,
        force_reload: bool = False
    ) -> bool:
        """Load a model for inference."""
        try:
            # Check if model is already loaded
            if model_name in self._loaded_models and not force_reload:
                logger.info(f"Model {model_name} already loaded")
                return True
            
            # Get model configuration
            config = self._model_configs.get(model_name)
            if not config:
                raise ModelLoadException(f"Unknown model: {model_name}")
            
            # Determine optimal device
            if not device:
                device = self.intel_optimizer.select_optimal_device(model_name, config["type"])
            
            # Get provider
            provider_name = config["provider"]
            provider = self._providers.get(provider_name)
            if not provider:
                raise ModelLoadException(f"Provider {provider_name} not available")
            
            # Get Intel optimization config
            intel_config = self.intel_optimizer.get_model_config(model_name, device)
            
            # Load the model
            model_path = Path(config["path"])
            if not model_path.is_absolute():
                model_path = Path.cwd() / model_path
            
            load_start = time.time()
            success = provider.load_model(
                model_path=str(model_path),
                device=DeviceType(device),
                **intel_config
            )
            load_time = time.time() - load_start
            
            if success:
                # Track loaded model
                self._loaded_models[model_name] = {
                    "config": config,
                    "device": device,
                    "provider": provider,
                    "loaded_at": datetime.utcnow(),
                    "load_time": load_time,
                    "intel_config": intel_config
                }
                
                # Initialize stats tracking
                self._inference_stats[model_name] = {
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_time": 0.0,
                    "average_latency": 0.0,
                    "last_used": datetime.utcnow()
                }
                
                logger.info(f"Loaded model {model_name} on {device} in {load_time:.2f}s")
                return True
            else:
                raise ModelLoadException(f"Failed to load model {model_name}")
                
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise ModelLoadException(f"Failed to load model {model_name}: {e}")
    
    async def unload_model(self, model_name: str) -> bool:
        """Unload a model."""
        try:
            if model_name not in self._loaded_models:
                logger.warning(f"Model {model_name} not loaded")
                return True
            
            model_info = self._loaded_models[model_name]
            provider = model_info["provider"]
            
            success = provider.unload_model()
            if success:
                del self._loaded_models[model_name]
                logger.info(f"Unloaded model {model_name}")
                return True
            else:
                logger.error(f"Failed to unload model {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error unloading model {model_name}: {e}")
            return False
    
    async def generate_text(
        self,
        model_name: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        stream: bool = False
    ) -> Union[str, AsyncIterator[str]]:
        """Generate text using a model."""
        try:
            # Ensure model is loaded
            if model_name not in self._loaded_models:
                await self.load_model(model_name)
            
            model_info = self._loaded_models[model_name]
            provider = model_info["provider"]
            config = model_info["config"]
            
            # Check if provider supports text generation
            if not isinstance(provider, ITextGenerator):
                raise ModelInferenceException(f"Model {model_name} does not support text generation")
            
            # Use defaults from config if not specified
            max_tokens = max_tokens or config.get("default_max_tokens", 256)
            temperature = temperature or config.get("default_temperature", 0.7)
            
            # Get Intel optimization parameters
            intel_params = self.intel_optimizer.optimize_inference_params(
                model_name, model_info["device"], max_tokens
            )
            
            # Start timing
            start_time = time.time()
            
            # Generate text
            if stream and config.get("supports_streaming", False):
                result = provider.generate_stream(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop_sequences=stop_sequences,
                    **intel_params
                )
            else:
                result = provider.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop_sequences=stop_sequences,
                    **intel_params
                )
            
            # Update statistics (for non-streaming)
            if not stream:
                self._update_stats(model_name, start_time, max_tokens)
            
            return result
            
        except Exception as e:
            logger.error(f"Text generation failed for model {model_name}: {e}")
            raise ModelInferenceException(f"Text generation failed: {e}")
    
    async def chat_completion(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> Union[str, AsyncIterator[str]]:
        """Generate chat completion using a model."""
        try:
            # Ensure model is loaded
            if model_name not in self._loaded_models:
                await self.load_model(model_name)
            
            model_info = self._loaded_models[model_name]
            provider = model_info["provider"]
            config = model_info["config"]
            
            # Check if provider supports chat
            if not isinstance(provider, IChatModel):
                # Fallback to text generation with formatted prompt
                return await self._chat_as_text_generation(
                    model_name, messages, max_tokens, temperature, stream
                )
            
            # Use defaults from config if not specified
            max_tokens = max_tokens or config.get("default_max_tokens", 256)
            temperature = temperature or config.get("default_temperature", 0.7)
            
            # Get Intel optimization parameters
            intel_params = self.intel_optimizer.optimize_inference_params(
                model_name, model_info["device"], max_tokens
            )
            
            # Start timing
            start_time = time.time()
            
            # Generate chat response
            if stream and config.get("supports_streaming", False):
                result = provider.chat_stream(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **intel_params
                )
            else:
                result = provider.chat(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **intel_params
                )
            
            # Update statistics (for non-streaming)
            if not stream:
                self._update_stats(model_name, start_time, max_tokens)
            
            return result
            
        except Exception as e:
            logger.error(f"Chat completion failed for model {model_name}: {e}")
            raise ModelInferenceException(f"Chat completion failed: {e}")
    
    async def _chat_as_text_generation(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        temperature: Optional[float],
        stream: bool
    ) -> Union[str, AsyncIterator[str]]:
        """Fallback to text generation for chat."""
        # Format messages as a prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt = "\n".join(prompt_parts) + "\nAssistant:"
        
        return await self.generate_text(
            model_name=model_name,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream
        )
    
    def _update_stats(self, model_name: str, start_time: float, tokens: int) -> None:
        """Update inference statistics."""
        try:
            if model_name in self._inference_stats:
                stats = self._inference_stats[model_name]
                elapsed = time.time() - start_time
                
                stats["total_requests"] += 1
                stats["total_tokens"] += tokens
                stats["total_time"] += elapsed
                stats["average_latency"] = stats["total_time"] / stats["total_requests"]
                stats["last_used"] = datetime.utcnow()
                
        except Exception as e:
            logger.debug(f"Failed to update stats for {model_name}: {e}")
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models."""
        return list(self._loaded_models.keys())
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return list(self._model_configs.keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a model."""
        if model_name in self._loaded_models:
            model_info = self._loaded_models[model_name].copy()
            model_info["stats"] = self._inference_stats.get(model_name, {})
            return model_info
        elif model_name in self._model_configs:
            return self._model_configs[model_name]
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all models."""
        return {
            "loaded_models": len(self._loaded_models),
            "total_models": len(self._model_configs),
            "model_stats": self._inference_stats.copy(),
            "hardware_summary": self.intel_optimizer.get_hardware_summary()
        }
    
    async def suggest_model_for_task(self, task_description: str) -> str:
        """Suggest the best model for a given task."""
        try:
            # Simple keyword-based suggestion
            task_lower = task_description.lower()
            
            if any(word in task_lower for word in ["quick", "fast", "simple", "tool"]):
                return "phi-3-mini-int4"
            elif any(word in task_lower for word in ["complex", "detailed", "analysis", "reasoning"]):
                return "qwen2.5-7b-int4"
            elif any(word in task_lower for word in ["lightweight", "basic", "npu"]):
                return "tinyllama-1.1b-int4"
            else:
                return "qwen2.5-7b-int4"  # Default
                
        except Exception as e:
            logger.warning(f"Failed to suggest model: {e}")
            return "qwen2.5-7b-int4"
    
    async def cleanup_unused_models(self, max_idle_minutes: int = 30) -> int:
        """Unload models that haven't been used recently."""
        try:
            unloaded_count = 0
            current_time = datetime.utcnow()
            
            models_to_unload = []
            for model_name, stats in self._inference_stats.items():
                last_used = stats.get("last_used")
                if last_used:
                    idle_time = (current_time - last_used).total_seconds() / 60
                    if idle_time > max_idle_minutes:
                        models_to_unload.append(model_name)
            
            for model_name in models_to_unload:
                if await self.unload_model(model_name):
                    unloaded_count += 1
                    logger.info(f"Unloaded idle model: {model_name}")
            
            return unloaded_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup unused models: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on model manager."""
        try:
            health = {
                "status": "healthy",
                "loaded_models": len(self._loaded_models),
                "available_models": len(self._model_configs),
                "providers": list(self._providers.keys()),
                "hardware": self.intel_optimizer.get_hardware_summary(),
                "errors": []
            }
            
            # Test each loaded model
            for model_name in self._loaded_models:
                try:
                    model_info = self._loaded_models[model_name]
                    provider = model_info["provider"]
                    if not provider.is_loaded():
                        health["errors"].append(f"Model {model_name} appears unloaded")
                except Exception as e:
                    health["errors"].append(f"Model {model_name} health check failed: {e}")
            
            if health["errors"]:
                health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }