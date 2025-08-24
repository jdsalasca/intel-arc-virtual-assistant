# server_openai.py
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os, time, glob
import openvino_genai as ov_genai
from huggingface_hub import snapshot_download

MODEL_ID_OLD  = "OpenVINO/Phi-3-mini-4k-instruct-int4-ov"
MODEL_ID = "OpenVINO/Qwen2.5-7B-Instruct-int4-ov"
BASE_DIR  = os.path.dirname(__file__)
MODEL_DIR_OLD = os.path.join(BASE_DIR, "Phi-3-mini-4k-instruct-int4-ov")
MODEL_DIR = os.path.join(BASE_DIR, "Qwen2.5-7B-Instruct-int4-ov")
MODEL_NAME_OLD = "ov-phi3-mini-int4"
MODEL_NAME = "ov-qwen2.5-7b-int4"

# download once
if not os.path.isdir(MODEL_DIR) or not glob.glob(os.path.join(MODEL_DIR, "*.xml")):
    snapshot_download(repo_id=MODEL_ID, local_dir=MODEL_DIR, local_dir_use_symlinks=False)

# load OV GenAI pipeline on Intel GPU
pipe = ov_genai.LLMPipeline(MODEL_DIR, "GPU")

app = FastAPI(title="OpenVINO OpenAI-compatible API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)

# ---------- OpenAI schemas (minimal) ----------
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

def _check_key(auth: Optional[str]):
    required = os.getenv("OPENAI_API_KEY")
    if not required:
        return
    if not auth or not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != required:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ---------- HEALTH ----------
@app.get("/healthz")
def healthz():
    return {"status": "ok", "model": MODEL_NAME}

# ---------- MODELS (OpenAI + alias) ----------
@app.get("/v1/models")
@app.get("/models")
def list_models():
    return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}

# ---------- CHAT COMPLETIONS (OpenAI + alias) ----------
@app.post("/v1/chat/completions")
@app.post("/chat/completions")
def chat_completions(req: ChatRequest, authorization: Optional[str] = Header(None)):
    _check_key(authorization)
    # build prompt from messages (very simple format)
    sys = "\n".join(m.content for m in req.messages if m.role == "system")
    convo = "\n".join(f"{m.role.upper()}: {m.content}" for m in req.messages if m.role != "system")
    prompt = (sys + "\n" + convo).strip() if sys else convo

    text = pipe.generate(
        prompt,
        max_new_tokens=req.max_tokens or 256,
        temperature=req.temperature or 0.2,
    )
    now = int(time.time())
    return {
        "id": f"chatcmpl-{now}",
        "object": "chat.completion",
        "created": now,
        "model": req.model or MODEL_NAME,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
    }

# ---------- COMPLETIONS (legacy OpenAI + alias) ----------
@app.post("/v1/completions")
@app.post("/completions")
def completions(req: CompletionRequest, authorization: Optional[str] = Header(None)):
    _check_key(authorization)
    text = pipe.generate(
        req.prompt,
        max_new_tokens=req.max_tokens or 256,
        temperature=req.temperature or 0.2,
    )
    now = int(time.time())
    return {
        "id": f"cmpl-{now}",
        "object": "text_completion",
        "created": now,
        "model": req.model or MODEL_NAME,
        "choices": [{"index": 0, "text": text, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
    }

# ---------- SIMPLE /generate ALIAS (for quick tests) ----------
class SimpleGen(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.2

@app.post("/generate")
def generate(req: SimpleGen, authorization: Optional[str] = Header(None)):
    _check_key(authorization)
    text = pipe.generate(req.prompt, max_new_tokens=req.max_tokens or 256, temperature=req.temperature or 0.2)
    return {"text": text}