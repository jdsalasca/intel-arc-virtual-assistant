"""
Health and Configuration API Routes
Provides system health, hardware info, and configuration management.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from config import get_settings, get_env_manager, ApplicationSettings, EnvironmentManager

router = APIRouter()

# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    hardware: Dict[str, Any]
    configuration: Dict[str, Any]

class HardwareResponse(BaseModel):
    cpu: Dict[str, Any]
    gpu: Dict[str, Any]
    npu: Dict[str, Any]
    memory: Dict[str, Any]
    system: Dict[str, Any]

class ConfigurationResponse(BaseModel):
    current_profile: Optional[str]
    available_profiles: List[str]
    model_settings: Dict[str, Any]
    voice_settings: Dict[str, Any]
    performance_settings: Dict[str, Any]

class ProfileUpdateRequest(BaseModel):
    profile_name: str

class SettingUpdateRequest(BaseModel):
    category: str
    key: str
    value: Any

# Dependencies
async def get_application_settings() -> ApplicationSettings:
    return get_settings()

async def get_environment_manager() -> EnvironmentManager:
    return get_env_manager()

# Health endpoints
@router.get("/status", response_model=HealthResponse)
async def get_health_status(
    settings: ApplicationSettings = Depends(get_application_settings),
    env_manager: EnvironmentManager = Depends(get_environment_manager)
):
    """Get overall system health status."""
    import datetime
    
    try:
        # Get system information
        system_info = env_manager.get_system_info()
        
        # Get hardware information (from intel optimizer would be better)
        hardware_info = {
            "cpu": {
                "available": True,
                "cores": system_info.get("hardware", {}).get("cpu_count", 0),
                "threads": system_info.get("hardware", {}).get("cpu_count_logical", 0)
            },
            "memory": {
                "total_gb": system_info.get("hardware", {}).get("memory_total_gb", 0),
                "available_gb": system_info.get("hardware", {}).get("memory_available_gb", 0)
            },
            "gpu": {"available": False},  # Would be detected via intel optimizer
            "npu": {"available": False}   # Would be detected via intel optimizer
        }
        
        # Configuration status
        config_info = {
            "current_profile": settings.current_intel_profile,
            "model": settings.model.name,
            "voice_enabled": settings.voice.tts_enabled and settings.voice.stt_enabled,
            "tools_enabled": len(settings.tools.enabled_tools) > 0
        }
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.datetime.now().isoformat(),
            version=settings.app_version,
            hardware=hardware_info,
            configuration=config_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/hardware", response_model=HardwareResponse)
async def get_hardware_info(
    env_manager: EnvironmentManager = Depends(get_environment_manager)
):
    """Get detailed hardware information."""
    try:
        system_info = env_manager.get_system_info()
        
        # Extract hardware details
        hardware_data = system_info.get("hardware", {})
        platform_data = system_info.get("platform", {})
        env_data = system_info.get("environment", {})
        
        return HardwareResponse(
            cpu={
                "cores": hardware_data.get("cpu_count", 0),
                "threads": hardware_data.get("cpu_count_logical", 0),
                "architecture": platform_data.get("architecture", ["unknown"])[0],
                "processor": platform_data.get("processor", "unknown")
            },
            gpu={
                "available": False,  # Would be detected via Intel libs
                "type": "unknown",
                "memory_mb": 0,
                "device": env_data.get("openvino_device", "CPU")
            },
            npu={
                "available": False,  # Would be detected via Intel libs
                "type": "unknown",
                "compute_units": 0
            },
            memory={
                "total_gb": hardware_data.get("memory_total_gb", 0),
                "available_gb": hardware_data.get("memory_available_gb", 0),
                "usage_percent": round((1 - hardware_data.get("memory_available_gb", 0) / 
                                     max(hardware_data.get("memory_total_gb", 1), 1)) * 100, 1)
            },
            system={
                "platform": platform_data.get("platform", "unknown"),
                "python_version": platform_data.get("python_version", "unknown"),
                "openvino_device": env_data.get("openvino_device", "CPU"),
                "mkl_threads": env_data.get("mkl_threads", 0)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hardware info failed: {str(e)}")

# Configuration endpoints
@router.get("/configuration", response_model=ConfigurationResponse)
async def get_configuration(
    settings: ApplicationSettings = Depends(get_application_settings)
):
    """Get current configuration settings."""
    try:
        return ConfigurationResponse(
            current_profile=settings.current_intel_profile,
            available_profiles=settings.list_available_intel_profiles(),
            model_settings={
                "name": settings.model.name,
                "device": settings.model.device,
                "precision": settings.model.precision,
                "max_tokens": settings.model.max_tokens,
                "temperature": settings.model.temperature,
                "batch_size": settings.model.batch_size
            },
            voice_settings={
                "tts_enabled": settings.voice.tts_enabled,
                "tts_model": settings.voice.tts_model,
                "tts_device": settings.voice.tts_device,
                "stt_enabled": settings.voice.stt_enabled,
                "stt_model": settings.voice.stt_model,
                "stt_device": settings.voice.stt_device
            },
            performance_settings={
                "intel_optimizations": settings.performance.enable_intel_optimizations,
                "openvino_optimizations": settings.performance.enable_openvino_optimizations,
                "memory_pool_mb": settings.performance.memory_pool_size_mb,
                "cache_size_mb": settings.performance.cache_size_mb
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration retrieval failed: {str(e)}")

@router.get("/profiles")
async def list_intel_profiles(
    settings: ApplicationSettings = Depends(get_application_settings)
):
    """List available Intel hardware profiles."""
    try:
        profiles = []
        for profile_name in settings.list_available_intel_profiles():
            profile_info = settings.get_intel_profile_info()
            if profile_info:
                profiles.append({
                    "name": profile_name,
                    "description": profile_info.get("description", ""),
                    "processor": profile_info.get("processor", ""),
                    "gpu": profile_info.get("gpu", ""),
                    "npu": profile_info.get("npu", ""),
                    "current": profile_name == settings.current_intel_profile
                })
        
        return {"profiles": profiles}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile listing failed: {str(e)}")

@router.get("/profiles/{profile_name}")
async def get_profile_details(
    profile_name: str,
    settings: ApplicationSettings = Depends(get_application_settings)
):
    """Get detailed information about a specific Intel profile."""
    try:
        profile_info = settings.intel_profile_manager.get_profile_details(profile_name)
        
        if not profile_info:
            raise HTTPException(status_code=404, detail=f"Profile not found: {profile_name}")
        
        return profile_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile details failed: {str(e)}")

@router.post("/profiles/{profile_name}/apply")
async def apply_intel_profile(
    profile_name: str,
    settings: ApplicationSettings = Depends(get_application_settings)
):
    """Apply an Intel hardware profile."""
    try:
        success = settings.apply_intel_profile(profile_name)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to apply profile: {profile_name}")
        
        # Save configuration
        settings.save_config()
        
        return {
            "success": True,
            "message": f"Successfully applied profile: {profile_name}",
            "current_profile": settings.current_intel_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile application failed: {str(e)}")

@router.put("/settings")
async def update_setting(
    request: SettingUpdateRequest,
    settings: ApplicationSettings = Depends(get_application_settings)
):
    """Update a specific configuration setting."""
    try:
        success = settings.update_setting(request.category, request.key, request.value)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to update setting: {request.category}.{request.key}"
            )
        
        # Save configuration
        settings.save_config()
        
        return {
            "success": True,
            "message": f"Setting updated: {request.category}.{request.key}",
            "value": request.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setting update failed: {str(e)}")

@router.get("/settings/{category}/{key}")
async def get_setting(
    category: str,
    key: str,
    settings: ApplicationSettings = Depends(get_application_settings)
):
    """Get a specific configuration setting."""
    try:
        value = settings.get_setting(category, key)
        
        if value is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Setting not found: {category}.{key}"
            )
        
        return {
            "category": category,
            "key": key,
            "value": value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setting retrieval failed: {str(e)}")

@router.post("/validate")
async def validate_configuration(
    settings: ApplicationSettings = Depends(get_application_settings),
    env_manager: EnvironmentManager = Depends(get_environment_manager)
):
    """Validate current configuration."""
    try:
        # Validate settings
        settings_issues = settings.validate_settings()
        
        # Validate environment
        env_validation = env_manager.validate_environment()
        
        return {
            "valid": len(settings_issues) == 0 and env_validation["valid"],
            "settings_issues": settings_issues,
            "environment_issues": env_validation.get("errors", []),
            "warnings": env_validation.get("warnings", []),
            "info": env_validation.get("info", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration validation failed: {str(e)}")

@router.post("/export")
async def export_configuration(
    settings: ApplicationSettings = Depends(get_application_settings),
    env_manager: EnvironmentManager = Depends(get_environment_manager)
):
    """Export current configuration."""
    try:
        # Export settings
        config_dict = settings.to_dict()
        
        # Export environment file
        env_exported = env_manager.export_environment_file(".env.exported")
        
        return {
            "configuration": config_dict,
            "environment_exported": env_exported,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration export failed: {str(e)}")

# Legacy compatibility
@router.get("/")
async def health_root():
    """Legacy root health endpoint."""
    return {"status": "ok", "service": "intel-assistant-health"}