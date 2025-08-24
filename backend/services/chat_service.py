"""
Chat Service Implementation
Business logic for handling chat operations and conversation flow.
"""

import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
from ..interfaces.services import IChatService
from ..interfaces.repositories import IConversationRepository, IMessageRepository
from ..interfaces.providers import IModelProvider, IToolProvider
from ..models.domain import (
    ChatRequest, ChatResponse, Message, MessageRole, 
    Conversation, ConversationStatus
)


class ChatService(IChatService):
    """Implementation of chat service with conversation management."""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        message_repo: IMessageRepository,
        model_provider: IModelProvider,
        tool_provider: Optional[IToolProvider] = None
    ):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.model_provider = model_provider
        self.tool_provider = tool_provider

    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return response."""
        start_time = time.time()
        tools_used = []

        try:
            # Get or create conversation
            conversation_id = await self._ensure_conversation(request.conversation_id)
            
            # Create user message
            user_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=request.message,
                timestamp=datetime.now()
            )
            
            # Save user message
            await self.message_repo.create_message(user_message)
            
            # Get conversation context
            context = await self.get_conversation_context(conversation_id)
            
            # Check if tools should be used
            tool_results = []
            if request.use_tools and self.tool_provider and self._should_use_tools(request.message):
                tool_results = await self._execute_tools(request.message)
                tools_used = [result["tool_name"] for result in tool_results]
            
            # Build prompt with context and tool results
            prompt = self._build_prompt(context, tool_results)
            
            # Generate response
            response_text = await self.model_provider.generate(
                prompt=prompt,
                model_id="default",  # This should come from config
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Create assistant message
            assistant_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                timestamp=datetime.now(),
                tools_used=tools_used,
                processing_time=time.time() - start_time
            )
            
            # Save assistant message
            await self.message_repo.create_message(assistant_message)
            
            # Update conversation
            await self._update_conversation_stats(conversation_id)
            
            return ChatResponse(
                message=response_text,
                conversation_id=conversation_id,
                processing_time=time.time() - start_time,
                tools_used=tools_used,
                model_used="default"  # This should come from config
            )
            
        except Exception as e:
            # In a real implementation, you'd log this error
            raise Exception(f"Failed to process chat request: {str(e)}")

    async def stream_chat_response(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """Stream chat response tokens."""
        conversation_id = await self._ensure_conversation(request.conversation_id)
        
        # Create user message
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=request.message,
            timestamp=datetime.now()
        )
        await self.message_repo.create_message(user_message)
        
        # Get context and build prompt
        context = await self.get_conversation_context(conversation_id)
        prompt = self._build_prompt(context)
        
        # Stream response
        response_parts = []
        async for token in self.model_provider.stream_generate(
            prompt=prompt,
            model_id="default",
            max_tokens=request.max_tokens,
            temperature=request.temperature
        ):
            response_parts.append(token)
            yield token
        
        # Save complete assistant message
        complete_response = "".join(response_parts)
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=complete_response,
            timestamp=datetime.now()
        )
        await self.message_repo.create_message(assistant_message)
        await self._update_conversation_stats(conversation_id)

    async def get_conversation_context(
        self, conversation_id: str, limit: int = 10
    ) -> List[Message]:
        """Get recent conversation context."""
        return await self.message_repo.get_messages_by_conversation(
            conversation_id, limit=limit
        )

    async def _ensure_conversation(self, conversation_id: Optional[str]) -> str:
        """Ensure conversation exists, create if needed."""
        if conversation_id:
            conversation = await self.conversation_repo.get_conversation_by_id(conversation_id)
            if conversation:
                return conversation_id
        
        # Create new conversation
        new_conversation = Conversation(
            id=str(uuid.uuid4()),
            title="New Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=ConversationStatus.ACTIVE,
            message_count=0
        )
        
        await self.conversation_repo.create_conversation(new_conversation)
        return new_conversation.id

    async def _update_conversation_stats(self, conversation_id: str):
        """Update conversation statistics."""
        conversation = await self.conversation_repo.get_conversation_by_id(conversation_id)
        if conversation:
            # Count messages
            messages = await self.message_repo.get_messages_by_conversation(conversation_id)
            conversation.message_count = len(messages)
            conversation.updated_at = datetime.now()
            
            # Update title if it's still default and we have messages
            if conversation.title == "New Conversation" and messages:
                user_messages = [m for m in messages if m.role == MessageRole.USER]
                if user_messages:
                    # Use first user message as title (truncated)
                    title = user_messages[0].content[:50]
                    if len(user_messages[0].content) > 50:
                        title += "..."
                    conversation.title = title
            
            await self.conversation_repo.update_conversation(conversation)

    def _should_use_tools(self, message: str) -> bool:
        """Determine if tools should be used for this message."""
        # Simple heuristic - in a real implementation, this could be more sophisticated
        tool_keywords = [
            "search", "find", "look up", "what's", "latest", "news", 
            "weather", "email", "gmail", "send", "calendar"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in tool_keywords)

    async def _execute_tools(self, message: str) -> List[Dict[str, Any]]:
        """Execute appropriate tools based on the message."""
        if not self.tool_provider:
            return []
        
        # This is a simplified implementation
        # In a real system, you'd have more sophisticated tool selection
        results = []
        
        try:
            if any(word in message.lower() for word in ["search", "find", "look up"]):
                # Extract search query (simplified)
                query = message  # In reality, you'd extract the actual query
                result = await self.tool_provider.execute({
                    "action": "web_search",
                    "query": query,
                    "max_results": 3
                })
                results.append({
                    "tool_name": "web_search",
                    "result": result,
                    "success": True
                })
        except Exception as e:
            results.append({
                "tool_name": "web_search",
                "result": None,
                "success": False,
                "error": str(e)
            })
        
        return results

    def _build_prompt(
        self, 
        context: List[Message], 
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build prompt for the language model."""
        prompt_parts = []
        
        # System message
        prompt_parts.append(
            "You are an intelligent virtual assistant optimized for Intel hardware. "
            "You are helpful, harmless, and honest. Provide accurate and concise responses."
        )
        
        # Add tool results if available
        if tool_results:
            prompt_parts.append("\nAdditional information from tools:")
            for result in tool_results:
                if result["success"] and result["result"]:
                    prompt_parts.append(f"- {result['tool_name']}: {result['result']}")
        
        # Add conversation context
        if context:
            prompt_parts.append("\nConversation history:")
            for message in context[-10:]:  # Last 10 messages
                role = "Human" if message.role == MessageRole.USER else "Assistant"
                prompt_parts.append(f"{role}: {message.content}")
        
        prompt_parts.append("\nAssistant:")
        
        return "\n".join(prompt_parts)