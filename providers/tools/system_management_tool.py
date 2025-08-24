"""
System Management Tool Provider
Provides secure system operations and computer management capabilities.
"""

import logging
import platform
import psutil
import subprocess
import os
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from core.interfaces.tool_provider import (
    ISystemTool, ToolCategory, ToolAuthType, ToolParameter, 
    ToolResult, ParameterType
)
from core.exceptions import ToolExecutionException

logger = logging.getLogger(__name__)

class SystemManagementTool(ISystemTool):
    """System management tool with secure computer control capabilities."""
    
    def __init__(self):
        self.name = "system_management"
        
        # Security: Define allowed operations
        self.safe_operations = {
            "get_system_info", "get_hardware_info", "get_processes", 
            "get_disk_usage", "get_memory_usage", "get_cpu_usage",
            "get_network_info", "get_environment_vars", "get_installed_software",
            "open_application", "close_application", "get_running_apps"
        }
        
        # Restricted operations that require explicit permission
        self.restricted_operations = {
            "execute_command", "restart_system", "shutdown_system",
            "kill_process", "modify_registry", "install_software"
        }
        
        # Track execution for security
        self.execution_log = []
    
    def get_tool_name(self) -> str:
        return self.name
    
    def get_tool_description(self) -> str:
        return "Perform secure system management and computer control operations"
    
    def get_tool_category(self) -> ToolCategory:
        return ToolCategory.SYSTEM
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="operation",
                type=ParameterType.STRING,
                description="System operation to perform",
                required=True,
                enum_values=list(self.safe_operations) + list(self.restricted_operations)
            ),
            ToolParameter(
                name="target",
                type=ParameterType.STRING,
                description="Target for the operation (process name, application, etc.)",
                required=False,
                max_length=256
            ),
            ToolParameter(
                name="parameters",
                type=ParameterType.OBJECT,
                description="Additional parameters for the operation",
                required=False
            ),
            ToolParameter(
                name="safe_mode",
                type=ParameterType.BOOLEAN,
                description="Enable safe mode (restricts dangerous operations)",
                required=False,
                default=True
            )
        ]
    
    def get_auth_type(self) -> ToolAuthType:
        return ToolAuthType.NONE
    
    def is_available(self) -> bool:
        """Check if system operations are available."""
        try:
            # Basic system info should always be available
            return platform.system() is not None
        except:
            return False
    
    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute system operation."""
        try:
            operation = parameters.get("operation")
            target = parameters.get("target", "")
            op_params = parameters.get("parameters", {})
            safe_mode = parameters.get("safe_mode", True)
            
            if not operation:
                raise ToolExecutionException("Operation is required")
            
            # Log the operation
            self._log_operation(operation, target, safe_mode)
            
            # Security check
            if operation in self.restricted_operations and safe_mode:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Operation '{operation}' is restricted in safe mode"
                )
            
            # Route to appropriate operation
            if operation == "get_system_info":
                return self.get_system_info()
            elif operation == "get_hardware_info":
                return self.get_hardware_info()
            elif operation == "get_processes":
                return self._get_processes(target)
            elif operation == "get_disk_usage":
                return self._get_disk_usage()
            elif operation == "get_memory_usage":
                return self._get_memory_usage()
            elif operation == "get_cpu_usage":
                return self._get_cpu_usage()
            elif operation == "get_network_info":
                return self._get_network_info()
            elif operation == "get_environment_vars":
                return self._get_environment_vars()
            elif operation == "get_installed_software":
                return self._get_installed_software()
            elif operation == "open_application":
                return self._open_application(target, op_params)
            elif operation == "close_application":
                return self._close_application(target)
            elif operation == "get_running_apps":
                return self._get_running_apps()
            elif operation == "execute_command":
                return self.execute_command(target, safe_mode)
            else:
                raise ToolExecutionException(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"System operation failed: {e}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e)
            )
    
    def get_system_info(self) -> ToolResult:
        """Get comprehensive system information."""
        try:
            info = {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "architecture": platform.architecture(),
                    "hostname": platform.node()
                },
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation(),
                    "executable": sys.executable
                },
                "system_stats": {
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                    "uptime_seconds": psutil.time.time() - psutil.boot_time(),
                    "cpu_count": psutil.cpu_count(),
                    "cpu_count_logical": psutil.cpu_count(logical=True)
                }
            }
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=info,
                message="System information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get system info: {e}"
            )
    
    def get_hardware_info(self) -> ToolResult:
        """Get hardware information."""
        try:
            # Memory information
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            info = {
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percentage": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percentage": round((disk.used / disk.total) * 100, 2)
                },
                "cpu": {
                    "physical_cores": psutil.cpu_count(logical=False),
                    "logical_cores": psutil.cpu_count(logical=True),
                    "max_frequency_mhz": getattr(psutil.cpu_freq(), 'max', 'Unknown'),
                    "current_frequency_mhz": getattr(psutil.cpu_freq(), 'current', 'Unknown')
                }
            }
            
            # Try to get GPU information
            try:
                info["gpu"] = self._get_gpu_info()
            except:
                info["gpu"] = {"error": "GPU information not available"}
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=info,
                message="Hardware information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get hardware info: {e}"
            )
    
    def execute_command(self, command: str, safe_mode: bool = True) -> ToolResult:
        """Execute a system command with safety restrictions."""
        try:
            if safe_mode:
                # In safe mode, only allow read-only commands
                safe_commands = ["dir", "ls", "echo", "whoami", "hostname", "date", "time"]
                if not any(command.lower().startswith(cmd) for cmd in safe_commands):
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        error="Command not allowed in safe mode"
                    )
            
            # Execute command with timeout
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return ToolResult(
                tool_name=self.name,
                success=result.returncode == 0,
                data={
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                },
                message=f"Command executed with return code {result.returncode}"
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Command execution timed out"
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Command execution failed: {e}"
            )
    
    def _get_processes(self, filter_name: str = "") -> ToolResult:
        """Get running processes information."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if not filter_name or filter_name.lower() in info['name'].lower():
                        processes.append({
                            "pid": info['pid'],
                            "name": info['name'],
                            "cpu_percent": info['cpu_percent'],
                            "memory_percent": round(info['memory_percent'], 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"processes": processes[:50]},  # Limit to top 50
                message=f"Found {len(processes)} processes"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get processes: {e}"
            )
    
    def _get_cpu_usage(self) -> ToolResult:
        """Get CPU usage information."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            
            info = {
                "overall_percent": psutil.cpu_percent(interval=1),
                "per_cpu_percent": cpu_percent,
                "load_average": getattr(psutil, 'getloadavg', lambda: (0, 0, 0))()
            }
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=info,
                message="CPU usage retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get CPU usage: {e}"
            )
    
    def _get_memory_usage(self) -> ToolResult:
        """Get memory usage information."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            info = {
                "virtual_memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percentage": memory.percent
                },
                "swap_memory": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "free_gb": round(swap.free / (1024**3), 2),
                    "percentage": swap.percent
                }
            }
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=info,
                message="Memory usage retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get memory usage: {e}"
            )
    
    def _get_disk_usage(self) -> ToolResult:
        """Get disk usage information."""
        try:
            disk_info = []
            
            # Get all disk partitions
            for partition in psutil.disk_partitions():
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "file_system": partition.fstype,
                        "total_gb": round(partition_usage.total / (1024**3), 2),
                        "used_gb": round(partition_usage.used / (1024**3), 2),
                        "free_gb": round(partition_usage.free / (1024**3), 2),
                        "percentage": round((partition_usage.used / partition_usage.total) * 100, 2)
                    })
                except PermissionError:
                    continue
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"disks": disk_info},
                message="Disk usage retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get disk usage: {e}"
            )
    
    def _get_network_info(self) -> ToolResult:
        """Get network information."""
        try:
            # Network interfaces
            interfaces = []
            for interface_name, addresses in psutil.net_if_addrs().items():
                interface_info = {"name": interface_name, "addresses": []}
                for addr in addresses:
                    interface_info["addresses"].append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask
                    })
                interfaces.append(interface_info)
            
            # Network statistics
            net_stats = psutil.net_io_counters()
            
            info = {
                "interfaces": interfaces,
                "statistics": {
                    "bytes_sent": net_stats.bytes_sent,
                    "bytes_received": net_stats.bytes_recv,
                    "packets_sent": net_stats.packets_sent,
                    "packets_received": net_stats.packets_recv
                }
            }
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=info,
                message="Network information retrieved successfully"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get network info: {e}"
            )
    
    def _get_environment_vars(self) -> ToolResult:
        """Get environment variables (filtered for security)."""
        try:
            # Filter out sensitive environment variables
            safe_vars = {}
            sensitive_keys = {'password', 'key', 'secret', 'token', 'auth'}
            
            for key, value in os.environ.items():
                if not any(sensitive in key.lower() for sensitive in sensitive_keys):
                    safe_vars[key] = value
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"environment_variables": safe_vars},
                message=f"Retrieved {len(safe_vars)} environment variables"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get environment variables: {e}"
            )
    
    def _get_installed_software(self) -> ToolResult:
        """Get list of installed software (Windows only)."""
        try:
            if platform.system() != "Windows":
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error="Installed software listing only supported on Windows"
                )
            
            # Use registry to get installed programs
            import winreg
            
            software_list = []
            registry_keys = [
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
                r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
            ]
            
            for registry_key in registry_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_key) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                        software_list.append({"name": name, "version": version})
                                    except FileNotFoundError:
                                        continue
                            except OSError:
                                continue
                except FileNotFoundError:
                    continue
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"installed_software": software_list[:100]},  # Limit to 100
                message=f"Found {len(software_list)} installed programs"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get installed software: {e}"
            )
    
    def _open_application(self, app_name: str, params: Dict[str, Any]) -> ToolResult:
        """Open an application."""
        try:
            if not app_name:
                raise ToolExecutionException("Application name is required")
            
            if platform.system() == "Windows":
                # Try to start the application
                result = subprocess.run(
                    ["start", app_name],
                    shell=True,
                    capture_output=True,
                    text=True
                )
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ["open", "-a", app_name],
                    capture_output=True,
                    text=True
                )
            else:  # Linux
                result = subprocess.run(
                    [app_name],
                    capture_output=True,
                    text=True
                )
            
            return ToolResult(
                tool_name=self.name,
                success=result.returncode == 0,
                data={"application": app_name, "return_code": result.returncode},
                message=f"Attempted to open {app_name}"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to open application: {e}"
            )
    
    def _close_application(self, app_name: str) -> ToolResult:
        """Close an application by name."""
        try:
            if not app_name:
                raise ToolExecutionException("Application name is required")
            
            closed_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name.lower() in proc.info['name'].lower():
                        proc.terminate()
                        closed_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return ToolResult(
                tool_name=self.name,
                success=len(closed_processes) > 0,
                data={"closed_processes": closed_processes},
                message=f"Closed {len(closed_processes)} processes matching '{app_name}'"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to close application: {e}"
            )
    
    def _get_running_apps(self) -> ToolResult:
        """Get list of running applications."""
        try:
            apps = set()
            for proc in psutil.process_iter(['name']):
                try:
                    apps.add(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"running_applications": sorted(list(apps))},
                message=f"Found {len(apps)} running applications"
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to get running applications: {e}"
            )
    
    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information (basic implementation)."""
        try:
            # Try to get GPU info using different methods
            gpu_info = {"gpus": []}
            
            # Method 1: Try nvidia-smi for NVIDIA GPUs
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split(', ')
                            if len(parts) >= 3:
                                gpu_info["gpus"].append({
                                    "name": parts[0],
                                    "memory_mb": parts[1],
                                    "utilization": parts[2],
                                    "vendor": "NVIDIA"
                                })
            except:
                pass
            
            # Method 2: Check for Intel GPU via registry (Windows) or other methods
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["wmic", "path", "win32_VideoController", "get", "name"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        for line in result.stdout.strip().split('\n'):
                            line = line.strip()
                            if line and line != "Name":
                                gpu_info["gpus"].append({
                                    "name": line,
                                    "vendor": "Intel" if "intel" in line.lower() else "Unknown"
                                })
                except:
                    pass
            
            return gpu_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def _log_operation(self, operation: str, target: str, safe_mode: bool):
        """Log operation for security tracking."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "target": target,
            "safe_mode": safe_mode
        }
        self.execution_log.append(log_entry)
        
        # Keep only last 100 entries
        if len(self.execution_log) > 100:
            self.execution_log = self.execution_log[-100:]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate system operation parameters."""
        try:
            operation = parameters.get("operation")
            if not operation or operation not in (self.safe_operations | self.restricted_operations):
                return False
            
            return True
            
        except Exception:
            return False

# Example usage and testing
if __name__ == "__main__":
    tool = SystemManagementTool()
    
    # Test system info
    result = tool.get_system_info()
    print("System Info:", result.data if result.success else result.error)
    
    # Test hardware info
    result = tool.get_hardware_info()
    print("Hardware Info:", result.data if result.success else result.error)