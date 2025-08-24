"""
LangChain Integration for OpenVINO GenAI Server
Demonstrates how to use the local OpenVINO server with LangChain.
"""

import os
from typing import Optional, List, Dict, Any
from langchain.llms.base import LLM
from langchain.schema import Generation, LLMResult
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chat_models.base import BaseChatModel
from langchain.schema.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.schema import ChatResult, ChatGeneration
import requests
import json

class OpenVINOGenAI(LLM):
    """LangChain LLM wrapper for OpenVINO GenAI server."""
    
    base_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    model_name: str = "ov-qwen2.5-7b-int4"
    temperature: float = 0.2
    max_tokens: int = 256
    
    @property
    def _llm_type(self) -> str:
        return "openvino_genai"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the OpenVINO GenAI server."""
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "prompt": prompt,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["text"]
        except Exception as e:
            raise RuntimeError(f"Error calling OpenVINO GenAI server: {e}")

class OpenVINOGenAIChat(BaseChatModel):
    """LangChain Chat Model wrapper for OpenVINO GenAI server."""
    
    base_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    model_name: str = "ov-qwen2.5-7b-int4"
    temperature: float = 0.2
    max_tokens: int = 256
    
    @property
    def _llm_type(self) -> str:
        return "openvino_genai_chat"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion using OpenVINO GenAI server."""
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Convert LangChain messages to OpenAI format
        openai_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
        
        payload = {
            "model": self.model_name,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            message_content = result["choices"][0]["message"]["content"]
            message = AIMessage(content=message_content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            raise RuntimeError(f"Error calling OpenVINO GenAI server: {e}")

# Example usage functions
def example_simple_llm():
    """Example using the simple LLM interface."""
    print("🔗 LangChain Simple LLM Example")
    
    llm = OpenVINOGenAI(
        base_url="http://localhost:8000",
        temperature=0.7,
        max_tokens=100
    )
    
    prompt = "Explain what OpenVINO is in simple terms."
    response = llm(prompt)
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")

def example_chat_model():
    """Example using the chat model interface."""
    print("\n💬 LangChain Chat Model Example")
    
    chat = OpenVINOGenAIChat(
        base_url="http://localhost:8000",
        temperature=0.7,
        max_tokens=150
    )
    
    messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        HumanMessage(content="What are the benefits of using local AI models?")
    ]
    
    result = chat(messages)
    print(f"Messages: {[msg.content for msg in messages]}")
    print(f"Response: {result.content}")

def example_with_chains():
    """Example using LangChain chains."""
    print("\n⛓️  LangChain Chains Example")
    
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    
    llm = OpenVINOGenAI(base_url="http://localhost:8000")
    
    prompt = PromptTemplate(
        input_variables=["topic"],
        template="Write a brief explanation about {topic} in 2-3 sentences."
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    topics = ["machine learning", "quantum computing", "blockchain"]
    
    for topic in topics:
        result = chain.run(topic=topic)
        print(f"Topic: {topic}")
        print(f"Explanation: {result}\n")

if __name__ == "__main__":
    print("🚀 OpenVINO GenAI LangChain Integration Examples")
    print("Make sure your OpenVINO GenAI server is running on http://localhost:8000")
    
    try:
        # Test server connectivity
        response = requests.get("http://localhost:8000/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            
            example_simple_llm()
            example_chat_model()
            example_with_chains()
            
        else:
            print("❌ Server is not responding correctly")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the server first:")
        print("   python start_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")