"""
Core interfaces for agent providers.
Defines abstractions for AI agents and assistant integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator, Union, Callable
from enum import Enum
from dataclasses import dataclass
import asyncio

class AgentType(Enum):
    """Types of AI agents."""
    CONVERSATIONAL = "conversational"
    TASK_ORIENTED = "task_oriented"
    MULTIMODAL = "multimodal"
    SPECIALIZED = "specialized"

class AgentCapability(Enum):
    """Agent capabilities."""
    TEXT_GENERATION = "text_generation"
    CONVERSATION = "conversation"
    TOOL_USAGE = "tool_usage"
    VOICE_INPUT = "voice_input"
    VOICE_OUTPUT = "voice_output"
    WEB_SEARCH = "web_search"
    EMAIL_ACCESS = "email_access"
    FILE_OPERATIONS = "file_operations"
    CODE_GENERATION = "code_generation"
    IMAGE_UNDERSTANDING = "image_understanding"

class ExecutionMode(Enum):
    """Agent execution modes."""
    SYNC = "sync"
    ASYNC = "async"
    STREAMING = "streaming"
    BATCH = "batch"

@dataclass
class AgentRequest:
    """Request to an agent."""
    user_input: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    tools_available: Optional[List[str]] = None
    execution_mode: ExecutionMode = ExecutionMode.ASYNC
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AgentResponse:
    """Response from an agent."""
    content: str
    success: bool = True
    error: Optional[str] = None
    tools_used: Optional[List[str]] = None
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # For streaming responses
    is_partial: bool = False
    is_final: bool = True
    
    # Performance metrics
    processing_time: Optional[float] = None
    token_count: Optional[int] = None

@dataclass
class AgentCapabilities:
    """Agent capabilities description."""
    supported_types: List[AgentType]
    capabilities: List[AgentCapability] 
    max_context_length: Optional[int] = None
    supports_streaming: bool = False
    supports_tools: bool = False
    supported_languages: Optional[List[str]] = None
    hardware_requirements: Optional[Dict[str, Any]] = None

class IAgentProvider(ABC):
    """Abstract interface for AI agent providers."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the agent provider."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the agent provider."""
        pass
    
    @abstractmethod
    def get_agent_name(self) -> str:
        """Get the name of the agent."""
        pass
    
    @abstractmethod
    def get_agent_description(self) -> str:
        """Get a description of the agent."""
        pass
    
    @abstractmethod
    def get_agent_version(self) -> str:
        """Get the version of the agent."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> AgentCapabilities:
        """Get the capabilities of this agent."""
        pass
    
    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if the agent is ready for requests."""
        pass
    
    @abstractmethod
    async def process_request(self, request: AgentRequest) -> Union[AgentResponse, AsyncIterator[AgentResponse]]:
        """Process a user request and return response(s)."""
        pass
    
    @abstractmethod
    async def validate_request(self, request: AgentRequest) -> bool:
        """Validate a request before processing."""
        pass

class IConversationalAgent(IAgentProvider):
    """Interface for conversational AI agents."""
    
    @abstractmethod
    async def start_conversation(self, user_id: Optional[str] = None) -> str:
        """Start a new conversation and return conversation ID."""
        pass
    
    @abstractmethod
    async def continue_conversation(self, conversation_id: str, user_input: str, **kwargs) -> AgentResponse:
        """Continue an existing conversation."""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history."""
        pass
    
    @abstractmethod
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history."""
        pass

class IToolCapableAgent(IAgentProvider):
    """Interface for agents that can use tools."""
    
    @abstractmethod
    async def register_tool(self, tool_name: str, tool_provider: Any) -> bool:
        """Register a tool with the agent."""
        pass
    
    @abstractmethod
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool from the agent."""
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        pass

class IMultimodalAgent(IAgentProvider):
    """Interface for multimodal AI agents."""
    
    @abstractmethod
    async def process_text(self, text: str, **kwargs) -> AgentResponse:
        """Process text input."""
        pass
    
    @abstractmethod
    async def process_voice(self, audio_data: bytes, **kwargs) -> AgentResponse:
        """Process voice input."""
        pass
    
    @abstractmethod
    async def process_image(self, image_data: bytes, prompt: Optional[str] = None, **kwargs) -> AgentResponse:
        """Process image input."""
        pass
    
    @abstractmethod
    async def generate_voice(self, text: str, **kwargs) -> bytes:
        """Generate voice output from text."""
        pass

class IAgentOrchestrator(ABC):
    """Interface for orchestrating multiple agents."""
    
    @abstractmethod
    async def register_agent(self, agent_id: str, agent: IAgentProvider) -> bool:
        """Register an agent with the orchestrator."""
        pass
    
    @abstractmethod
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the orchestrator."""
        pass
    
    @abstractmethod
    def get_available_agents(self) -> List[str]:
        """Get list of available agents."""
        pass
    
    @abstractmethod
    async def route_request(self, request: AgentRequest, preferred_agent: Optional[str] = None) -> AgentResponse:
        """Route a request to the appropriate agent."""
        pass
    
    @abstractmethod
    async def get_agent_for_request(self, request: AgentRequest) -> Optional[str]:
        """Determine which agent should handle a request."""
        pass

class IAgentMiddleware(ABC):
    """Interface for agent middleware components."""
    
    @abstractmethod
    async def before_request(self, request: AgentRequest) -> AgentRequest:
        """Process request before sending to agent."""
        pass
    
    @abstractmethod
    async def after_response(self, response: AgentResponse) -> AgentResponse:
        """Process response after receiving from agent."""
        pass
    
    @abstractmethod
    async def on_error(self, error: Exception, request: AgentRequest) -> Optional[AgentResponse]:
        """Handle errors during processing."""
        pass

class IAgentEventListener(ABC):
    """Interface for agent event listeners."""
    
    @abstractmethod
    async def on_agent_registered(self, agent_id: str, agent: IAgentProvider) -> None:
        """Called when an agent is registered."""
        pass
    
    @abstractmethod
    async def on_agent_unregistered(self, agent_id: str) -> None:
        """Called when an agent is unregistered."""
        pass
    
    @abstractmethod
    async def on_request_started(self, request: AgentRequest) -> None:
        """Called when a request starts processing."""
        pass
    
    @abstractmethod
    async def on_request_completed(self, request: AgentRequest, response: AgentResponse) -> None:
        """Called when a request completes successfully."""
        pass
    
    @abstractmethod
    async def on_request_failed(self, request: AgentRequest, error: Exception) -> None:
        """Called when a request fails."""
        pass