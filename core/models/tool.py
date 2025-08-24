"""
Core data models for tool management and execution.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid

class ToolCategory(str, Enum):
    """Categories of tools."""
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    SEARCH = "search"
    FILE_SYSTEM = "file_system"
    WEB = "web"
    SYSTEM = "system"
    AI = "ai"
    CUSTOM = "custom"

class ToolStatus(str, Enum):
    """Status of tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ToolAuthType(str, Enum):
    """Authentication types for tools."""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    TOKEN = "token"
    BASIC_AUTH = "basic_auth"
    CUSTOM = "custom"

class ParameterType(str, Enum):
    """Types of tool parameters."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    URL = "url"

class ToolParameter(BaseModel):
    """Definition of a tool parameter."""
    
    name: str
    type: ParameterType
    description: str
    required: bool = False
    default: Any = None
    
    # Validation constraints
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # regex pattern
    enum_values: Optional[List[Any]] = None
    
    # UI hints
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    widget: Optional[str] = None  # text, textarea, select, file, etc.

class ToolRequest(BaseModel):
    """Request to execute a tool."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    parameters: Dict[str, Any]
    user_id: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    
    # Request metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timeout: Optional[int] = 30  # seconds
    priority: int = 0  # higher = more priority
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ToolResult(BaseModel):
    """Result of tool execution."""
    
    request_id: str
    tool_name: str
    status: ToolStatus
    success: bool = False
    
    # Results
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Output formatting
    formatted_output: Optional[str] = None
    output_type: str = "text"  # text, json, html, markdown, etc.

class ToolDefinition(BaseModel):
    """Definition of a tool."""
    
    name: str
    display_name: str
    description: str
    category: ToolCategory
    version: str = "1.0.0"
    
    # Parameters
    parameters: List[ToolParameter] = Field(default_factory=list)
    
    # Authentication
    auth_type: ToolAuthType = ToolAuthType.NONE
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Capabilities
    supports_streaming: bool = False
    supports_cancellation: bool = False
    max_execution_time: int = 30  # seconds
    rate_limit: Optional[int] = None  # requests per minute
    
    # Requirements
    required_permissions: List[str] = Field(default_factory=list)
    required_config: List[str] = Field(default_factory=list)
    
    # Availability
    is_enabled: bool = True
    is_premium: bool = False
    provider: str = "default"
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_parameter(self, name: str) -> Optional[ToolParameter]:
        """Get a parameter by name."""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """Validate parameters and return list of errors."""
        errors = []
        
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"Required parameter '{param.name}' is missing")
        
        # Validate parameter types and constraints
        for name, value in parameters.items():
            param = self.get_parameter(name)
            if param:
                # Type validation would go here
                pass
        
        return errors

class ToolExecution(BaseModel):
    """Execution record for a tool."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    request: ToolRequest
    result: Optional[ToolResult] = None
    
    # Execution tracking
    status: ToolStatus = ToolStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Resource usage
    cpu_time: Optional[float] = None
    memory_usage: Optional[int] = None
    network_requests: Optional[int] = None
    
    # Logging
    logs: List[str] = Field(default_factory=list)
    
    def add_log(self, message: str) -> None:
        """Add a log message."""
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")

class ToolUsageStats(BaseModel):
    """Usage statistics for a tool."""
    
    tool_name: str
    user_id: Optional[str] = None
    
    # Counters
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    
    # Timing
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    
    # Dates
    first_used: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    # Period stats (daily, weekly, monthly)
    daily_usage: Dict[str, int] = Field(default_factory=dict)
    weekly_usage: Dict[str, int] = Field(default_factory=dict)
    monthly_usage: Dict[str, int] = Field(default_factory=dict)

class ToolConfiguration(BaseModel):
    """Configuration for a tool."""
    
    tool_name: str
    user_id: Optional[str] = None  # None for global config
    
    # Authentication credentials
    credentials: Dict[str, str] = Field(default_factory=dict)
    
    # Tool-specific settings
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Permissions and limits
    enabled: bool = True
    max_requests_per_minute: Optional[int] = None
    max_requests_per_day: Optional[int] = None
    allowed_operations: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }