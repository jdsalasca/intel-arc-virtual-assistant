#!/usr/bin/env python3
"""
Quick System Stability Test
Tests core components to identify and fix stability issues.
"""

import sys
import logging
import asyncio
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_core_imports():
    """Test if core modules can be imported."""
    logger.info("🔍 Testing core imports...")
    
    try:
        from config.settings import ApplicationSettings
        logger.info("✅ Settings module imported")
        
        from services.model_manager import ModelManager
        logger.info("✅ Model manager imported")
        
        from services.tool_registry import ToolRegistry
        logger.info("✅ Tool registry imported")
        
        from providers.tools.music_control_tool import MusicControlTool
        logger.info("✅ Music control tool imported")
        
        from providers.voice.enhanced_voice_provider import EnhancedVoiceProvider
        logger.info("✅ Enhanced voice provider imported")
        
        from providers.tools.oauth2_gmail_provider import OAuth2GmailProvider
        logger.info("✅ OAuth2 Gmail provider imported")
        
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False

async def test_configuration():
    """Test configuration loading."""
    logger.info("🔍 Testing configuration...")
    
    try:
        from config.settings import ApplicationSettings
        settings = ApplicationSettings()
        
        logger.info(f"✅ Configuration loaded: {settings.app_name}")
        logger.info(f"   Model: {settings.model.name}")
        logger.info(f"   Provider: {settings.model.provider}")
        logger.info(f"   Intel Profile: {settings.current_intel_profile}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Configuration failed: {e}")
        return False

async def test_tool_registry():
    """Test tool registry functionality."""
    logger.info("🔍 Testing tool registry...")
    
    try:
        from services.tool_registry import ToolRegistry
        from providers.tools.music_control_tool import MusicControlTool
        
        registry = ToolRegistry()
        music_tool = MusicControlTool()
        
        # Test registration
        success = registry.register_tool("music_control", music_tool)
        if not success:
            logger.error("❌ Failed to register music tool")
            return False
        
        # Test availability
        tools = registry.get_available_tools()
        if "music_control" not in tools:
            logger.error("❌ Music tool not available after registration")
            return False
        
        logger.info(f"✅ Tool registry working: {len(tools)} tools")
        return True
    except Exception as e:
        logger.error(f"❌ Tool registry failed: {e}")
        return False

async def test_voice_provider():
    """Test voice provider functionality."""
    logger.info("🔍 Testing voice provider...")
    
    try:
        from providers.voice.enhanced_voice_provider import EnhancedVoiceProvider
        
        voice_provider = EnhancedVoiceProvider()
        success = await voice_provider.initialize()
        
        if success:
            info = voice_provider.get_model_info()
            logger.info(f"✅ Voice provider initialized: {info.get('tts_engine', 'Unknown')}")
            return True
        else:
            logger.warning("⚠️ Voice provider failed to initialize")
            return False
    except Exception as e:
        logger.error(f"❌ Voice provider failed: {e}")
        return False

async def test_model_loading():
    """Test model loading."""
    logger.info("🔍 Testing model loading...")
    
    try:
        from services.intel_optimizer import IntelOptimizer
        from services.model_manager import ModelManager
        from providers.models.mistral_openvino_provider import MistralOpenVINOProvider
        
        optimizer = IntelOptimizer()
        model_manager = ModelManager(optimizer)
        
        # Register provider
        provider = MistralOpenVINOProvider()
        model_manager.register_provider("mistral", provider)
        
        # Test load
        success = await model_manager.load_model("mistral-7b-instruct")
        if success:
            logger.info("✅ Model loading successful")
            return True
        else:
            logger.warning("⚠️ Model loading failed")
            return False
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        return False

async def main():
    """Main test runner."""
    logger.info("🚀 Starting Quick Stability Test\n")
    
    tests = [
        ("Core Imports", test_core_imports),
        ("Configuration", test_configuration),
        ("Tool Registry", test_tool_registry),
        ("Voice Provider", test_voice_provider),
        ("Model Loading", test_model_loading),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            print()  # Add spacing
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            print()
    
    logger.info(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! System is stable.")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. System needs fixes.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)