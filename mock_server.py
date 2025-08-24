"""
Mock OpenAI-compatible server for testing the agent system
This allows us to test the agent system without OpenVINO dependencies
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import random

app = FastAPI(title="Mock OpenAI-compatible API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"], 
    allow_headers=["*"],
)

MODEL_NAME = "mock-llm"

# OpenAI schemas
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 256

class CompletionRequest(BaseModel):
    model: Optional[str] = None
    prompt: str
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 256

class SimpleGen(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.2

def generate_mock_response(prompt: str, max_tokens: int = 256) -> str:
    """Generate a mock response for testing."""
    responses = [
        f"Esta es una respuesta simulada para: {prompt[:50]}...",
        f"Respuesta de prueba para el prompt: {prompt[:50]}...",
        f"Simulación de respuesta del modelo: {prompt[:50]}...",
    ]
    return random.choice(responses) + f" [Mock response, max_tokens: {max_tokens}]"

@app.get("/healthz")
def healthz():
    return {"status": "ok", "model": MODEL_NAME}

@app.get("/v1/models")
@app.get("/models")
def list_models():
    return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
def chat_completions(req: ChatRequest):
    # Build simple prompt from messages
    last_message = req.messages[-1].content if req.messages else "Hello"
    text = generate_mock_response(last_message, req.max_tokens or 256)
    
    now = int(time.time())
    return {
        "id": f"chatcmpl-{now}",
        "object": "chat.completion",
        "created": now,
        "model": req.model or MODEL_NAME,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
    }

@app.post("/v1/completions")
@app.post("/completions")
def completions(req: CompletionRequest):
    text = generate_mock_response(req.prompt, req.max_tokens or 256)
    now = int(time.time())
    return {
        "id": f"cmpl-{now}",
        "object": "text_completion",
        "created": now,
        "model": req.model or MODEL_NAME,
        "choices": [{"index": 0, "text": text, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
    }

@app.post("/generate")
def generate(req: SimpleGen):
    text = generate_mock_response(req.prompt, req.max_tokens or 256)
    return {"text": text}