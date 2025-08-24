# 🚀 Quick Start Guide

## Immediate Setup (Windows)

1. **Run the setup script**:
   ```cmd
   setup.bat
   ```

2. **Start the server**:
   ```cmd
   python start_server.py
   ```

3. **Test the server** (in another terminal):
   ```cmd
   python test_client.py
   ```

## Manual Setup

1. **Install dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional):
   ```cmd
   copy .env.example .env
   ```

3. **Start server**:
   ```cmd
   python start_server.py
   ```

## Quick Usage Examples

### Simple API Call
```bash
curl -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{"prompt": "Hello!"}'
```

### LangChain Integration
```python
from langchain_client import OpenVINOGenAI
llm = OpenVINOGenAI()
response = llm("Explain AI in simple terms")
```

### OpenAI Python Client
```python
import openai
client = openai.OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")
response = client.chat.completions.create(
    model="ov-qwen2.5-7b-int4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Common Commands

- Start server: `python start_server.py`
- Test server: `python test_client.py`
- Test specific endpoint: `python test_client.py --test generate`
- Development mode: `python start_server.py --reload`
- Docker: `docker-compose up`

## First Run Notes

- Model download will happen automatically on first run
- Requires ~5-10GB for model download
- Intel GPU recommended for better performance
- Check `README.md` for detailed documentation