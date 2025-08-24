"""
Health Controller for Intel Virtual Assistant Backend
FastAPI endpoints for system health monitoring and diagnostics.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends

from ..interfaces.services import IHealthService, IHardwareService
from ..models.dto import BenchmarkRequest, SystemStatusResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/health", tags=["health"])


from ..config.container import get_health_service, get_hardware_service


# Dependency injection functions are imported from container


@router.get("/status")
async def get_system_status(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Get overall system health status."""
    try:
        logger.debug("Getting system status")
        
        status = await health_service.get_system_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/")
async def health_check():
    """Simple health check endpoint."""
    try:
        return {
            "status": "healthy",
            "message": "System is running",
            "timestamp": "2024-08-24T17:18:00Z"  # This would be current time
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/services/{service_name}")
async def check_service_health(
    service_name: str,
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Check health of a specific service."""
    try:
        logger.debug(f"Checking health of service: {service_name}")
        
        valid_services = ["model", "voice", "hardware", "chat", "tools"]
        if service_name not in valid_services:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid service name. Valid services: {valid_services}"
            )
        
        service_health = await health_service.check_service_health(service_name)
        return service_health
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking service health for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics/performance")
async def get_performance_metrics(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Get detailed performance metrics."""
    try:
        logger.debug("Getting performance metrics")
        
        metrics = await health_service.get_performance_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/hardware")
async def get_hardware_info(
    hardware_service: IHardwareService = Depends(get_hardware_service)
) -> Dict[str, Any]:
    """Get hardware information."""
    try:
        logger.debug("Getting hardware information")
        
        hardware_info = await hardware_service.get_hardware_info()
        return hardware_info.to_dict()
        
    except Exception as e:
        logger.error(f"Error getting hardware info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/diagnostics")
async def run_diagnostics(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Run comprehensive system diagnostics."""
    try:
        logger.info("Running system diagnostics")
        
        diagnostics = await health_service.run_diagnostics()
        return diagnostics
        
    except Exception as e:
        logger.error(f"Error running diagnostics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alerts")
async def get_system_alerts(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Get current system alerts."""
    try:
        logger.debug("Getting system alerts")
        
        alerts = await health_service.get_alerts()
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "timestamp": "2024-08-24T17:18:00Z"  # This would be current time
        }
        
    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/benchmark")
async def run_benchmark(
    request: BenchmarkRequest,
    hardware_service: IHardwareService = Depends(get_hardware_service)
) -> Dict[str, Any]:
    """Run hardware benchmark."""
    try:
        logger.info(f"Running benchmark for device: {request.device_type}")
        
        valid_devices = ["cpu", "gpu", "npu"]
        if request.device_type.lower() not in valid_devices:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid device type. Valid devices: {valid_devices}"
            )
        
        if not (10 <= request.duration <= 300):
            raise HTTPException(
                status_code=400,
                detail="Duration must be between 10 and 300 seconds"
            )
        
        benchmark_result = await hardware_service.benchmark_device(request.device_type)
        
        return {
            "device_type": request.device_type,
            "test_type": request.test_type,
            "duration": request.duration,
            "results": benchmark_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/optimization/{device_type}")
async def get_optimization_config(
    device_type: str,
    hardware_service: IHardwareService = Depends(get_hardware_service)
) -> Dict[str, Any]:
    """Get optimization configuration for a device."""
    try:
        logger.debug(f"Getting optimization config for: {device_type}")
        
        valid_devices = ["cpu", "gpu", "npu"]
        if device_type.lower() not in valid_devices:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid device type. Valid devices: {valid_devices}"
            )
        
        config = await hardware_service.optimize_for_device(device_type, "default")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/devices/optimal")
async def get_optimal_device(
    task_type: str,
    hardware_service: IHardwareService = Depends(get_hardware_service)
) -> Dict[str, Any]:
    """Get the optimal device for a task type."""
    try:
        logger.debug(f"Getting optimal device for task: {task_type}")
        
        valid_tasks = ["inference", "training", "voice_synthesis", "general"]
        if task_type not in valid_tasks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task type. Valid tasks: {valid_tasks}"
            )
        
        optimal_device = await hardware_service.get_optimal_device(task_type)
        
        return {
            "task_type": task_type,
            "optimal_device": optimal_device,
            "recommendation": f"Use {optimal_device} for {task_type} tasks"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimal device: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/uptime")
async def get_system_uptime(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Get system uptime and basic info."""
    try:
        logger.debug("Getting system uptime")
        
        # Get basic status that includes uptime
        status = await health_service.get_system_status()
        
        return {
            "uptime_seconds": status.get("uptime", 0),
            "status": status.get("status", "unknown"),
            "timestamp": status.get("timestamp"),
            "health_score": status.get("health_score", 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting system uptime: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/memory")
async def get_memory_info(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Get detailed memory information."""
    try:
        logger.debug("Getting memory information")
        
        metrics = await health_service.get_performance_metrics()
        memory_info = metrics.get("memory", {})
        process_info = metrics.get("process", {})
        
        return {
            "system_memory": memory_info,
            "process_memory": process_info,
            "swap_usage": {
                "total_gb": memory_info.get("swap_total_gb", 0),
                "used_gb": memory_info.get("swap_used_gb", 0),
                "percent": memory_info.get("swap_percent", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting memory info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cpu")
async def get_cpu_info(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Get detailed CPU information."""
    try:
        logger.debug("Getting CPU information")
        
        metrics = await health_service.get_performance_metrics()
        cpu_info = metrics.get("cpu", {})
        
        # Get additional system info
        status = await health_service.get_system_status()
        system_info = status.get("system", {})
        
        return {
            "usage": cpu_info,
            "system_info": {
                "processor": system_info.get("processor", "unknown"),
                "platform": system_info.get("platform", "unknown"),
                "machine": system_info.get("machine", "unknown")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting CPU info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/network")
async def get_network_info(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Get network information."""
    try:
        logger.debug("Getting network information")
        
        metrics = await health_service.get_performance_metrics()
        network_info = metrics.get("network", {})
        
        return {
            "network_io": network_info,
            "status": "active" if network_info else "unknown"
        }
        
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/disk")
async def get_disk_info(
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Get disk usage information."""
    try:
        logger.debug("Getting disk information")
        
        metrics = await health_service.get_performance_metrics()
        disk_info = metrics.get("disk", {})
        
        return {
            "disk_usage": disk_info,
            "warnings": [
                "High disk usage" 
                if disk_info.get("usage_percent", 0) > 90 
                else None
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting disk info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stress-test")
async def run_stress_test(
    duration: int = 30,
    intensity: str = "medium",
    health_service: IHealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Run a system stress test."""
    try:
        logger.info(f"Running stress test: duration={duration}s, intensity={intensity}")
        
        if not (10 <= duration <= 300):
            raise HTTPException(
                status_code=400,
                detail="Duration must be between 10 and 300 seconds"
            )
        
        valid_intensities = ["low", "medium", "high"]
        if intensity not in valid_intensities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid intensity. Valid intensities: {valid_intensities}"
            )
        
        # This would run actual stress tests
        # For now, return a placeholder
        return {
            "message": "Stress test completed",
            "duration": duration,
            "intensity": intensity,
            "status": "not_implemented",
            "note": "Stress testing functionality not yet implemented"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running stress test: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")