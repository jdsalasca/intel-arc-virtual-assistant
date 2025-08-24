"""
Models Controller for Intel Virtual Assistant Backend
FastAPI endpoints for AI model management and text generation.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from ..interfaces.services import IModelService
from ..models.dto import LoadModelRequest, GenerateTextRequest
from ..models.domain import ModelInfo

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/models", tags=["models"])


def get_model_service() -> IModelService:
    """Dependency injection for model service."""
    # This will be replaced by proper DI container
    from ..services import ModelService
    # For now, return a placeholder - this will be implemented in DI container
    raise NotImplementedError("DI container not yet implemented")


@router.get("/", response_model=List[ModelInfo])
async def get_available_models(
    model_service: IModelService = Depends(get_model_service)
) -> List[ModelInfo]:
    """Get list of available AI models."""
    try:
        logger.debug("Getting available models")
        
        models = await model_service.get_available_models()
        return models
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/loaded", response_model=List[ModelInfo])
async def get_loaded_models(
    model_service: IModelService = Depends(get_model_service)
) -> List[ModelInfo]:
    """Get list of currently loaded models."""
    try:
        logger.debug("Getting loaded models")
        
        models = await model_service.get_loaded_models()
        return models
        
    except Exception as e:
        logger.error(f"Error getting loaded models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/load")
async def load_model(
    request: LoadModelRequest,
    background_tasks: BackgroundTasks,
    model_service: IModelService = Depends(get_model_service)
):
    """Load an AI model."""
    try:
        logger.info(f"Loading model: {request.model_id}")
        
        if not request.model_id.strip():
            raise HTTPException(status_code=400, detail="Model ID cannot be empty")
        
        # Load model in background
        async def load_model_task():
            try:
                success = await model_service.load_model(
                    request.model_id, 
                    request.device
                )
                if success:
                    logger.info(f"Model {request.model_id} loaded successfully")
                else:
                    logger.error(f"Failed to load model {request.model_id}")
            except Exception as e:
                logger.error(f"Error in background model loading: {e}")
        
        background_tasks.add_task(load_model_task)
        
        return {
            "message": f"Model {request.model_id} loading started",
            "model_id": request.model_id,
            "device": request.device,
            "status": "loading"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading model {request.model_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/unload/{model_id}")
async def unload_model(
    model_id: str,
    model_service: IModelService = Depends(get_model_service)
):
    """Unload an AI model."""
    try:
        logger.info(f"Unloading model: {model_id}")
        
        if not model_id.strip():
            raise HTTPException(status_code=400, detail="Model ID cannot be empty")
        
        success = await model_service.unload_model(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found or not loaded")
        
        return {
            "message": f"Model {model_id} unloaded successfully",
            "model_id": model_id,
            "status": "unloaded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unloading model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{model_id}/status")
async def get_model_status(
    model_id: str,
    model_service: IModelService = Depends(get_model_service)
) -> Dict[str, Any]:
    """Get status of a specific model."""
    try:
        logger.debug(f"Getting status for model: {model_id}")
        
        if not model_id.strip():
            raise HTTPException(status_code=400, detail="Model ID cannot be empty")
        
        status = await model_service.get_model_status(model_id)
        return status
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate")
async def generate_text(
    request: GenerateTextRequest,
    model_service: IModelService = Depends(get_model_service)
) -> Dict[str, Any]:
    """Generate text using a loaded model."""
    try:
        logger.debug(f"Generating text with model: {request.model_id}")
        
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        if request.max_tokens <= 0 or request.max_tokens > 2048:
            raise HTTPException(status_code=400, detail="max_tokens must be between 1 and 2048")
        
        if not (0.0 <= request.temperature <= 2.0):
            raise HTTPException(status_code=400, detail="temperature must be between 0.0 and 2.0")
        
        if not (0.0 <= request.top_p <= 1.0):
            raise HTTPException(status_code=400, detail="top_p must be between 0.0 and 1.0")
        
        # Generate text
        generated_text = await model_service.generate_text(
            prompt=request.prompt,
            model_id=request.model_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        return {
            "prompt": request.prompt,
            "generated_text": generated_text,
            "model_id": request.model_id,
            "parameters": {
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid generation request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{model_id}/optimize")
async def optimize_model(
    model_id: str,
    optimization_level: str = "balanced",
    model_service: IModelService = Depends(get_model_service)
):
    """Optimize a loaded model for better performance."""
    try:
        logger.info(f"Optimizing model {model_id} with level {optimization_level}")
        
        if not model_id.strip():
            raise HTTPException(status_code=400, detail="Model ID cannot be empty")
        
        valid_levels = ["speed", "memory", "balanced"]
        if optimization_level not in valid_levels:
            raise HTTPException(
                status_code=400, 
                detail=f"optimization_level must be one of: {valid_levels}"
            )
        
        success = await model_service.optimize_model(model_id, optimization_level)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found or optimization failed")
        
        return {
            "message": f"Model {model_id} optimized successfully",
            "model_id": model_id,
            "optimization_level": optimization_level,
            "status": "optimized"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{model_id}/validate")
async def validate_model(
    model_id: str,
    model_service: IModelService = Depends(get_model_service)
) -> Dict[str, Any]:
    """Validate model integrity and performance."""
    try:
        logger.info(f"Validating model: {model_id}")
        
        if not model_id.strip():
            raise HTTPException(status_code=400, detail="Model ID cannot be empty")
        
        validation_result = await model_service.validate_model(model_id)
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/memory/usage")
async def get_memory_usage(
    model_service: IModelService = Depends(get_model_service)
) -> Dict[str, Any]:
    """Get memory usage statistics for loaded models."""
    try:
        logger.debug("Getting model memory usage")
        
        usage_stats = await model_service.get_model_memory_usage()
        return usage_stats
        
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{model_id}/warmup")
async def warmup_model(
    model_id: str,
    model_service: IModelService = Depends(get_model_service)
):
    """Warm up a model with a test inference."""
    try:
        logger.info(f"Warming up model: {model_id}")
        
        if not model_id.strip():
            raise HTTPException(status_code=400, detail="Model ID cannot be empty")
        
        success = await model_service.warmup_model(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found or warmup failed")
        
        return {
            "message": f"Model {model_id} warmed up successfully",
            "model_id": model_id,
            "status": "ready"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error warming up model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/benchmarks")
async def get_model_benchmarks(
    model_service: IModelService = Depends(get_model_service)
) -> Dict[str, Any]:
    """Get performance benchmarks for loaded models."""
    try:
        logger.debug("Getting model benchmarks")
        
        # This would run benchmarks on all loaded models
        loaded_models = await model_service.get_loaded_models()
        benchmarks = {}
        
        for model in loaded_models:
            try:
                validation_result = await model_service.validate_model(model.id)
                benchmarks[model.id] = {
                    "model_name": model.name,
                    "device": model.device.value if model.device else "unknown",
                    "metrics": validation_result.get("metrics", {}),
                    "valid": validation_result.get("valid", False)
                }
            except Exception as e:
                logger.warning(f"Error benchmarking model {model.id}: {e}")
                benchmarks[model.id] = {"error": str(e)}
        
        return {
            "benchmarks": benchmarks,
            "total_models": len(loaded_models)
        }
        
    except Exception as e:
        logger.error(f"Error getting model benchmarks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/supported")
async def get_supported_models() -> Dict[str, Any]:
    """Get list of supported model architectures and formats."""
    try:
        # This would return information about supported models
        supported_models = {
            "architectures": [
                "mistralai/Mistral-7B-Instruct-v0.3",
                "microsoft/DialoGPT-medium",
                "microsoft/DialoGPT-large",
                "huggingface/CodeBERTa-small-v1"
            ],
            "formats": [
                "transformers",
                "openvino_ir",
                "onnx"
            ],
            "optimizations": [
                "int8_quantization", 
                "int4_quantization",
                "intel_neural_compressor",
                "openvino_optimization"
            ],
            "devices": [
                "CPU",
                "GPU", 
                "NPU",
                "AUTO"
            ]
        }
        
        return supported_models
        
    except Exception as e:
        logger.error(f"Error getting supported models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")