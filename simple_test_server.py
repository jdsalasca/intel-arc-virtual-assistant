#!/usr/bin/env python3
"""
Simple Test Server - Demonstrates the project can run
A lightweight FastAPI server without heavy AI dependencies.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(
    title="WiWin AI Assistant - Test Server",
    description="Lightweight test server to demonstrate project functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    user_id: str = "test_user"

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

@app.get("/")
async def root():
    return {
        "message": "WiWin AI Assistant Test Server is Running! 🚀",
        "status": "healthy",
        "project": "Intel-optimized AI Assistant",
        "note": "This is a lightweight test version without AI models"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "wiwin-ai-assistant",
        "version": "1.0.0",
        "dependencies": {
            "fastapi": "✅ Working",
            "uvicorn": "✅ Working",
            "pydantic": "✅ Working"
        }
    }

@app.post("/api/v1/chat")
async def chat_endpoint(message: ChatMessage):
    """Simple chat endpoint that echoes back with a response."""
    try:
        # Simple response logic (without AI)
        user_message = message.message.lower()
        
        if "hello" in user_message or "hi" in user_message:
            response = "Hello! I'm the WiWin AI Assistant test server. How can I help you?"
        elif "status" in user_message:
            response = "I'm running perfectly! This is a lightweight test version."
        elif "help" in user_message:
            response = "I can respond to basic messages. Try saying 'hello', 'status', or 'about'."
        elif "about" in user_message:
            response = "I'm part of the WiWin project - an Intel-optimized AI Assistant with voice, search, and conversational capabilities!"
        else:
            response = f"You said: '{message.message}'. This is a test response from the WiWin AI Assistant!"
        
        return ChatResponse(response=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/v1/capabilities")
async def get_capabilities():
    return {
        "available_features": [
            "Basic Chat Interface",
            "Health Monitoring",
            "REST API Endpoints",
            "CORS Support"
        ],
        "full_features": [
            "🎤 Voice Recognition & Synthesis",
            "🔍 Multi-Engine Web Search",
            "🧠 Conversational AI with Memory",
            "🛠️ Tool Integration (Gmail, Files, Music)",
            "⚡ Intel Hardware Optimization",
            "🌐 OpenAI-Compatible API"
        ],
        "note": "This test server shows basic functionality. Full features require additional setup."
    }

if __name__ == "__main__":
    print("🚀 Starting WiWin AI Assistant Test Server...")
    print("📍 This is a lightweight version for testing")
    print("🌐 Server will be available at: http://localhost:8080")
    print("📚 API docs at: http://localhost:8080/docs")
    print("❤️  Health check at: http://localhost:8080/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )