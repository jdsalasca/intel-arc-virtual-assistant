"""
API Routes for Intel Virtual Assistant.
"""

from .chat import router as chat_router
from .voice import router as voice_router
from .health import router as health_router
from .tools import router as tools_router

__all__ = ['chat_router', 'voice_router', 'health_router', 'tools_router']