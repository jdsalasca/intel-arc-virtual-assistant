"""
Model Service Implementation for Intel Virtual Assistant Backend
Handles AI model lifecycle management and text generation.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..interfaces.services import IModelService
from ..interfaces.providers import IModelProvider
from ..interfaces.repositories import IModelRepository
from ..models.domain import ModelInfo, ModelType, HardwareType

logger = logging.getLogger(__name__)


class ModelService(IModelService):
    """Service for managing AI models with Intel optimization."""

    def __init__(
        self,
        model_provider: IModelProvider,
        model_repository: IModelRepository
    ):
        """Initialize model service with dependencies."""
        self._model_provider = model_provider
        self._model_repository = model_repository
        self._loaded_models: Dict[str, ModelInfo] = {}
        self._lock = asyncio.Lock()

    async def load_model(self, model_id: str, device: Optional[str] = None) -> bool:
        """Load an AI model."""
        async with self._lock:
            try:
                logger.info(f"Loading model {model_id} on device {device}")
                
                # Check if model is already loaded
                if model_id in self._loaded_models:
                    logger.info(f"Model {model_id} is already loaded")
                    return True

                # Get model info from repository
                model_info = await self._model_repository.get_model_info(model_id)
                if not model_info:
                    logger.error(f"Model {model_id} not found in repository")
                    return False

                # Load model using provider
                success = await self._model_provider.load_model(model_id, device)
                if not success:
                    logger.error(f"Failed to load model {model_id}")
                    return False

                # Update model info
                model_info.loaded = True
                model_info.device = HardwareType(device) if device else HardwareType.AUTO
                
                # Store in memory and update repository
                self._loaded_models[model_id] = model_info
                await self._model_repository.update_model_info(model_info)

                logger.info(f"Successfully loaded model {model_id}")
                return True

            except Exception as e:
                logger.error(f"Error loading model {model_id}: {str(e)}")
                return False

    async def unload_model(self, model_id: str) -> bool:
        """Unload an AI model."""
        async with self._lock:
            try:
                logger.info(f"Unloading model {model_id}")
                
                if model_id not in self._loaded_models:
                    logger.warning(f"Model {model_id} is not loaded")
                    return True

                # Unload from provider
                success = await self._model_provider.unload_model(model_id)
                if not success:
                    logger.error(f"Failed to unload model {model_id}")
                    return False

                # Update model info
                model_info = self._loaded_models[model_id]
                model_info.loaded = False
                model_info.device = None

                # Remove from memory and update repository
                del self._loaded_models[model_id]
                await self._model_repository.update_model_info(model_info)

                logger.info(f"Successfully unloaded model {model_id}")
                return True

            except Exception as e:
                logger.error(f"Error unloading model {model_id}: {str(e)}")
                return False

    async def get_loaded_models(self) -> List[ModelInfo]:
        """Get information about loaded models."""
        try:
            return list(self._loaded_models.values())
        except Exception as e:
            logger.error(f"Error getting loaded models: {str(e)}")
            return []

    async def get_available_models(self) -> List[ModelInfo]:
        """Get information about available models."""
        try:
            return await self._model_repository.get_all_models()
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return []

    async def generate_text(
        self, 
        prompt: str, 
        model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using a loaded model."""
        try:
            # Determine which model to use
            if model_id and model_id not in self._loaded_models:
                raise ValueError(f"Model {model_id} is not loaded")
            
            if not model_id:
                # Use the first available LLM model
                llm_models = [m for m in self._loaded_models.values() 
                             if m.type == ModelType.LLM]
                if not llm_models:
                    raise ValueError("No LLM models are loaded")
                model_id = llm_models[0].id

            logger.debug(f"Generating text with model {model_id}")
            
            # Generate text using provider
            result = await self._model_provider.generate(
                prompt=prompt,
                model_id=model_id,
                **kwargs
            )

            return result

        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    async def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """Get detailed status of a specific model."""
        try:
            if model_id not in self._loaded_models:
                return {"loaded": False, "status": "not_loaded"}

            model_info = self._loaded_models[model_id]
            status = await self._model_provider.get_model_status(model_id)
            
            return {
                "loaded": True,
                "model_info": model_info.to_dict(),
                "provider_status": status
            }

        except Exception as e:
            logger.error(f"Error getting model status for {model_id}: {str(e)}")
            return {"loaded": False, "status": "error", "error": str(e)}

    async def optimize_model(
        self, 
        model_id: str, 
        optimization_level: str = "balanced"
    ) -> bool:
        """Optimize a model for better performance."""
        try:
            logger.info(f"Optimizing model {model_id} with level {optimization_level}")
            
            if model_id not in self._loaded_models:
                raise ValueError(f"Model {model_id} is not loaded")

            # Apply optimization using provider
            success = await self._model_provider.optimize_model(
                model_id, optimization_level
            )

            if success:
                logger.info(f"Successfully optimized model {model_id}")
            else:
                logger.error(f"Failed to optimize model {model_id}")

            return success

        except Exception as e:
            logger.error(f"Error optimizing model {model_id}: {str(e)}")
            return False

    async def validate_model(self, model_id: str) -> Dict[str, Any]:
        """Validate model integrity and performance."""
        try:
            logger.info(f"Validating model {model_id}")
            
            if model_id not in self._loaded_models:
                return {"valid": False, "error": "Model not loaded"}

            # Run validation using provider
            validation_result = await self._model_provider.validate_model(model_id)
            
            return {
                "valid": validation_result.get("valid", False),
                "performance_metrics": validation_result.get("metrics", {}),
                "issues": validation_result.get("issues", []),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error validating model {model_id}: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_model_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics for loaded models."""
        try:
            usage = {}
            total_memory = 0
            
            for model_id, model_info in self._loaded_models.items():
                model_usage = await self._model_provider.get_memory_usage(model_id)
                usage[model_id] = {
                    "model_size": model_info.size,
                    "runtime_memory": model_usage.get("runtime_memory", 0),
                    "device": model_info.device.value if model_info.device else "unknown"
                }
                total_memory += model_usage.get("runtime_memory", 0)

            return {
                "models": usage,
                "total_memory": total_memory,
                "loaded_count": len(self._loaded_models)
            }

        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            return {"models": {}, "total_memory": 0, "loaded_count": 0}

    async def warmup_model(self, model_id: str) -> bool:
        """Warm up a model with a test inference."""
        try:
            logger.info(f"Warming up model {model_id}")
            
            if model_id not in self._loaded_models:
                raise ValueError(f"Model {model_id} is not loaded")

            # Run a small test inference
            test_prompt = "Hello"
            result = await self.generate_text(
                prompt=test_prompt,
                model_id=model_id,
                max_tokens=5,
                temperature=0.1
            )

            logger.info(f"Model {model_id} warmed up successfully")
            return bool(result)

        except Exception as e:
            logger.error(f"Error warming up model {model_id}: {str(e)}")
            return False