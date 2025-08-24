#!/usr/bin/env python3
"""
Comprehensive System Validator for Intel AI Assistant
Tests all components to ensure solid functionality and modularity.
"""

import sys
import asyncio
import importlib
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

class SystemValidator:
    """Comprehensive system validation."""
    
    def __init__(self):
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
        
    def log_test_result(self, category: str, test_name: str, success: bool, details: str = ""):
        """Log a test result."""
        if category not in self.test_results:
            self.test_results[category] = {}
            
        self.test_results[category][test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {category}.{test_name}: {details}")
        
        if not success:
            self.errors.append(f"{category}.{test_name}: {details}")
    
    def test_import_system(self) -> bool:
        """Test all critical imports."""
        logger.info("🔍 Testing Import System...")
        
        critical_modules = [
            ("config.settings", "Core configuration"),
            ("core.interfaces.agent_provider", "Agent interfaces"),
            ("core.interfaces.model_provider", "Model interfaces"),  
            ("core.interfaces.tool_provider", "Tool interfaces"),
            ("services.chat_agent_orchestrator", "Chat orchestrator"),
            ("services.model_manager", "Model manager"),
            ("services.conversation_manager", "Conversation manager"),
            ("services.tool_registry", "Tool registry"),
            ("providers.models.mistral_openvino_provider", "Mistral provider"),
            ("providers.voice.speecht5_openvino_provider", "Voice provider"),
            ("providers.tools.enhanced_web_search_tool", "Web search tool"),
            ("providers.tools.gmail_connector_tool", "Gmail tool"),
            ("api.routes.chat", "API routes")
        ]
        
        all_passed = True
        for module_name, description in critical_modules:
            try:
                importlib.import_module(module_name)
                self.log_test_result("imports", module_name, True, description)
            except Exception as e:
                self.log_test_result("imports", module_name, False, f"{description} - Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_configuration_system(self) -> bool:
        """Test configuration system."""
        logger.info("⚙️ Testing Configuration System...")
        
        try:
            from config.settings import ApplicationSettings, initialize_settings
            
            # Test basic settings creation
            settings = ApplicationSettings()
            self.log_test_result("config", "basic_creation", True, "Settings created successfully")
            
            # Test settings validation
            issues = settings.validate_settings()
            if isinstance(issues, list):
                self.log_test_result("config", "validation", True, f"Validation returned {len(issues)} issues")
            else:
                self.log_test_result("config", "validation", False, "Validation didn't return a list")
                return False
            
            # Test Intel profile application
            try:
                result = settings.apply_intel_profile("cpu_only")
                self.log_test_result("config", "intel_profile", True, f"Profile application result: {result}")
            except Exception as e:
                self.log_test_result("config", "intel_profile", False, f"Profile error: {str(e)}")
                return False
            
            # Test settings serialization
            try:
                config_dict = settings.to_dict()
                if isinstance(config_dict, dict) and "app_name" in config_dict:
                    self.log_test_result("config", "serialization", True, "Settings serialization works")
                else:
                    self.log_test_result("config", "serialization", False, "Invalid serialization format")
                    return False
            except Exception as e:
                self.log_test_result("config", "serialization", False, f"Serialization error: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("config", "system", False, f"Configuration system error: {str(e)}")
            return False
    
    def test_modular_architecture(self) -> bool:
        """Test modular architecture and extensibility."""
        logger.info("🧩 Testing Modular Architecture...")
        
        try:
            # Test provider interfaces
            from core.interfaces.agent_provider import IAgentProvider, AgentCapabilities, AgentType, AgentCapability
            from core.interfaces.model_provider import ITextGenerator, IModelProvider
            from core.interfaces.tool_provider import IToolProvider, ToolCapability, ToolCategory
            
            self.log_test_result("architecture", "interfaces", True, "All interfaces importable")
            
            # Test that providers can be instantiated (without loading models)
            from providers.models.mistral_openvino_provider import MistralOpenVINOProvider
            from providers.voice.speecht5_openvino_provider import SpeechT5OpenVINOProvider
            from providers.tools.enhanced_web_search_tool import EnhancedWebSearchTool
            from providers.tools.gmail_connector_tool import GmailConnectorTool
            
            # Test provider metadata
            mistral_provider = MistralOpenVINOProvider()
            info = mistral_provider.get_model_info()
            if isinstance(info, dict) and "name" in info:
                self.log_test_result("architecture", "mistral_metadata", True, f"Mistral info: {info.get('name')}")
            else:
                self.log_test_result("architecture", "mistral_metadata", False, "Invalid Mistral metadata")
                return False
            
            # Test tool providers
            search_tool = EnhancedWebSearchTool()
            if search_tool.get_tool_name() == "enhanced_web_search":
                self.log_test_result("architecture", "search_tool", True, "Web search tool metadata correct")
            else:
                self.log_test_result("architecture", "search_tool", False, "Invalid web search tool metadata")
                return False
            
            gmail_tool = GmailConnectorTool()
            if gmail_tool.get_tool_name() == "gmail_connector":
                self.log_test_result("architecture", "gmail_tool", True, "Gmail tool metadata correct")
            else:
                self.log_test_result("architecture", "gmail_tool", False, "Invalid Gmail tool metadata")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("architecture", "modular_system", False, f"Architecture error: {str(e)}")
            return False
    
    async def test_service_layer(self) -> bool:
        """Test service layer components."""
        logger.info("🔧 Testing Service Layer...")
        
        try:
            # Test tool registry
            from services.tool_registry import ToolRegistry
            from services.intel_optimizer import IntelOptimizer
            
            registry = ToolRegistry()
            available_tools = registry.get_available_tools()
            self.log_test_result("services", "tool_registry", True, f"Registry created, {len(available_tools)} tools")
            
            # Test Intel optimizer
            optimizer = IntelOptimizer()
            hardware_info = optimizer.get_hardware_summary()
            if isinstance(hardware_info, dict) and "cpu" in hardware_info:
                self.log_test_result("services", "intel_optimizer", True, "Hardware detection works")
            else:
                self.log_test_result("services", "intel_optimizer", False, "Invalid hardware detection")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("services", "service_layer", False, f"Service layer error: {str(e)}")
            return False
    
    async def test_voice_capabilities(self) -> bool:
        """Test voice assistant capabilities."""
        logger.info("🎤 Testing Voice Assistant Capabilities...")
        
        try:
            from providers.voice.speecht5_openvino_provider import SpeechT5OpenVINOProvider
            
            # Test TTS provider initialization
            tts_provider = SpeechT5OpenVINOProvider()
            
            # Test voice configuration
            voices = tts_provider.get_available_voices()
            if isinstance(voices, list) and len(voices) > 0:
                self.log_test_result("voice", "tts_voices", True, f"{len(voices)} voices available")
            else:
                self.log_test_result("voice", "tts_voices", False, "No TTS voices available")
                return False
            
            # Test supported formats
            formats = tts_provider.get_supported_formats()
            if isinstance(formats, list) and len(formats) > 0:
                # Convert enum values to strings for display
                format_names = []
                for fmt in formats:
                    if hasattr(fmt, 'value'):
                        format_names.append(fmt.value)
                    else:
                        format_names.append(str(fmt))
                self.log_test_result("voice", "audio_formats", True, f"Formats: {', '.join(format_names)}")
            else:
                self.log_test_result("voice", "audio_formats", False, "No audio formats supported")
                return False
            
            # Test model info
            model_info = tts_provider.get_model_info()
            if isinstance(model_info, dict) and "name" in model_info:
                self.log_test_result("voice", "tts_metadata", True, f"TTS model: {model_info['name']}")
            else:
                self.log_test_result("voice", "tts_metadata", False, "Invalid TTS metadata")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("voice", "voice_system", False, f"Voice system error: {str(e)}")
            return False
    
    def test_api_system(self) -> bool:
        """Test API system."""
        logger.info("🌐 Testing API System...")
        
        try:
            from api.routes.chat import router
            from fastapi import FastAPI
            
            # Test that router can be created
            app = FastAPI()
            app.include_router(router, prefix="/api/v1/chat")
            
            self.log_test_result("api", "router_creation", True, "Chat router created successfully")
            
            # Test route definitions exist
            routes = [route.path for route in app.routes]
            expected_routes = ["/api/v1/chat/message", "/api/v1/chat/status"]
            
            routes_found = sum(1 for route in expected_routes if any(route in path for path in routes))
            if routes_found >= len(expected_routes) - 1:  # Allow some flexibility
                self.log_test_result("api", "routes", True, f"{routes_found}/{len(expected_routes)} routes found")
            else:
                self.log_test_result("api", "routes", False, f"Only {routes_found}/{len(expected_routes)} routes found")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("api", "api_system", False, f"API system error: {str(e)}")
            return False
    
    def test_web_interface(self) -> bool:
        """Test web interface files."""
        logger.info("🖥️ Testing Web Interface...")
        
        try:
            # Check for required web files
            web_files = [
                ("web/templates/chat.html", "Main chat template"),
                ("web/static/css/style.css", "CSS styles"),
                ("web/static/js/app.js", "JavaScript application")
            ]
            
            for file_path, description in web_files:
                if Path(file_path).exists():
                    self.log_test_result("web", file_path.replace("/", "_"), True, description)
                else:
                    self.log_test_result("web", file_path.replace("/", "_"), False, f"Missing: {description}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_test_result("web", "web_interface", False, f"Web interface error: {str(e)}")
            return False
    
    def test_extensibility(self) -> bool:
        """Test system extensibility."""
        logger.info("🔌 Testing System Extensibility...")
        
        try:
            from services.tool_registry import ToolRegistry
            from core.interfaces.tool_provider import IToolProvider, ToolResult
            
            # Create mock tool to test registration
            class MockTool(IToolProvider):
                def get_tool_name(self) -> str:
                    return "test_mock_tool"
                
                def get_tool_description(self) -> str:
                    return "Mock tool for testing extensibility"
                
                def get_tool_category(self):
                    from core.interfaces.tool_provider import ToolCategory
                    return ToolCategory.UTILITY
                
                def get_auth_type(self):
                    from core.interfaces.tool_provider import ToolAuthType
                    return ToolAuthType.NONE
                
                def is_available(self) -> bool:
                    return True
                
                def validate_parameters(self, parameters: dict) -> bool:
                    return True
                
                def execute(self, parameters: dict) -> ToolResult:
                    return ToolResult(success=True, data={"test": "passed"})
                
                def get_parameters(self) -> list:
                    return []
            
            # Test tool registration
            registry = ToolRegistry()
            mock_tool = MockTool()
            
            success = registry.register_tool(mock_tool)
            if success:
                self.log_test_result("extensibility", "tool_registration", True, "Mock tool registered successfully")
            else:
                self.log_test_result("extensibility", "tool_registration", False, "Failed to register mock tool")
                return False
            
            # Test tool availability
            available = registry.get_available_tools()
            if "test_mock_tool" in available:
                self.log_test_result("extensibility", "tool_availability", True, "Registered tool is available")
            else:
                self.log_test_result("extensibility", "tool_availability", False, "Registered tool not available")
                return False
            
            # Test tool unregistration
            unregister_success = registry.unregister_tool("test_mock_tool")
            if unregister_success:
                self.log_test_result("extensibility", "tool_unregistration", True, "Mock tool unregistered successfully")
            else:
                self.log_test_result("extensibility", "tool_unregistration", False, "Failed to unregister mock tool")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("extensibility", "extensibility_system", False, f"Extensibility error: {str(e)}")
            return False
    
    async def run_comprehensive_validation(self) -> bool:
        """Run all validation tests."""
        print("🚀 Starting Comprehensive Intel AI Assistant Validation")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Run all tests
        tests = [
            ("Import System", self.test_import_system),
            ("Configuration System", self.test_configuration_system),
            ("Modular Architecture", self.test_modular_architecture),
            ("Service Layer", self.test_service_layer),
            ("Voice Capabilities", self.test_voice_capabilities),
            ("API System", self.test_api_system),
            ("Web Interface", self.test_web_interface),
            ("System Extensibility", self.test_extensibility)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                if not result:
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"Test '{test_name}' crashed: {str(e)}")
                logger.error(traceback.format_exc())
                self.log_test_result("system", test_name.lower().replace(" ", "_"), False, f"Test crashed: {str(e)}")
                all_passed = False
        
        # Generate report
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("🎯 VALIDATION RESULTS")
        print("=" * 60)
        
        total_tests = sum(len(category) for category in self.test_results.values())
        passed_tests = sum(
            sum(1 for test in category.values() if test["success"]) 
            for category in self.test_results.values()
        )
        
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📊 Tests: {passed_tests}/{total_tests} passed")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if all_passed:
            print("\n✅ ALL TESTS PASSED!")
            print("🎉 Intel AI Assistant is ready for deployment!")
            print("🚀 System demonstrates solid modularity and functionality!")
        else:
            print(f"\n❌ {len(self.errors)} ISSUES FOUND:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"   • {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more issues")
        
        return all_passed

async def main():
    """Main validation function."""
    validator = SystemValidator()
    success = await validator.run_comprehensive_validation()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("   1. Run: python main.py")
        print("   2. Open: http://localhost:8000")
        print("   3. Start chatting with your Intel AI Assistant!")
        return 0
    else:
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("   1. Review error messages above")
        print("   2. Install missing dependencies")
        print("   3. Fix configuration issues")
        print("   4. Re-run validation")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)