"""
Controllers Package for Intel Virtual Assistant Backend
Contains FastAPI route controllers following REST conventions.
"""

from .chat_controller import router as chat_router
from .models_controller import router as models_router
from .voice_controller import router as voice_router
from .tools_controller import router as tools_router
from .health_controller import router as health_router

# Export all routers
__all__ = [
    "chat_router",
    "models_router", 
    "voice_router",
    "tools_router",
    "health_router"
]

# List of all routers for easy registration
ALL_ROUTERS = [
    chat_router,
    models_router,
    voice_router,
    tools_router,
    health_router
]