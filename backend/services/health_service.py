"""
Health Service Implementation for Intel Virtual Assistant Backend
Handles system health monitoring and status reporting.
"""

import logging
import psutil
import platform
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..interfaces.services import IHealthService
from ..interfaces.services import IModelService, IVoiceService, IHardwareService

logger = logging.getLogger(__name__)


class HealthService(IHealthService):
    """Service for monitoring system health and status."""

    def __init__(
        self,
        model_service: IModelService,
        voice_service: IVoiceService,
        hardware_service: IHardwareService
    ):
        """Initialize health service with dependencies."""
        self._model_service = model_service
        self._voice_service = voice_service
        self._hardware_service = hardware_service
        self._start_time = datetime.now()
        self._health_checks = {}
        self._alert_thresholds = {
            "cpu_usage": 90.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 10.0
        }

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            logger.debug("Getting system status")
            
            # Get basic system info
            system_info = await self._get_system_info()
            
            # Get resource usage
            resource_usage = await self._get_resource_usage()
            
            # Get service statuses
            service_status = await self._get_service_status()
            
            # Get hardware status
            hardware_status = await self._get_hardware_status()
            
            # Calculate overall health
            overall_health = await self._calculate_overall_health(
                resource_usage, service_status
            )

            return {
                "status": overall_health["status"],
                "timestamp": datetime.now().isoformat(),
                "uptime": self._get_uptime_seconds(),
                "system": system_info,
                "resources": resource_usage,
                "services": service_status,
                "hardware": hardware_status,
                "health_score": overall_health["score"],
                "alerts": overall_health["alerts"]
            }

        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        try:
            logger.debug(f"Checking health of service: {service_name}")
            
            if service_name == "model":
                return await self._check_model_service_health()
            elif service_name == "voice":
                return await self._check_voice_service_health()
            elif service_name == "hardware":
                return await self._check_hardware_service_health()
            else:
                return {
                    "service": service_name,
                    "status": "unknown",
                    "error": f"Unknown service: {service_name}"
                }

        except Exception as e:
            logger.error(f"Error checking {service_name} service health: {str(e)}")
            return {
                "service": service_name,
                "status": "error",
                "error": str(e)
            }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "frequency_mhz": cpu_freq.current if cpu_freq else None,
                    "cores": cpu_count,
                    "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "usage_percent": memory.percent,
                    "swap_total_gb": round(swap.total / (1024**3), 2),
                    "swap_used_gb": round(swap.used / (1024**3), 2),
                    "swap_percent": swap.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2),
                    "io_read_mb": round(disk_io.read_bytes / (1024**2), 2) if disk_io else None,
                    "io_write_mb": round(disk_io.write_bytes / (1024**2), 2) if disk_io else None
                },
                "network": {
                    "bytes_sent_mb": round(network.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(network.bytes_recv / (1024**2), 2),
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                    "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                    "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None
                }
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}

    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics."""
        try:
            logger.info("Running system diagnostics")
            
            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "tests": []
            }

            # Test 1: Basic system resources
            resource_test = await self._test_system_resources()
            diagnostics["tests"].append(resource_test)

            # Test 2: Model service functionality
            model_test = await self._test_model_service()
            diagnostics["tests"].append(model_test)

            # Test 3: Voice service functionality
            voice_test = await self._test_voice_service()
            diagnostics["tests"].append(voice_test)

            # Test 4: Hardware detection
            hardware_test = await self._test_hardware_service()
            diagnostics["tests"].append(hardware_test)

            # Test 5: Memory allocation
            memory_test = await self._test_memory_allocation()
            diagnostics["tests"].append(memory_test)

            # Calculate overall result
            passed_tests = sum(1 for test in diagnostics["tests"] if test["passed"])
            total_tests = len(diagnostics["tests"])
            
            diagnostics["summary"] = {
                "passed": passed_tests,
                "total": total_tests,
                "success_rate": round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0,
                "overall_status": "healthy" if passed_tests == total_tests else "issues_detected"
            }

            return diagnostics

        except Exception as e:
            logger.error(f"Error running diagnostics: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "summary": {"overall_status": "error"}
            }

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current system alerts."""
        try:
            alerts = []
            
            # Check resource usage alerts
            resource_usage = await self._get_resource_usage()
            
            if resource_usage["cpu"]["usage_percent"] > self._alert_thresholds["cpu_usage"]:
                alerts.append({
                    "type": "warning",
                    "category": "performance",
                    "message": f"High CPU usage: {resource_usage['cpu']['usage_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })

            if resource_usage["memory"]["usage_percent"] > self._alert_thresholds["memory_usage"]:
                alerts.append({
                    "type": "warning",
                    "category": "performance",
                    "message": f"High memory usage: {resource_usage['memory']['usage_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })

            # Check service alerts
            service_status = await self._get_service_status()
            
            for service_name, status in service_status.items():
                if not status.get("healthy", False):
                    alerts.append({
                        "type": "error",
                        "category": "service",
                        "message": f"Service {service_name} is unhealthy: {status.get('error', 'Unknown error')}",
                        "timestamp": datetime.now().isoformat()
                    })

            return alerts

        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            return []

    # Private helper methods

    async def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }

    async def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "usage_percent": memory.percent
            }
        }

    async def _get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        services = {}
        
        # Check model service
        try:
            models = await self._model_service.get_loaded_models()
            services["model"] = {
                "healthy": True,
                "loaded_models": len(models),
                "status": "operational"
            }
        except Exception as e:
            services["model"] = {
                "healthy": False,
                "error": str(e),
                "status": "error"
            }

        # Check voice service
        try:
            voice_available = await self._voice_service.is_voice_available()
            services["voice"] = {
                "healthy": voice_available,
                "status": "operational" if voice_available else "unavailable"
            }
        except Exception as e:
            services["voice"] = {
                "healthy": False,
                "error": str(e),
                "status": "error"
            }

        return services

    async def _get_hardware_status(self) -> Dict[str, Any]:
        """Get hardware status."""
        try:
            hardware_info = await self._hardware_service.get_hardware_info()
            return {
                "cpu_available": hardware_info.cpu_available,
                "gpu_available": hardware_info.gpu_available,
                "npu_available": hardware_info.npu_available,
                "status": "operational"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _calculate_overall_health(
        self, resource_usage: Dict[str, Any], service_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall system health."""
        score = 100
        alerts = []
        
        # Deduct points for high resource usage
        cpu_usage = resource_usage["cpu"]["usage_percent"]
        memory_usage = resource_usage["memory"]["usage_percent"]
        
        if cpu_usage > 80:
            score -= 20
            alerts.append(f"High CPU usage: {cpu_usage:.1f}%")
        elif cpu_usage > 60:
            score -= 10

        if memory_usage > 80:
            score -= 20
            alerts.append(f"High memory usage: {memory_usage:.1f}%")
        elif memory_usage > 60:
            score -= 10

        # Deduct points for unhealthy services
        for service_name, status in service_status.items():
            if not status.get("healthy", False):
                score -= 30
                alerts.append(f"Service {service_name} is unhealthy")

        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"

        return {
            "status": status,
            "score": max(0, score),
            "alerts": alerts
        }

    def _get_uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds()

    # Diagnostic test methods

    async def _test_system_resources(self) -> Dict[str, Any]:
        """Test system resource availability."""
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            
            # Check minimum requirements
            min_memory_gb = 4
            min_cpu_cores = 2
            
            passed = (
                memory.total >= min_memory_gb * (1024**3) and
                cpu_count >= min_cpu_cores
            )
            
            return {
                "name": "System Resources",
                "passed": passed,
                "details": {
                    "memory_gb": round(memory.total / (1024**3), 2),
                    "cpu_cores": cpu_count,
                    "min_memory_gb": min_memory_gb,
                    "min_cpu_cores": min_cpu_cores
                }
            }
        except Exception as e:
            return {
                "name": "System Resources",
                "passed": False,
                "error": str(e)
            }

    async def _test_model_service(self) -> Dict[str, Any]:
        """Test model service functionality."""
        try:
            models = await self._model_service.get_available_models()
            return {
                "name": "Model Service",
                "passed": True,
                "details": {
                    "available_models": len(models)
                }
            }
        except Exception as e:
            return {
                "name": "Model Service",
                "passed": False,
                "error": str(e)
            }

    async def _test_voice_service(self) -> Dict[str, Any]:
        """Test voice service functionality."""
        try:
            available = await self._voice_service.is_voice_available()
            return {
                "name": "Voice Service",
                "passed": available,
                "details": {
                    "voice_available": available
                }
            }
        except Exception as e:
            return {
                "name": "Voice Service",
                "passed": False,
                "error": str(e)
            }

    async def _test_hardware_service(self) -> Dict[str, Any]:
        """Test hardware service functionality."""
        try:
            hardware_info = await self._hardware_service.get_hardware_info()
            return {
                "name": "Hardware Service",
                "passed": True,
                "details": {
                    "cpu_available": hardware_info.cpu_available,
                    "gpu_available": hardware_info.gpu_available,
                    "npu_available": hardware_info.npu_available
                }
            }
        except Exception as e:
            return {
                "name": "Hardware Service",
                "passed": False,
                "error": str(e)
            }

    async def _test_memory_allocation(self) -> Dict[str, Any]:
        """Test memory allocation."""
        try:
            # Allocate and deallocate small memory block
            test_size = 100 * 1024 * 1024  # 100MB
            test_data = bytearray(test_size)
            del test_data
            
            return {
                "name": "Memory Allocation",
                "passed": True,
                "details": {
                    "test_size_mb": test_size // (1024**2)
                }
            }
        except Exception as e:
            return {
                "name": "Memory Allocation",
                "passed": False,
                "error": str(e)
            }

    async def _check_model_service_health(self) -> Dict[str, Any]:
        """Check model service health."""
        try:
            models = await self._model_service.get_loaded_models()
            return {
                "service": "model",
                "status": "healthy",
                "details": {
                    "loaded_models": len(models)
                }
            }
        except Exception as e:
            return {
                "service": "model",
                "status": "unhealthy",
                "error": str(e)
            }

    async def _check_voice_service_health(self) -> Dict[str, Any]:
        """Check voice service health."""
        try:
            available = await self._voice_service.is_voice_available()
            return {
                "service": "voice",
                "status": "healthy" if available else "unavailable",
                "details": {
                    "voice_available": available
                }
            }
        except Exception as e:
            return {
                "service": "voice",
                "status": "unhealthy",
                "error": str(e)
            }

    async def _check_hardware_service_health(self) -> Dict[str, Any]:
        """Check hardware service health."""
        try:
            hardware_info = await self._hardware_service.get_hardware_info()
            return {
                "service": "hardware",
                "status": "healthy",
                "details": hardware_info.to_dict()
            }
        except Exception as e:
            return {
                "service": "hardware",
                "status": "unhealthy",
                "error": str(e)
            }