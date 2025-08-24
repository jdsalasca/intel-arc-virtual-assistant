"""
Virtual Assistant Main Application
Intel-optimized AI assistant with multi-modal capabilities.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

# Import our services and providers
from services.intel_optimizer import IntelOptimizer
from services.model_manager import ModelManager
from services.conversation_manager import ConversationManager

# Import providers (we'll create these next)
from providers.models.openvino_provider import OpenVINOProvider
from providers.storage.sqlite_provider import SQLiteProvider

# Import API routes (we'll create these next)
from api.routes import chat, voice, tools, health

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
intel_optimizer = None
model_manager = None
conversation_manager = None
storage_provider = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Virtual Assistant...")
    
    try:
        # Initialize Intel optimizer
        global intel_optimizer, model_manager, conversation_manager, storage_provider
        
        intel_optimizer = IntelOptimizer()
        logger.info("✅ Intel optimizer initialized")
        
        # Initialize storage
        storage_provider = SQLiteProvider()
        storage_provider.connect("assistant.db")
        logger.info("✅ Storage initialized")
        
        # Initialize conversation manager
        conversation_manager = ConversationManager(storage_provider)
        logger.info("✅ Conversation manager initialized")
        
        # Initialize model manager
        model_manager = ModelManager(intel_optimizer)
        
        # Register OpenVINO provider
        openvino_provider = OpenVINOProvider()
        model_manager.register_provider("openvino", openvino_provider)
        
        # Load default model
        await model_manager.load_model("qwen2.5-7b-int4")
        logger.info("✅ Model manager initialized")
        
        # Hardware summary
        hardware = intel_optimizer.get_hardware_summary()
        logger.info(f"🔧 Hardware: CPU={hardware['cpu']['available']}, "
                   f"Arc GPU={hardware['arc_gpu']['available']}, "
                   f"NPU={hardware['npu']['available']}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("⏹️ Shutting down Virtual Assistant...")
    
    try:
        # Cleanup models
        if model_manager:
            for model_name in model_manager.get_loaded_models():
                await model_manager.unload_model(model_name)
        
        # Cleanup storage
        if storage_provider:
            storage_provider.disconnect()
        
        logger.info("✅ Shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Create FastAPI app
app = FastAPI(
    title="Intel Virtual Assistant",
    description="Intelligent virtual assistant optimized for Intel Core Ultra 7 with Arc GPU and NPU",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
async def get_intel_optimizer() -> IntelOptimizer:
    return intel_optimizer

async def get_model_manager() -> ModelManager:
    return model_manager

async def get_conversation_manager() -> ConversationManager:
    return conversation_manager

# Include API routes
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

# Static files
if Path("web/static").exists():
    app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    html_file = Path("web/templates/index.html")
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Intel Virtual Assistant</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 40px; }
                .logo { font-size: 48px; margin-bottom: 10px; }
                .status { padding: 20px; background: #e8f5e8; border-radius: 5px; margin: 20px 0; }
                .api-list { list-style: none; padding: 0; }
                .api-list li { padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; }
                .api-list a { text-decoration: none; color: #0066cc; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🤖</div>
                    <h1>Intel Virtual Assistant</h1>
                    <p>Intelligent AI assistant optimized for Intel Core Ultra 7</p>
                </div>
                
                <div class="status">
                    <h3>✅ Server Running</h3>
                    <p>Your virtual assistant is ready! The server is optimized for Intel Arc GPU and AI Boost NPU.</p>
                </div>
                
                <h3>Available Endpoints:</h3>
                <ul class="api-list">
                    <li><a href="/docs">📚 Interactive API Documentation</a></li>
                    <li><a href="/api/v1/health/status">🔍 Health Check</a></li>
                    <li><a href="/api/v1/health/hardware">🔧 Hardware Info</a></li>
                    <li><a href="/api/v1/chat/models">🧠 Available Models</a></li>
                </ul>
                
                <h3>Features:</h3>
                <ul>
                    <li>🗣️ Multi-modal conversations (text, voice)</li>
                    <li>🔧 Intel hardware optimization (Arc GPU + NPU)</li>
                    <li>📧 Tool integrations (Gmail, web search, files)</li>
                    <li>💾 Conversation history and context</li>
                    <li>🌐 Internet access for real-time information</li>
                </ul>
                
                <p style="text-align: center; margin-top: 40px; color: #666;">
                    Powered by Intel OpenVINO • Core Ultra 7 Optimized
                </p>
            </div>
        </body>
        </html>
        """)

# Legacy compatibility endpoints
@app.get("/healthz")
@app.get("/health")
async def health():
    """Legacy health check endpoint."""
    try:
        if model_manager:
            models = model_manager.get_loaded_models()
            return {
                "status": "ok",
                "loaded_models": models,
                "hardware": intel_optimizer.get_hardware_summary() if intel_optimizer else {}
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
        if model_manager:
            available = model_manager.get_available_models()
            loaded = model_manager.get_loaded_models()
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
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 1))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    # Run server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        reload=False  # Set to True for development
    )