#!/usr/bin/env python3
"""
Comprehensive Test Suite for Intel AI Assistant
Tests all components including models, tools, chat agent, and system integration.
"""

import asyncio
import pytest
import json
import time
import logging
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our components
from services.chat_agent_orchestrator import ChatAgentOrchestrator
from services.model_manager import ModelManager
from services.conversation_manager import ConversationManager
from services.intel_optimizer import IntelOptimizer
from services.tool_registry import ToolRegistry

from providers.models.mistral_openvino_provider import MistralOpenVINOProvider
from providers.voice.speecht5_openvino_provider import SpeechT5OpenVINOProvider
from providers.tools.enhanced_web_search_tool import EnhancedWebSearchTool
from providers.tools.gmail_connector_tool import GmailConnectorTool

from config.settings import ApplicationSettings, initialize_settings

logger = logging.getLogger(__name__)

class TestIntelOptimizer:
    """Test Intel hardware optimization and detection."""
    
    @pytest.fixture
    def optimizer(self):
        return IntelOptimizer()
    
    def test_hardware_detection(self, optimizer):
        """Test hardware detection capabilities."""
        hardware = optimizer.get_hardware_summary()
        
        assert "cpu" in hardware
        assert "arc_gpu" in hardware
        assert "npu" in hardware
        
        # Check basic structure
        for component in ["cpu", "arc_gpu", "npu"]:
            assert "available" in hardware[component]
            assert "performance" in hardware[component]
    
    def test_device_selection(self, optimizer):
        """Test optimal device selection logic."""
        # Test for different model types
        device = optimizer.select_optimal_device("test-llm", "llm")
        assert device in ["CPU", "GPU", "NPU", "AUTO"]
        
        device = optimizer.select_optimal_device("test-tts", "tts")
        assert device in ["CPU", "GPU", "NPU", "AUTO"]
    
    def test_model_config_generation(self, optimizer):
        """Test model configuration generation."""
        config = optimizer.get_model_config("test-model", "CPU")
        
        assert isinstance(config, dict)
        assert "num_threads" in config or "batch_size" in config

class TestMistralProvider:
    """Test Mistral-7B OpenVINO provider."""
    
    @pytest.fixture
    def provider(self):
        return MistralOpenVINOProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider can be initialized."""
        assert provider.model is None
        assert provider.tokenizer is None
        assert not provider.is_loaded()
    
    def test_device_support(self, provider):
        """Test device support detection."""
        supported_devices = provider.get_supported_devices()
        assert len(supported_devices) > 0
        assert any(device.value == "CPU" for device in supported_devices)
    
    def test_model_info(self, provider):
        """Test model information retrieval."""
        info = provider.get_model_info()
        
        assert "name" in info
        assert "provider" in info
        assert "quantization" in info
        assert info["name"] == "Mistral-7B-Instruct-v0.3"

class TestSpeechT5Provider:
    """Test SpeechT5 TTS provider."""
    
    @pytest.fixture
    def provider(self):
        return SpeechT5OpenVINOProvider()
    
    def test_provider_initialization(self, provider):
        """Test TTS provider initialization."""
        assert provider.model is None
        assert provider.processor is None
        assert not provider.is_model_loaded
    
    def test_voice_configuration(self, provider):
        """Test voice configuration."""
        voices = provider.get_available_voices()
        assert len(voices) > 0
        
        for voice in voices:
            assert "id" in voice
            assert "name" in voice
            assert "gender" in voice
    
    def test_supported_formats(self, provider):
        """Test supported audio formats."""
        formats = provider.get_supported_formats()
        assert len(formats) > 0

class TestWebSearchTool:
    """Test enhanced web search tool."""
    
    @pytest.fixture
    def search_tool(self):
        return EnhancedWebSearchTool()
    
    def test_tool_metadata(self, search_tool):
        """Test tool metadata and configuration."""
        assert search_tool.get_tool_name() == "enhanced_web_search"
        assert search_tool.get_tool_description()
        assert search_tool.is_available()
    
    def test_parameter_validation(self, search_tool):
        """Test parameter validation."""
        # Valid parameters
        valid_params = {
            "query": "test search",
            "num_results": 5,
            "search_type": "web"
        }
        assert search_tool.validate_parameters(valid_params)
        
        # Invalid parameters
        invalid_params = {
            "query": "",  # Empty query
            "num_results": 0  # Invalid count
        }
        assert not search_tool.validate_parameters(invalid_params)
    
    def test_search_engines(self, search_tool):
        """Test search engine availability."""
        # Should have at least DuckDuckGo available
        engines = search_tool.search_engines
        assert "duckduckgo" in engines
        assert engines["duckduckgo"]["requires_auth"] is False

class TestGmailTool:
    """Test Gmail connector tool."""
    
    @pytest.fixture
    def gmail_tool(self):
        return GmailConnectorTool()
    
    def test_tool_metadata(self, gmail_tool):
        """Test Gmail tool metadata."""
        assert gmail_tool.get_tool_name() == "gmail_connector"
        assert gmail_tool.get_tool_description()
        assert gmail_tool.get_tool_category().value == "communication"
    
    def test_parameter_structure(self, gmail_tool):
        """Test parameter structure."""
        params = gmail_tool.get_parameters()
        assert len(params) > 0
        
        # Should have action parameter
        action_param = next((p for p in params if p.name == "action"), None)
        assert action_param is not None
        assert action_param.required
    
    def test_oauth_configuration(self, gmail_tool):
        """Test OAuth configuration."""
        assert gmail_tool.get_auth_type().value == "oauth"

class TestToolRegistry:
    """Test tool registry and management."""
    
    @pytest.fixture
    def registry(self):
        return ToolRegistry()
    
    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool for testing."""
        tool = Mock()
        tool.get_tool_name.return_value = "mock_tool"
        tool.get_tool_description.return_value = "Mock tool for testing"
        tool.is_available.return_value = True
        tool.validate_parameters.return_value = True
        tool.execute.return_value = Mock(success=True, data={"result": "test"})
        return tool
    
    def test_tool_registration(self, registry, mock_tool):
        """Test tool registration and management."""
        # Register tool
        success = registry.register_tool("mock_tool", mock_tool)
        assert success
        
        # Check availability
        available_tools = registry.get_available_tools()
        assert "mock_tool" in available_tools
        
        # Unregister tool
        success = registry.unregister_tool("mock_tool")
        assert success
        
        available_tools = registry.get_available_tools()
        assert "mock_tool" not in available_tools

class TestConversationManager:
    """Test conversation management."""
    
    @pytest.fixture
    def conv_manager(self):
        # Use in-memory storage for testing
        from providers.storage.sqlite_provider import SQLiteProvider
        storage = SQLiteProvider()
        storage.connect(":memory:")  # In-memory database
        return ConversationManager(storage)
    
    @pytest.mark.asyncio
    async def test_conversation_creation(self, conv_manager):
        """Test conversation creation."""
        conversation = await conv_manager.create_conversation()
        
        assert conversation is not None
        assert conversation.id is not None
        assert len(conversation.messages) == 0
    
    @pytest.mark.asyncio
    async def test_message_handling(self, conv_manager):
        """Test message addition and retrieval."""
        from core.models.conversation import Message, MessageRole
        from datetime import datetime
        
        conversation = await conv_manager.create_conversation()
        
        # Add messages
        user_msg = Message(
            role=MessageRole.USER,
            content="Hello, AI!",
            timestamp=datetime.utcnow()
        )
        conversation.add_message(user_msg)
        
        assistant_msg = Message(
            role=MessageRole.ASSISTANT,
            content="Hello! How can I help you?",
            timestamp=datetime.utcnow()
        )
        conversation.add_message(assistant_msg)
        
        # Save conversation
        await conv_manager.save_conversation(conversation)
        
        # Retrieve conversation
        retrieved = await conv_manager.get_conversation(conversation.id)
        assert retrieved is not None
        assert len(retrieved.messages) == 2

class TestModelManager:
    """Test model management and lifecycle."""
    
    @pytest.fixture
    def model_manager(self):
        optimizer = IntelOptimizer()
        return ModelManager(optimizer)
    
    def test_provider_registration(self, model_manager):
        """Test model provider registration."""
        mock_provider = Mock()
        mock_provider.load_model.return_value = True
        mock_provider.is_loaded.return_value = True
        mock_provider.get_model_info.return_value = {"name": "test"}
        
        model_manager.register_provider("test", mock_provider)
        assert "test" in model_manager._providers

class TestChatAgentOrchestrator:
    """Test the main chat agent orchestrator."""
    
    @pytest.fixture
    async def chat_agent(self):
        """Create a chat agent with mocked dependencies."""
        # Mock components
        model_manager = Mock(spec=ModelManager)
        model_manager.load_model = AsyncMock(return_value=True)
        model_manager.get_loaded_models = Mock(return_value=["mistral-7b-instruct"])
        model_manager.generate_text = AsyncMock(return_value="Hello! I'm your AI assistant.")
        
        conv_manager = Mock(spec=ConversationManager)
        conv_manager.create_conversation = AsyncMock()
        conv_manager.save_conversation = AsyncMock()
        
        tool_registry = Mock(spec=ToolRegistry)
        tool_registry.get_available_tools = Mock(return_value=["web_search"])
        
        agent = ChatAgentOrchestrator(model_manager, conv_manager, tool_registry)
        
        # Initialize with mock config
        await agent.initialize({
            "primary_model": "mistral-7b-instruct",
            "tts_model": "speecht5-tts"
        })
        
        return agent
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, chat_agent):
        """Test agent initialization."""
        assert chat_agent.is_initialized
        assert await chat_agent.is_ready()
        
        capabilities = chat_agent.get_capabilities()
        assert capabilities is not None
        assert len(capabilities.capabilities) > 0
    
    @pytest.mark.asyncio
    async def test_text_processing(self, chat_agent):
        """Test basic text processing."""
        from core.interfaces.agent_provider import AgentRequest
        
        request = AgentRequest(
            user_input="Hello, AI assistant!",
            max_tokens=50,
            temperature=0.7
        )
        
        response = await chat_agent.process_request(request)
        assert response is not None
        assert response.success
        assert response.content

class TestApplicationSettings:
    """Test application configuration and settings."""
    
    def test_settings_initialization(self):
        """Test settings initialization."""
        settings = ApplicationSettings()
        
        assert settings.app_name
        assert settings.app_version
        assert settings.model is not None
        assert settings.voice is not None
    
    def test_intel_profile_application(self):
        """Test Intel profile application."""
        settings = ApplicationSettings()
        
        # Test profile application
        success = settings.apply_intel_profile("cpu_only")
        # Should not fail even if profile doesn't exist
        assert isinstance(success, bool)
    
    def test_settings_validation(self):
        """Test settings validation."""
        settings = ApplicationSettings()
        
        issues = settings.validate_settings()
        # Should be a list (empty if no issues)
        assert isinstance(issues, list)

class TestSystemIntegration:
    """Test full system integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_conversation(self):
        """Test complete conversation flow."""
        # This would test the full pipeline from user input to response
        # Currently mocked due to model loading requirements
        
        # Mock the main components
        with patch('services.model_manager.ModelManager') as MockModelManager:
            with patch('services.conversation_manager.ConversationManager') as MockConvManager:
                
                # Configure mocks
                mock_model_mgr = MockModelManager.return_value
                mock_model_mgr.load_model = AsyncMock(return_value=True)
                mock_model_mgr.get_loaded_models = Mock(return_value=["mistral-7b-instruct"])
                
                mock_conv_mgr = MockConvManager.return_value
                
                # Test conversation
                agent = ChatAgentOrchestrator(mock_model_mgr, mock_conv_mgr)
                await agent.initialize({})
                
                assert await agent.is_ready()
    
    def test_configuration_loading(self):
        """Test configuration loading and validation."""
        # Test default configuration
        settings = initialize_settings()
        assert settings is not None
        
        # Validate configuration
        issues = settings.validate_settings()
        assert isinstance(issues, list)
    
    def test_hardware_optimization_integration(self):
        """Test Intel hardware optimization integration."""
        optimizer = IntelOptimizer()
        settings = ApplicationSettings()
        
        # Test that hardware detection works
        hardware = optimizer.get_hardware_summary()
        assert hardware is not None
        
        # Test configuration generation
        config = optimizer.get_model_config("test-model", "CPU")
        assert isinstance(config, dict)

class TestPerformanceMetrics:
    """Test performance monitoring and metrics."""
    
    def test_performance_tracking(self):
        """Test performance metrics collection."""
        # Mock components
        optimizer = IntelOptimizer()
        model_manager = ModelManager(optimizer)
        
        # Check stats structure
        stats = model_manager._inference_stats
        assert isinstance(stats, dict)
    
    def test_tool_performance_tracking(self):
        """Test tool performance tracking."""
        search_tool = EnhancedWebSearchTool()
        stats = search_tool.get_stats()
        
        assert "tool_name" in stats
        assert "performance" in stats

def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🧪 Starting Comprehensive Intel AI Assistant Tests")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run pytest with detailed output
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--color=yes",
        "-x"  # Stop on first failure
    ]
    
    # Add coverage if available
    try:
        import pytest_cov
        pytest_args.extend(["--cov=services", "--cov=providers", "--cov=core"])
    except ImportError:
        print("⚠️  pytest-cov not available, skipping coverage")
    
    try:
        exit_code = pytest.main(pytest_args)
        
        if exit_code == 0:
            print("\n✅ All tests passed successfully!")
            print("🎯 Intel AI Assistant is ready for deployment")
        else:
            print(f"\n❌ Some tests failed (exit code: {exit_code})")
            print("🔧 Please review the test output and fix issues")
            
        return exit_code
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

def validate_system_requirements():
    """Validate system requirements and dependencies."""
    print("🔍 Validating System Requirements...")
    
    requirements = {
        "Python": (3, 8),
        "RAM": "8GB minimum, 16GB recommended",
        "Storage": "10GB free space for models",
        "OS": "Windows 11 with Intel hardware"
    }
    
    issues = []
    
    # Check Python version
    if sys.version_info < requirements["Python"]:
        issues.append(f"Python {requirements['Python'][0]}.{requirements['Python'][1]}+ required")
    
    # Check available packages
    required_packages = [
        "fastapi", "uvicorn", "pydantic", "transformers", 
        "optimum", "openvino", "torch", "numpy"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            issues.append(f"Missing package: {package}")
    
    if issues:
        print("❌ System requirements not met:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ System requirements satisfied")
        return True

if __name__ == "__main__":
    # Validate system first
    if validate_system_requirements():
        # Run comprehensive tests
        exit_code = run_comprehensive_tests()
        sys.exit(exit_code)
    else:
        print("\n🚫 Please install missing requirements and try again")
        sys.exit(1)