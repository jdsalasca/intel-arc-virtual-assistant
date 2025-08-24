"""
Core interfaces for tool providers.
Defines abstractions for external tools and integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass

class ToolCategory(Enum):
    """Categories of tools."""
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    SEARCH = "search"
    FILE_SYSTEM = "file_system"
    WEB = "web"
    SYSTEM = "system"
    AI = "ai"
    CUSTOM = "custom"

class ToolAuthType(Enum):
    """Authentication types for tools."""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    TOKEN = "token"
    CUSTOM = "custom"

@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = False
    default: Any = None
    options: Optional[List[Any]] = None

@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class IToolProvider(ABC):
    """Abstract interface for tool providers."""
    
    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        pass
    
    @abstractmethod
    def get_tool_description(self) -> str:
        """Get a description of what the tool does."""
        pass
    
    @abstractmethod
    def get_tool_category(self) -> ToolCategory:
        """Get the category of the tool."""
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """Get the parameters required by this tool."""
        pass
    
    @abstractmethod
    def get_auth_type(self) -> ToolAuthType:
        """Get the authentication type required."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool is available and configured."""
        pass
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters before execution."""
        pass

class IWebSearchTool(IToolProvider):
    """Interface for web search tools."""
    
    @abstractmethod
    def search(self, query: str, num_results: int = 10) -> ToolResult:
        """Search the web for a query."""
        pass
    
    @abstractmethod
    def search_news(self, query: str, num_results: int = 10) -> ToolResult:
        """Search for news articles."""
        pass
    
    @abstractmethod
    def search_images(self, query: str, num_results: int = 10) -> ToolResult:
        """Search for images."""
        pass

class IEmailTool(IToolProvider):
    """Interface for email tools."""
    
    @abstractmethod
    def send_email(
        self, 
        to: Union[str, List[str]], 
        subject: str, 
        body: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[str]] = None
    ) -> ToolResult:
        """Send an email."""
        pass
    
    @abstractmethod
    def get_recent_emails(self, count: int = 10) -> ToolResult:
        """Get recent emails."""
        pass
    
    @abstractmethod
    def search_emails(self, query: str, count: int = 10) -> ToolResult:
        """Search emails by query."""
        pass

class IFileTool(IToolProvider):
    """Interface for file system tools."""
    
    @abstractmethod
    def read_file(self, file_path: str) -> ToolResult:
        """Read contents of a file."""
        pass
    
    @abstractmethod
    def write_file(self, file_path: str, content: str) -> ToolResult:
        """Write content to a file."""
        pass
    
    @abstractmethod
    def list_directory(self, directory_path: str) -> ToolResult:
        """List contents of a directory."""
        pass
    
    @abstractmethod
    def create_directory(self, directory_path: str) -> ToolResult:
        """Create a directory."""
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> ToolResult:
        """Delete a file."""
        pass
    
    @abstractmethod
    def copy_file(self, source: str, destination: str) -> ToolResult:
        """Copy a file."""
        pass
    
    @abstractmethod
    def move_file(self, source: str, destination: str) -> ToolResult:
        """Move a file."""
        pass

class ISystemTool(IToolProvider):
    """Interface for system tools."""
    
    @abstractmethod
    def get_system_info(self) -> ToolResult:
        """Get system information."""
        pass
    
    @abstractmethod
    def get_hardware_info(self) -> ToolResult:
        """Get hardware information."""
        pass
    
    @abstractmethod
    def execute_command(self, command: str, safe_mode: bool = True) -> ToolResult:
        """Execute a system command."""
        pass

class IToolRegistry(ABC):
    """Abstract interface for tool registry."""
    
    @abstractmethod
    def register_tool(self, tool: IToolProvider) -> bool:
        """Register a new tool."""
        pass
    
    @abstractmethod
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        pass
    
    @abstractmethod
    def get_tool(self, tool_name: str) -> Optional[IToolProvider]:
        """Get a tool by name."""
        pass
    
    @abstractmethod
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[IToolProvider]:
        """List available tools."""
        pass
    
    @abstractmethod
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name."""
        pass
    
    @abstractmethod
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get the schema for a tool."""
        pass