"""
File Operations Tool Provider
Provides secure file system operations with proper validation.
"""

import logging
import os
import shutil
import mimetypes
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import hashlib
from datetime import datetime

from core.interfaces.tool_provider import (
    IFileTool, ToolCategory, ToolAuthType, ToolParameter, 
    ToolResult, ParameterType
)
from core.exceptions import ToolExecutionException

logger = logging.getLogger(__name__)

class FileOperationsTool(IFileTool):
    """Secure file operations tool with restricted access."""
    
    def __init__(self, allowed_directories: Optional[List[str]] = None):
        self.name = "file_operations"
        
        # Security: Define allowed directories
        if allowed_directories is None:
            # Default safe directories
            home_dir = Path.home()
            self.allowed_directories = [
                str(home_dir / "Documents"),
                str(home_dir / "Downloads"),
                str(home_dir / "Desktop"),
                "./workspace",  # Relative to current working directory
                "./temp"
            ]
        else:
            self.allowed_directories = allowed_directories
        
        # Ensure allowed directories exist
        for dir_path in self.allowed_directories:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create directory {dir_path}: {e}")
        
        # Security restrictions
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.forbidden_extensions = {'.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js'}
        self.max_path_length = 260  # Windows limitation
    
    def get_tool_name(self) -> str:
        return self.name
    
    def get_tool_description(self) -> str:
        return "Perform secure file operations including read, write, list, and manage files"
    
    def get_tool_category(self) -> ToolCategory:
        return ToolCategory.FILE_SYSTEM
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="operation",
                type=ParameterType.STRING,
                description="File operation to perform",
                required=True,
                enum_values=["read", "write", "list", "create_dir", "delete", "copy", "move", "info"]
            ),
            ToolParameter(
                name="path",
                type=ParameterType.STRING,
                description="File or directory path",
                required=True,
                max_length=self.max_path_length
            ),
            ToolParameter(
                name="content",
                type=ParameterType.STRING,
                description="Content to write (for write operations)",
                required=False,
                max_length=1024 * 1024  # 1MB max content
            ),
            ToolParameter(
                name="destination",
                type=ParameterType.STRING,
                description="Destination path (for copy/move operations)",
                required=False,
                max_length=self.max_path_length
            ),
            ToolParameter(
                name="recursive",
                type=ParameterType.BOOLEAN,
                description="Recursive operation for directories",
                required=False,
                default=False
            ),
            ToolParameter(
                name="create_parents",
                type=ParameterType.BOOLEAN,
                description="Create parent directories if they don't exist",
                required=False,
                default=False
            )
        ]
    
    def get_auth_type(self) -> ToolAuthType:
        return ToolAuthType.NONE
    
    def is_available(self) -> bool:
        """Check if file operations are available."""
        try:
            # Test if we can access at least one allowed directory
            for dir_path in self.allowed_directories:
                if os.path.exists(dir_path) and os.access(dir_path, os.R_OK):
                    return True
            return False
        except:
            return False
    
    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute file operation."""
        try:
            operation = parameters.get("operation")
            path = parameters.get("path", "").strip()
            
            if not operation or not path:
                raise ToolExecutionException("Operation and path are required")
            
            # Security validation
            validated_path = self._validate_and_resolve_path(path)
            
            # Route to appropriate operation
            if operation == "read":
                return self._read_file(validated_path)
            elif operation == "write":
                content = parameters.get("content", "")
                create_parents = parameters.get("create_parents", False)
                return self._write_file(validated_path, content, create_parents)
            elif operation == "list":
                recursive = parameters.get("recursive", False)
                return self._list_directory(validated_path, recursive)
            elif operation == "create_dir":
                create_parents = parameters.get("create_parents", False)
                return self._create_directory(validated_path, create_parents)
            elif operation == "delete":
                recursive = parameters.get("recursive", False)
                return self._delete_file(validated_path, recursive)
            elif operation == "copy":
                destination = parameters.get("destination", "")
                if not destination:
                    raise ToolExecutionException("Destination is required for copy operation")
                validated_dest = self._validate_and_resolve_path(destination)
                return self._copy_file(validated_path, validated_dest)
            elif operation == "move":
                destination = parameters.get("destination", "")
                if not destination:
                    raise ToolExecutionException("Destination is required for move operation")
                validated_dest = self._validate_and_resolve_path(destination)
                return self._move_file(validated_path, validated_dest)
            elif operation == "info":
                return self._get_file_info(validated_path)
            else:
                raise ToolExecutionException(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"File operation failed: {e}")
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="failed",
                success=False,
                error=str(e)
            )
    
    def read_file(self, file_path: str) -> ToolResult:
        """Read contents of a file."""
        return self.execute({"operation": "read", "path": file_path})
    
    def write_file(self, file_path: str, content: str) -> ToolResult:
        """Write content to a file."""
        return self.execute({"operation": "write", "path": file_path, "content": content})
    
    def list_directory(self, directory_path: str) -> ToolResult:
        """List contents of a directory."""
        return self.execute({"operation": "list", "path": directory_path})
    
    def create_directory(self, directory_path: str) -> ToolResult:
        """Create a directory."""
        return self.execute({"operation": "create_dir", "path": directory_path})
    
    def delete_file(self, file_path: str) -> ToolResult:
        """Delete a file."""
        return self.execute({"operation": "delete", "path": file_path})
    
    def copy_file(self, source: str, destination: str) -> ToolResult:
        """Copy a file."""
        return self.execute({"operation": "copy", "path": source, "destination": destination})
    
    def move_file(self, source: str, destination: str) -> ToolResult:
        """Move a file."""
        return self.execute({"operation": "move", "path": source, "destination": destination})
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate file operation parameters."""
        try:
            operation = parameters.get("operation")
            if operation not in ["read", "write", "list", "create_dir", "delete", "copy", "move", "info"]:
                return False
            
            path = parameters.get("path", "")
            if not isinstance(path, str) or len(path.strip()) == 0:
                return False
            
            # Validate path security
            try:
                self._validate_and_resolve_path(path)
            except:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Parameter validation failed: {e}")
            return False
    
    def _validate_and_resolve_path(self, path: str) -> Path:
        """Validate and resolve a file path for security."""
        try:
            # Convert to Path object
            path_obj = Path(path).expanduser().resolve()
            
            # Check path length
            if len(str(path_obj)) > self.max_path_length:
                raise ToolExecutionException("Path too long")
            
            # Check for forbidden characters (more permissive for Windows)
            forbidden_chars = ['<', '>', '"', '|', '?', '*']
            # Note: Removed ':' to allow Windows drive letters
            path_str = str(path_obj)
            if any(char in path_str for char in forbidden_chars):
                raise ToolExecutionException("Path contains forbidden characters")
            
            # Check if path is within allowed directories or current working directory
            allowed = False
            
            # Allow current working directory and subdirectories
            cwd = Path.cwd().resolve()
            if str(path_obj).startswith(str(cwd)):
                allowed = True
            
            # Check configured allowed directories
            if not allowed:
                for allowed_dir in self.allowed_directories:
                    try:
                        allowed_dir_resolved = Path(allowed_dir).expanduser().resolve()
                        if str(path_obj).startswith(str(allowed_dir_resolved)):
                            allowed = True
                            break
                    except Exception:
                        continue
            
            if not allowed:
                raise ToolExecutionException("Path is outside allowed directories")
            
            # Check file extension for security (only for files, not directories)
            if path_obj.suffix and path_obj.suffix.lower() in self.forbidden_extensions:
                raise ToolExecutionException("File type not allowed")
            
            return path_obj
            
        except Exception as e:
            if isinstance(e, ToolExecutionException):
                raise
            raise ToolExecutionException(f"Invalid path: {e}")
    
    def _read_file(self, path: Path) -> ToolResult:
        """Read file contents."""
        try:
            if not path.exists():
                raise ToolExecutionException("File does not exist")
            
            if not path.is_file():
                raise ToolExecutionException("Path is not a file")
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                raise ToolExecutionException("File too large")
            
            # Determine if file is text or binary
            mime_type, _ = mimetypes.guess_type(str(path))
            is_text = mime_type and mime_type.startswith('text')
            
            if is_text:
                # Read as text
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                return ToolResult(
                    request_id="",
                    tool_name=self.name,
                    status="completed",
                    success=True,
                    data={
                        "content": content,
                        "size": file_size,
                        "mime_type": mime_type,
                        "encoding": "utf-8"
                    }
                )
            else:
                # For binary files, return metadata only
                return ToolResult(
                    request_id="",
                    tool_name=self.name,
                    status="completed",
                    success=True,
                    data={
                        "message": "Binary file - content not displayed",
                        "size": file_size,
                        "mime_type": mime_type,
                        "path": str(path)
                    }
                )
                
        except Exception as e:
            raise ToolExecutionException(f"Failed to read file: {e}")
    
    def _write_file(self, path: Path, content: str, create_parents: bool) -> ToolResult:
        """Write content to file."""
        try:
            # Check content size
            if len(content.encode('utf-8')) > self.max_file_size:
                raise ToolExecutionException("Content too large")
            
            # Create parent directories if requested
            if create_parents:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="completed",
                success=True,
                data={
                    "message": "File written successfully",
                    "path": str(path),
                    "size": len(content.encode('utf-8'))
                }
            )
            
        except Exception as e:
            raise ToolExecutionException(f"Failed to write file: {e}")
    
    def _list_directory(self, path: Path, recursive: bool) -> ToolResult:
        """List directory contents."""
        try:
            if not path.exists():
                raise ToolExecutionException("Directory does not exist")
            
            if not path.is_dir():
                raise ToolExecutionException("Path is not a directory")
            
            items = []
            
            if recursive:
                for item in path.rglob('*'):
                    items.append(self._get_item_info(item))
            else:
                for item in path.iterdir():
                    items.append(self._get_item_info(item))
            
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="completed",
                success=True,
                data={
                    "path": str(path),
                    "files": items,  # Changed from 'items' to 'files' to match test expectation
                    "count": len(items),
                    "recursive": recursive
                }
            )
            
        except Exception as e:
            raise ToolExecutionException(f"Failed to list directory: {e}")
    
    def _create_directory(self, path: Path, create_parents: bool) -> ToolResult:
        """Create directory."""
        try:
            if path.exists():
                return ToolResult(
                    request_id="",
                    tool_name=self.name,
                    status="completed",
                    success=True,
                    data={
                        "message": "Directory already exists",
                        "path": str(path)
                    }
                )
            
            path.mkdir(parents=create_parents, exist_ok=True)
            
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="completed",
                success=True,
                data={
                    "message": "Directory created successfully",
                    "path": str(path)
                }
            )
            
        except Exception as e:
            raise ToolExecutionException(f"Failed to create directory: {e}")
    
    def _delete_file(self, path: Path, recursive: bool) -> ToolResult:
        """Delete file or directory."""
        try:
            if not path.exists():
                raise ToolExecutionException("Path does not exist")
            
            if path.is_file():
                path.unlink()
                message = "File deleted successfully"
            elif path.is_dir():
                if recursive:
                    shutil.rmtree(path)
                    message = "Directory deleted recursively"
                else:
                    path.rmdir()  # Only works for empty directories
                    message = "Empty directory deleted"
            else:
                raise ToolExecutionException("Unknown file type")
            
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="completed",
                success=True,
                data={
                    "message": message,
                    "path": str(path)
                }
            )
            
        except Exception as e:
            raise ToolExecutionException(f"Failed to delete: {e}")
    
    def _copy_file(self, source: Path, destination: Path) -> ToolResult:
        """Copy file or directory."""
        try:
            if not source.exists():
                raise ToolExecutionException("Source does not exist")
            
            if source.is_file():
                # Check file size
                if source.stat().st_size > self.max_file_size:
                    raise ToolExecutionException("File too large to copy")
                
                shutil.copy2(source, destination)
                message = "File copied successfully"
            elif source.is_dir():
                shutil.copytree(source, destination)
                message = "Directory copied successfully"
            else:
                raise ToolExecutionException("Unknown file type")
            
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="completed",
                success=True,
                data={
                    "message": message,
                    "source": str(source),
                    "destination": str(destination)
                }
            )
            
        except Exception as e:
            raise ToolExecutionException(f"Failed to copy: {e}")
    
    def _move_file(self, source: Path, destination: Path) -> ToolResult:
        """Move file or directory."""
        try:
            if not source.exists():
                raise ToolExecutionException("Source does not exist")
            
            shutil.move(str(source), str(destination))
            
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="completed",
                success=True,
                data={
                    "message": "Moved successfully",
                    "source": str(source),
                    "destination": str(destination)
                }
            )
            
        except Exception as e:
            raise ToolExecutionException(f"Failed to move: {e}")
    
    def _get_file_info(self, path: Path) -> ToolResult:
        """Get file information."""
        try:
            if not path.exists():
                raise ToolExecutionException("Path does not exist")
            
            info = self._get_item_info(path)
            
            return ToolResult(
                request_id="",
                tool_name=self.name,
                status="completed",
                success=True,
                data=info
            )
            
        except Exception as e:
            raise ToolExecutionException(f"Failed to get file info: {e}")
    
    def _get_item_info(self, path: Path) -> Dict[str, Any]:
        """Get detailed information about a file or directory."""
        try:
            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(str(path))
            
            info = {
                "name": path.name,
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size if path.is_file() else None,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "mime_type": mime_type,
                "extension": path.suffix.lower() if path.suffix else None
            }
            
            # Add file hash for files
            if path.is_file() and stat.st_size < 10 * 1024 * 1024:  # < 10MB
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                        info["md5"] = hashlib.md5(content).hexdigest()
                except:
                    pass
            
            return info
            
        except Exception as e:
            return {
                "name": path.name,
                "path": str(path),
                "error": str(e)
            }