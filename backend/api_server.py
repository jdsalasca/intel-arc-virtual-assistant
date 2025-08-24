"""
Backend API Server for Intel Virtual Assistant
Optimized for React frontend with proper CORS and WebSocket support.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Import configuration system
from config import (
    initialize_settings,
    initialize_environment,
    get_settings,
    get_env_manager
)

# Import our services and providers
from services.intel_optimizer import IntelOptimizer
from services.model_manager import ModelManager
from services.conversation_manager import ConversationManager
from services.chat_agent_orchestrator import ChatAgentOrchestrator
from services.tool_registry import ToolRegistry

# Import providers
from providers.models.mistral_openvino_provider import MistralOpenVINOProvider
from providers.voice.speecht5_openvino_provider import SpeechT5OpenVINOProvider
from providers.tools.enhanced_web_search_tool import EnhancedWebSearchTool
from providers.tools.gmail_connector_tool import GmailConnectorTool
from providers.tools.music_control_tool import MusicControlTool
from providers.storage.sqlite_provider import SQLiteProvider

# Import API routes
from api.routes import chat_router, voice_router, health_router, tools_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services - these will be initialized during startup
app_state: dict[str, Any] = {
    "intel_optimizer": None,
    "model_manager": None,
    "conversation_manager": None,
    "chat_agent": None,
    "tool_registry": None,
    "storage_provider": None,
    "settings": None,
    "env_manager": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Backend API Server...")
    
    try:
        # Initialize environment and settings
        app_state["env_manager"] = initialize_environment()
        app_state["settings"] = initialize_settings()
        
        # Validate environment
        validation = app_state["env_manager"].validate_environment()
        if not validation["valid"]:
            for error in validation["errors"]:
                logger.error(f"Environment validation error: {error}")
        
        for warning in validation["warnings"]:
            logger.warning(f"Environment warning: {warning}")
        
        for info in validation["info"]:
            logger.info(f"Environment info: {info}")
        
        logger.info("✅ Configuration system initialized")
        
        # Initialize Intel optimizer
        app_state["intel_optimizer"] = IntelOptimizer()
        logger.info("✅ Intel optimizer initialized")
        
        # Initialize storage
        app_state["storage_provider"] = SQLiteProvider()
        app_state["storage_provider"].connect("assistant.db")
        logger.info("✅ Storage initialized")
        
        # Initialize conversation manager
        app_state["conversation_manager"] = ConversationManager(app_state["storage_provider"])
        logger.info("✅ Conversation manager initialized")
        
        # Initialize model manager
        app_state["model_manager"] = ModelManager(app_state["intel_optimizer"])
        
        # Register Mistral OpenVINO provider
        mistral_provider = MistralOpenVINOProvider()
        app_state["model_manager"].register_provider("mistral", mistral_provider)
        
        # Load default model from settings
        default_model = app_state["settings"].model.name
        await app_state["model_manager"].load_model(default_model)
        logger.info(f"✅ Model manager initialized with {default_model}")
        
        # Initialize tool registry
        app_state["tool_registry"] = ToolRegistry()
        
        # Register web search tool
        web_search_tool = EnhancedWebSearchTool()
        app_state["tool_registry"].register_tool("web_search", web_search_tool)
        
        # Register Gmail tool if available
        try:
            gmail_tool = GmailConnectorTool()
            if gmail_tool.is_available():
                app_state["tool_registry"].register_tool("gmail_connector", gmail_tool)
                logger.info("✅ Gmail connector available")
        except Exception as e:
            logger.warning(f"Gmail connector not available: {e}")

        # Register Music Control tool
        try:
            music_tool = MusicControlTool()
            app_state["tool_registry"].register_tool("music_control", music_tool)
            logger.info("✅ Music control tool registered")
        except Exception as e:
            logger.warning(f"Music control tool registration failed: {e}")
        
        logger.info(f"✅ Tool registry initialized with {len(app_state['tool_registry'].get_available_tools())} tools")
        
        # Initialize chat agent orchestrator
        app_state["chat_agent"] = ChatAgentOrchestrator(
            app_state["model_manager"], 
            app_state["conversation_manager"], 
            app_state["tool_registry"]
        )
        await app_state["chat_agent"].initialize({
            "primary_model": default_model,
            "tts_model": app_state["settings"].voice.tts_model
        })
        logger.info("✅ Chat agent orchestrator initialized")
        
        # Hardware summary
        hardware = app_state["intel_optimizer"].get_hardware_summary()
        logger.info(f"🔧 Hardware: CPU={hardware['cpu']['available']}, "
                   f"Arc GPU={hardware['arc_gpu']['available']}, "
                   f"NPU={hardware['npu']['available']}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("⏹️ Shutting down Backend API Server...")
    
    try:
        # Cleanup models
        if app_state["model_manager"]:
            for model_name in app_state["model_manager"].get_loaded_models():
                await app_state["model_manager"].unload_model(model_name)
        
        # Cleanup storage
        if app_state["storage_provider"]:
            app_state["storage_provider"].disconnect()
        
        logger.info("✅ Shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Create FastAPI app
app = FastAPI(
    title="Intel Virtual Assistant API",
    description="Backend API for Intel Virtual Assistant React frontend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:8080",  # Alternative frontend port
        "http://127.0.0.1:8080",  # Alternative frontend port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Dependency injection functions
async def get_intel_optimizer():
    return app_state["intel_optimizer"]

async def get_model_manager():
    return app_state["model_manager"]

async def get_conversation_manager():
    return app_state["conversation_manager"]

async def get_chat_agent():
    return app_state["chat_agent"]

async def get_tool_registry():
    return app_state["tool_registry"]

async def get_settings():
    return app_state["settings"]

# Include API routes
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(voice_router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
app.include_router(tools_router, prefix="/api/v1/tools", tags=["tools"])

# Root endpoint for API info
@app.get("/")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Intel Virtual Assistant API",
        "version": "1.0.0",
        "description": "Backend API optimized for Intel Core Ultra 7 with Arc GPU and NPU",
        "endpoints": {
            "health": "/api/v1/health/status",
            "hardware": "/api/v1/health/hardware",
            "chat": "/api/v1/chat/message",
            "websocket": "/api/v1/chat/ws/{client_id}",
            "voice": "/api/v1/voice/tts",
            "tools": "/api/v1/tools/available",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "features": [
            "Real-time chat with WebSocket support",
            "Voice synthesis and recognition",
            "Intel hardware optimization",
            "Tool integrations (Gmail, web search, music)",
            "Conversation history and context",
            "OpenAI-compatible endpoints"
        ]
    }

# Legacy compatibility endpoints for existing clients
@app.get("/healthz")
@app.get("/health")
async def health():
    """Legacy health check endpoint."""
    try:
        if app_state["model_manager"]:
            models = app_state["model_manager"].get_loaded_models()
            return {
                "status": "ok",
                "loaded_models": models,
                "hardware": app_state["intel_optimizer"].get_hardware_summary() if app_state["intel_optimizer"] else {}
            }
        else:
            return {"status": "initializing"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/models")
@app.get("/v1/models") 
async def list_models():
    """Legacy models endpoint."""
    try:
        if app_state["model_manager"]:
            available = app_state["model_manager"].get_available_models()
            loaded = app_state["model_manager"].get_loaded_models()
            return {
                "object": "list",
                "data": [
                    {
                        "id": model,
                        "object": "model",
                        "owned_by": "intel-assistant",
                        "loaded": model in loaded
                    }
                    for model in available
                ]
            }
        else:
            return {"object": "list", "data": []}
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return {"object": "list", "data": []}

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8000))
    workers = int(os.getenv("API_WORKERS", 1))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    # Run server
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        reload=os.getenv("DEV_MODE", "false").lower() == "true"
    )