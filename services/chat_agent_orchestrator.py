"""
ChatAgent Orchestrator - Main Intelligence Coordinator
Integrates LLM, TTS, tools, and conversation management into a cohesive AI assistant.
"""

import os
import logging
import asyncio
import json
import time
import re
from typing import Dict, List, Any, Optional, Union, AsyncIterator
from datetime import datetime
from pathlib import Path

from core.interfaces.agent_provider import (
    IConversationalAgent, IToolCapableAgent, IMultimodalAgent,
    AgentRequest, AgentResponse, AgentCapabilities, AgentType, AgentCapability, ExecutionMode
)
from core.interfaces.model_provider import ITextGenerator, IChatModel, DeviceType
from core.interfaces.voice_provider import IVoiceOutput
from core.interfaces.tool_provider import IToolProvider
from core.models.conversation import Message, MessageRole, Conversation
from services.conversation_manager import ConversationManager
from services.model_manager import ModelManager
from services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class ChatAgentOrchestrator(IConversationalAgent, IToolCapableAgent, IMultimodalAgent):
    """
    Main ChatAgent that orchestrates all AI assistant capabilities.
    Follows Clean Architecture principles with clear separation of concerns.
    """
    
    def __init__(
        self,
        model_manager: ModelManager,
        conversation_manager: ConversationManager,
        tool_registry: Optional[ToolRegistry] = None
    ):
        self.model_manager = model_manager
        self.conversation_manager = conversation_manager
        self.tool_registry = tool_registry or ToolRegistry()
        
        # Agent configuration
        self.agent_config = {
            "name": "Intel AI Assistant",
            "version": "1.0.0",
            "description": "Intelligent virtual assistant optimized for Intel hardware",
            "primary_model": "mistral-7b-instruct",
            "tts_model": "speecht5-tts",
            "max_context_length": 8192,
            "default_max_tokens": 256,
            "default_temperature": 0.7
        }
        
        # State management
        self.is_initialized = False
        self.active_conversations = {}
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "tools_used": {},
            "average_response_time": 0.0
        }
        
        # Tool usage patterns and decision logic
        self.tool_patterns = {
            "web_search": [
                r"search\s+(for\s+)?(.+)",
                r"look\s+up\s+(.+)",
                r"find\s+(information\s+about\s+)?(.+)",
                r"what\s+is\s+(.+)\s+(today|currently|now)",
                r"latest\s+(.+)",
                r"current\s+(.+)",
                r"news\s+about\s+(.+)"
            ],
            "gmail_connector": [
                r"check\s+(my\s+)?email",
                r"read\s+(my\s+)?email",
                r"send\s+(an\s+)?email\s+to\s+(.+)",
                r"email\s+(.+)",
                r"unread\s+emails?",
                r"recent\s+emails?"
            ],
            "music_control": [
                r"^(play)\b(.*)$",
                r"\b(pause|resume|next|previous)\b",
                r"volume\s+(up|down|set\s+\d+)%?"
            ]
        }
        
        # System prompt for Mistral
        self.system_prompt = """You are an intelligent AI assistant optimized for Intel hardware. You are helpful, informative, and engaging. 

Key capabilities:
- Answer questions using your knowledge and available tools
- Search the web for current information when needed
- Access Gmail when requested (if configured)
- Provide clear, concise, and accurate responses
- Cite sources when using external information

Guidelines:
- If you need current information, use web search
- If asked about emails, use Gmail tools (if available)
- Always be helpful and polite
- Keep responses focused and relevant
- When using tools, explain what you're doing

Tool usage format:
When you need to use a tool, respond with: [TOOL: tool_name] parameters

Available tools: {available_tools}
"""
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the chat agent with configuration."""
        try:
            # Update configuration
            self.agent_config.update(config)
            
            # Initialize model manager
            if not await self._initialize_models():
                logger.error("Failed to initialize models")
                return False
            
            # Initialize tools
            await self._initialize_tools()
            
            # Load conversation manager
            await self._initialize_conversation_manager()
            
            self.is_initialized = True
            logger.info("✅ ChatAgent initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ChatAgent: {e}")
            return False
    
    async def _initialize_models(self) -> bool:
        """Initialize required AI models."""
        try:
            # Load primary LLM
            primary_model = self.agent_config["primary_model"]
            success = await self.model_manager.load_model(primary_model)
            if not success:
                logger.error(f"Failed to load primary model: {primary_model}")
                return False
            
            logger.info(f"Primary model loaded: {primary_model}")
            return True
            
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            return False
    
    async def _initialize_tools(self):
        """Initialize and register available tools."""
        try:
            # Register web search tool
            from providers.tools.enhanced_web_search_tool import EnhancedWebSearchTool
            web_search = EnhancedWebSearchTool()
            await self.register_tool("web_search", web_search)
            
            # Register Gmail tool (if configured)
            try:
                from providers.tools.gmail_connector_tool import GmailConnectorTool
                gmail_tool = GmailConnectorTool()
                if gmail_tool.is_available():
                    await self.register_tool("gmail_connector", gmail_tool)
                    logger.info("Gmail connector available")
                else:
                    logger.info("Gmail connector not configured")
            except ImportError:
                logger.info("Gmail connector not available")
            
            logger.info(f"Initialized {len(self.tool_registry.get_available_tools())} tools")
            
        except Exception as e:
            logger.error(f"Tool initialization failed: {e}")
    
    async def _initialize_conversation_manager(self):
        """Initialize conversation management."""
        try:
            # Ensure conversation manager is ready
            logger.info("Conversation manager initialized")
        except Exception as e:
            logger.error(f"Conversation manager initialization failed: {e}")
    
    async def shutdown(self) -> bool:
        """Shutdown the agent gracefully."""
        try:
            # Save any pending conversations
            for conv_id in list(self.active_conversations.keys()):
                await self.conversation_manager.save_conversation(
                    self.active_conversations[conv_id]
                )
            
            # Cleanup models
            loaded_models = self.model_manager.get_loaded_models()
            for model_name in loaded_models:
                await self.model_manager.unload_model(model_name)
            
            self.is_initialized = False
            logger.info("ChatAgent shut down gracefully")
            return True
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            return False
    
    def get_agent_name(self) -> str:
        """Get the name of the agent."""
        return self.agent_config["name"]
    
    def get_agent_description(self) -> str:
        """Get a description of the agent."""
        return self.agent_config["description"]
    
    def get_agent_version(self) -> str:
        """Get the version of the agent."""
        return self.agent_config["version"]
    
    def get_capabilities(self) -> AgentCapabilities:
        """Get the capabilities of this agent."""
        available_tools = self.tool_registry.get_available_tools()
        
        capabilities = [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.CONVERSATION,
            AgentCapability.TOOL_USAGE
        ]
        
        # Add capabilities based on available tools
        if "web_search" in available_tools:
            capabilities.append(AgentCapability.WEB_SEARCH)
        if "gmail_connector" in available_tools:
            capabilities.append(AgentCapability.EMAIL_ACCESS)
        
        return AgentCapabilities(
            supported_types=[AgentType.CONVERSATIONAL, AgentType.MULTIMODAL],
            capabilities=capabilities,
            max_context_length=self.agent_config["max_context_length"],
            supports_streaming=True,
            supports_tools=True,
            supported_languages=["en"],
            hardware_requirements={
                "min_ram_gb": 8,
                "recommended_ram_gb": 16,
                "intel_optimization": True
            }
        )
    
    async def is_ready(self) -> bool:
        """Check if the agent is ready for requests."""
        if not self.is_initialized:
            return False
        
        # Check if primary model is loaded
        loaded_models = self.model_manager.get_loaded_models()
        return self.agent_config["primary_model"] in loaded_models
    
    async def process_request(self, request: AgentRequest) -> Union[AgentResponse, AsyncIterator[AgentResponse]]:
        """Process a user request and return response(s)."""
        if not await self.is_ready():
            return AgentResponse(
                content="I'm not ready yet. Please wait a moment while I initialize.",
                success=False,
                error="Agent not ready"
            )
        
        start_time = time.time()
        self.performance_stats["total_requests"] += 1
        
        try:
            # Validate request
            if not await self.validate_request(request):
                return AgentResponse(
                    content="I couldn't understand your request. Could you please rephrase it?",
                    success=False,
                    error="Invalid request"
                )
            
            # Handle streaming vs non-streaming
            if request.execution_mode == ExecutionMode.STREAMING:
                return self._process_request_streaming(request, start_time)
            else:
                return await self._process_request_sync(request, start_time)
        
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            self.performance_stats["failed_requests"] += 1
            
            return AgentResponse(
                content="I apologize, but I encountered an error processing your request. Please try again.",
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    async def _process_request_sync(self, request: AgentRequest, start_time: float) -> AgentResponse:
        """Process request synchronously."""
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(request.conversation_id)
            
            # Add user message to conversation
            user_message = Message(
                role=MessageRole.USER,
                content=request.user_input,
                timestamp=datetime.utcnow()
            )
            conversation.add_message(user_message)
            
            # Check if tools are needed
            tool_responses = await self._check_and_execute_tools(request.user_input)
            
            # Prepare context for LLM
            context = self._prepare_llm_context(conversation, tool_responses, request.context)
            
            # Generate response using LLM
            response_content = await self._generate_llm_response(context, request)
            
            # Create assistant message
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=response_content,
                timestamp=datetime.utcnow(),
                metadata={"tools_used": list(tool_responses.keys()) if tool_responses else None}
            )
            conversation.add_message(assistant_message)
            
            # Save conversation
            await self.conversation_manager.save_conversation(conversation)
            
            # Update stats
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True, tool_responses.keys() if tool_responses else [])
            
            return AgentResponse(
                content=response_content,
                success=True,
                conversation_id=conversation.id,
                tools_used=list(tool_responses.keys()) if tool_responses else None,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Sync request processing failed: {e}")
            self.performance_stats["failed_requests"] += 1
            raise
    
    async def _process_request_streaming(self, request: AgentRequest, start_time: float) -> AsyncIterator[AgentResponse]:
        """Process request with streaming responses."""
        try:
            # Get or create conversation  
            conversation = await self._get_or_create_conversation(request.conversation_id)
            
            # Add user message
            user_message = Message(
                role=MessageRole.USER,
                content=request.user_input,
                timestamp=datetime.utcnow()
            )
            conversation.add_message(user_message)
            
            # Check tools first (non-streaming)
            tool_responses = await self._check_and_execute_tools(request.user_input)
            
            if tool_responses:
                # Send tool usage notification
                yield AgentResponse(
                    content=f"🔍 Using tools: {', '.join(tool_responses.keys())}",
                    success=True,
                    is_partial=True,
                    is_final=False,
                    tools_used=list(tool_responses.keys())
                )
            
            # Prepare context and stream LLM response
            context = self._prepare_llm_context(conversation, tool_responses, request.context)
            
            full_response = ""
            async for chunk in self._generate_llm_response_streaming(context, request):
                full_response += chunk
                yield AgentResponse(
                    content=chunk,
                    success=True,
                    is_partial=True,
                    is_final=False,
                    conversation_id=conversation.id
                )
            
            # Send final response
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=full_response,
                timestamp=datetime.utcnow(),
                metadata={"tools_used": list(tool_responses.keys()) if tool_responses else None}
            )
            conversation.add_message(assistant_message)
            
            # Save conversation
            await self.conversation_manager.save_conversation(conversation)
            
            # Update stats
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True, tool_responses.keys() if tool_responses else [])
            
            # Final response
            yield AgentResponse(
                content="",
                success=True,
                is_partial=False,
                is_final=True,
                conversation_id=conversation.id,
                tools_used=list(tool_responses.keys()) if tool_responses else None,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Streaming request processing failed: {e}")
            yield AgentResponse(
                content="An error occurred while processing your request.",
                success=False,
                error=str(e),
                is_final=True
            )
    
    async def _get_or_create_conversation(self, conversation_id: Optional[str] = None) -> Conversation:
        """Get existing conversation or create new one."""
        if conversation_id and conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]
        
        if conversation_id:
            # Try to load from storage
            conversation = await self.conversation_manager.get_conversation(conversation_id)
            if conversation:
                self.active_conversations[conversation_id] = conversation
                return conversation
        
        # Create new conversation
        conversation = await self.conversation_manager.create_conversation()
        self.active_conversations[conversation.id] = conversation
        return conversation
    
    async def _check_and_execute_tools(self, user_input: str) -> Dict[str, Any]:
        """Check if tools are needed and execute them."""
        tool_responses = {}
        user_input_lower = user_input.lower()
        
        # Check for explicit tool requests
        tool_match = re.search(r'\[TOOL:\s*(\w+)\]\s*(.+)', user_input, re.IGNORECASE)
        if tool_match:
            tool_name = tool_match.group(1)
            tool_params = tool_match.group(2)
            
            if tool_name in self.tool_registry.get_available_tools():
                result = await self._execute_tool_by_name(tool_name, tool_params)
                if result:
                    tool_responses[tool_name] = result
        
        # Check for pattern-based tool usage
        for tool_name, patterns in self.tool_patterns.items():
            if tool_name in self.tool_registry.get_available_tools():
                for pattern in patterns:
                    match = re.search(pattern, user_input_lower)
                    if match:
                        result = await self._execute_tool_by_pattern(tool_name, match, user_input)
                        if result:
                            tool_responses[tool_name] = result
                        break
        
        return tool_responses
    
    async def _execute_tool_by_name(self, tool_name: str, params_str: str) -> Optional[Dict[str, Any]]:
        """Execute tool by explicit name and parameters."""
        try:
            # Parse parameters (simplified JSON or key=value format)
            params = {}
            if params_str.strip().startswith('{'):
                params = json.loads(params_str)
            else:
                # Simple key=value parsing
                for pair in params_str.split(','):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        params[key.strip()] = value.strip()
            
            result = await self.tool_registry.execute_tool(tool_name, params)
            return result.data if result.success else None
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return None
    
    async def _execute_tool_by_pattern(self, tool_name: str, match: re.Match, user_input: str) -> Optional[Dict[str, Any]]:
        """Execute tool based on pattern match."""
        try:
            if tool_name == "web_search":
                # Extract search query
                query = match.group(-1) if match.groups() else user_input
                query = query.strip()
                
                params = {
                    "query": query,
                    "num_results": 5,
                    "search_type": "web"
                }
                
                # Check if it's a news query
                if any(word in user_input.lower() for word in ["news", "latest", "current", "today"]):
                    params["search_type"] = "news"
                    params["freshness"] = "week"
                
                result = await self.tool_registry.execute_tool(tool_name, params)
                return result.data if result.success else None
            
            elif tool_name == "gmail_connector":
                # Determine Gmail action
                if "send" in user_input.lower():
                    # Would need more sophisticated parsing for send email
                    return None
                else:
                    # Default to reading recent emails
                    params = {
                        "action": "read_recent",
                        "count": 5,
                        "include_body": False
                    }
                    
                    if "unread" in user_input.lower():
                        params["action"] = "get_unread"
                
                result = await self.tool_registry.execute_tool(tool_name, params)
                return result.data if result.success else None
            
        except Exception as e:
            logger.error(f"Pattern-based tool execution failed for {tool_name}: {e}")
            return None
    
    def _prepare_llm_context(
        self, 
        conversation: Conversation, 
        tool_responses: Optional[Dict[str, Any]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Prepare context for LLM generation."""
        # Build system prompt with available tools
        available_tools = ", ".join(self.tool_registry.get_available_tools())
        system_prompt = self.system_prompt.format(available_tools=available_tools)
        
        # Add conversation history
        context_parts = [system_prompt, "\n## Conversation History:"]
        
        # Get recent messages (limit to context window)
        recent_messages = conversation.get_recent_messages(20)  # Limit for context
        
        for message in recent_messages:
            role_name = "Human" if message.role == MessageRole.USER else "Assistant"
            context_parts.append(f"{role_name}: {message.content}")
        
        # Add tool responses if available
        if tool_responses:
            context_parts.append("\n## Tool Results:")
            for tool_name, response_data in tool_responses.items():
                context_parts.append(f"\n### {tool_name} Results:")
                if isinstance(response_data, dict):
                    context_parts.append(self._format_tool_response(tool_name, response_data))
                else:
                    context_parts.append(str(response_data))
        
        # Add additional context
        if additional_context:
            context_parts.append(f"\n## Additional Context:\n{json.dumps(additional_context, indent=2)}")
        
        context_parts.append("\nAssistant: ")
        
        return "\n".join(context_parts)
    
    def _format_tool_response(self, tool_name: str, response_data: Dict[str, Any]) -> str:
        """Format tool response for LLM context."""
        if tool_name == "web_search" or tool_name == "enhanced_web_search":
            results = response_data.get("results", [])
            formatted = []
            for i, result in enumerate(results[:3], 1):  # Limit to top 3 results
                formatted.append(
                    f"{i}. {result.get('title', 'No title')}\n"
                    f"   URL: {result.get('url', '')}\n" 
                    f"   Snippet: {result.get('snippet', 'No snippet')[:200]}..."
                )
            return "\n".join(formatted)
        
        elif tool_name == "gmail_connector":
            emails = response_data.get("emails", [])
            if emails:
                formatted = []
                for i, email in enumerate(emails[:3], 1):  # Limit to 3 emails
                    formatted.append(
                        f"{i}. From: {email.get('sender', 'Unknown')}\n"
                        f"   Subject: {email.get('subject', 'No subject')}\n"
                        f"   Date: {email.get('date', 'Unknown')}\n"
                        f"   Snippet: {email.get('snippet', 'No content')[:150]}..."
                    )
                return "\n".join(formatted)
            else:
                return "No emails found."
        
        # Default formatting
        return json.dumps(response_data, indent=2)[:500] + "..."
    
    async def _generate_llm_response(self, context: str, request: AgentRequest) -> str:
        """Generate response using the LLM."""
        try:
            # Use model manager to generate response
            model_name = self.agent_config["primary_model"]
            
            response = await self.model_manager.generate_text(
                model_name=model_name,
                prompt=context,
                max_tokens=request.max_tokens or self.agent_config["default_max_tokens"],
                temperature=request.temperature or self.agent_config["default_temperature"],
                stop_sequences=["Human:", "## Tool Results:", "## Additional Context:"]
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    async def _generate_llm_response_streaming(self, context: str, request: AgentRequest) -> AsyncIterator[str]:
        """Generate streaming response using the LLM."""
        try:
            model_name = self.agent_config["primary_model"]
            
            async for chunk in self.model_manager.generate_text_stream(
                model_name=model_name,
                prompt=context,
                max_tokens=request.max_tokens or self.agent_config["default_max_tokens"],
                temperature=request.temperature or self.agent_config["default_temperature"],
                stop_sequences=["Human:", "## Tool Results:", "## Additional Context:"]
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Streaming LLM response generation failed: {e}")
            yield "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def _update_stats(self, processing_time: float, success: bool, tools_used: List[str]):
        """Update performance statistics."""
        if success:
            self.performance_stats["successful_requests"] += 1
        else:
            self.performance_stats["failed_requests"] += 1
        
        # Update average response time
        total = self.performance_stats["total_requests"]
        current_avg = self.performance_stats["average_response_time"]
        self.performance_stats["average_response_time"] = (
            (current_avg * (total - 1) + processing_time) / total
        )
        
        # Track tool usage
        for tool in tools_used:
            if tool not in self.performance_stats["tools_used"]:
                self.performance_stats["tools_used"][tool] = 0
            self.performance_stats["tools_used"][tool] += 1
    
    async def validate_request(self, request: AgentRequest) -> bool:
        """Validate a request before processing."""
        if not request.user_input or not request.user_input.strip():
            return False
        
        # Check for reasonable input length
        if len(request.user_input) > 10000:  # 10k character limit
            return False
        
        return True
    
    # Implement IConversationalAgent methods
    async def start_conversation(self, user_id: Optional[str] = None) -> str:
        """Start a new conversation."""
        conversation = await self.conversation_manager.create_conversation(user_id=user_id)
        self.active_conversations[conversation.id] = conversation
        return conversation.id
    
    async def continue_conversation(self, conversation_id: str, user_input: str, **kwargs) -> AgentResponse:
        """Continue an existing conversation."""
        request = AgentRequest(
            user_input=user_input,
            conversation_id=conversation_id,
            **kwargs
        )
        return await self.process_request(request)
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history."""
        conversation = await self.conversation_manager.get_conversation(conversation_id)
        if not conversation:
            return []
        
        history = []
        for message in conversation.messages:
            history.append({
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                "metadata": message.metadata
            })
        
        return history
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history."""
        try:
            if conversation_id in self.active_conversations:
                del self.active_conversations[conversation_id]
            
            return await self.conversation_manager.delete_conversation(conversation_id)
        except Exception as e:
            logger.error(f"Failed to clear conversation {conversation_id}: {e}")
            return False
    
    # Implement IToolCapableAgent methods
    async def register_tool(self, tool_name: str, tool_provider: IToolProvider) -> bool:
        """Register a tool with the agent."""
        return self.tool_registry.register_tool(tool_name, tool_provider)
    
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool from the agent."""
        return self.tool_registry.unregister_tool(tool_name)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return self.tool_registry.get_available_tools()
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        result = await self.tool_registry.execute_tool(tool_name, parameters)
        return result.data if result.success else {"error": result.error}
    
    # Implement IMultimodalAgent methods  
    async def process_text(self, text: str, **kwargs) -> AgentResponse:
        """Process text input."""
        request = AgentRequest(user_input=text, **kwargs)
        return await self.process_request(request)
    
    async def process_voice(self, audio_data: bytes, **kwargs) -> AgentResponse:
        """Process voice input.""" 
        # Would need STT integration
        return AgentResponse(
            content="Voice input processing not yet implemented",
            success=False,
            error="Feature not available"
        )
    
    async def process_image(self, image_data: bytes, prompt: Optional[str] = None, **kwargs) -> AgentResponse:
        """Process image input."""
        # Would need vision model integration
        return AgentResponse(
            content="Image processing not yet implemented", 
            success=False,
            error="Feature not available"
        )
    
    async def generate_voice(self, text: str, **kwargs) -> bytes:
        """Generate voice output from text."""
        # Would need TTS integration
        raise NotImplementedError("Voice generation not yet implemented")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "agent_name": self.get_agent_name(),
            "is_ready": asyncio.run(self.is_ready()) if not self.is_initialized else self.is_initialized,
            "active_conversations": len(self.active_conversations),
            "available_tools": len(self.tool_registry.get_available_tools()),
            "performance": self.performance_stats.copy()
        }
