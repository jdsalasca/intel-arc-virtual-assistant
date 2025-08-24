# OpenVINO GenAI Server

A FastAPI-based server that provides OpenAI-compatible API endpoints for local AI inference using Intel's OpenVINO GenAI toolkit. This server enables you to run large language models locally with high performance and integrate them with popular frameworks like LangChain and Model Context Protocol (MCP).

## 🚀 Features

- **OpenAI-Compatible API**: Full compatibility with OpenAI's chat completions and completions endpoints
- **Local Inference**: Run models locally using Intel OpenVINO for optimized performance
- **LangChain Integration**: Ready-to-use LangChain wrappers for seamless integration
- **MCP Support**: Model Context Protocol integration for advanced AI workflows
- **Authentication**: Optional API key authentication
- **CORS Support**: Configured for cross-origin requests
- **Health Monitoring**: Built-in health check endpoints
- **Comprehensive Testing**: Full test suite included

## 📋 Requirements

- Python 3.8+
- Intel GPU (for GPU acceleration) or CPU
- At least 8GB RAM (16GB+ recommended for larger models)
- 10GB+ free disk space for model storage

## 🛠️ Installation

1. **Clone or download this repository**:
   ```bash
   cd wiwin
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## 🚀 Quick Start

### 1. Start the Server

**Simple start:**
```bash
python start_server.py
```

**With custom configuration:**
```bash
python start_server.py --host 0.0.0.0 --port 8000 --reload
```

**Development mode:**
```bash
python start_server.py --reload --log-level debug
```

### 2. Verify Server is Running

```bash
python test_client.py
```

Or manually check:
```bash
curl http://localhost:8000/healthz
```

## 📚 API Endpoints

### Health Check
```http
GET /healthz
```

### List Models
```http
GET /v1/models
GET /models
```

### Chat Completions
```http
POST /v1/chat/completions
POST /chat/completions
```

**Example request:**
```json
{
  "model": "ov-qwen2.5-7b-int4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 256
}
```

### Text Completions
```http
POST /v1/completions
POST /completions
```

**Example request:**
```json
{
  "model": "ov-qwen2.5-7b-int4",
  "prompt": "The future of AI is",
  "temperature": 0.7,
  "max_tokens": 256
}
```

### Simple Generation
```http
POST /generate
```

**Example request:**
```json
{
  "prompt": "Explain quantum computing",
  "temperature": 0.7,
  "max_tokens": 256
}
```

## 🔗 Framework Integrations

### LangChain Integration

Use the provided LangChain wrapper:

```python
from langchain_client import OpenVINOGenAI, OpenVINOGenAIChat

# Simple LLM
llm = OpenVINOGenAI(base_url="http://localhost:8000")
response = llm("Explain machine learning")

# Chat model
chat = OpenVINOGenAIChat(base_url="http://localhost:8000")
messages = [
    {"role": "user", "content": "What is OpenVINO?"}
]
response = chat(messages)
```

**Run LangChain examples:**
```bash
python langchain_client.py
```

### MCP Integration

Use the Model Context Protocol integration:

```python
from mcp_integration import OpenVINOGenAIMCP

async with OpenVINOGenAIMCP() as client:
    result = await client.simple_generate("Hello, world!")
    print(result["text"])
```

**Run MCP examples:**
```bash
python mcp_integration.py
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Authentication (optional)
OPENAI_API_KEY=your_secret_key_here

# Model Configuration
MODEL_ID=OpenVINO/Qwen2.5-7B-Instruct-int4-ov
MODEL_NAME=ov-qwen2.5-7b-int4
DEVICE=GPU

# Generation Defaults
DEFAULT_TEMPERATURE=0.2
DEFAULT_MAX_TOKENS=256
```

### Model Configuration

The server supports different OpenVINO models. To use a different model:

1. Update `MODEL_ID` in your `.env` file or directly in `server_openai.py`
2. Ensure the model is compatible with OpenVINO GenAI
3. Restart the server

**Supported model formats:**
- OpenVINO optimized models from Hugging Face
- Models with `.xml` and `.bin` files
- INT4, INT8, and FP16 quantized models

## 🧪 Testing

### Run All Tests
```bash
python test_client.py
```

### Run Specific Tests
```bash
# Test health endpoint only
python test_client.py --test health

# Test with custom URL
python test_client.py --url http://192.168.1.100:8000

# Test with API key
python test_client.py --api-key your_secret_key
```

### Manual Testing

**Test with curl:**
```bash
# Health check
curl http://localhost:8000/healthz

# Simple generation
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "max_tokens": 50}'

# Chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

## 🔐 Authentication

To enable authentication:

1. Set `OPENAI_API_KEY` in your `.env` file
2. Include the API key in requests:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Authorization: Bearer your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!"}'
```

## 🐳 Docker Support

### Build and Run

```bash
# Build image
docker build -t openvino-genai-server .

# Run container
docker run -p 8000:8000 openvino-genai-server
```

### Docker Compose

```bash
docker-compose up
```

## 📊 Performance Optimization

### Hardware Recommendations

- **GPU**: Intel Arc, Intel Xe, or compatible Intel GPUs
- **CPU**: Intel Core i5/i7/i9 or Xeon processors
- **RAM**: 16GB+ for optimal performance
- **Storage**: SSD recommended for model loading

### Configuration Tips

1. **Use GPU acceleration** when available (set `DEVICE=GPU`)
2. **Adjust worker count** based on your hardware (`WORKERS=1` for GPU)
3. **Monitor memory usage** with larger models
4. **Use appropriate quantization** (INT4 for balance, FP16 for quality)

## 🚨 Troubleshooting

### Common Issues

**Server won't start:**
- Check if port 8000 is available
- Verify OpenVINO installation
- Check GPU drivers if using GPU acceleration

**Model loading fails:**
- Ensure sufficient disk space
- Check internet connectivity for model download
- Verify model ID is correct

**Poor performance:**
- Switch from CPU to GPU if available
- Reduce max_tokens for faster responses
- Use quantized models (INT4/INT8)

**Connection errors:**
- Verify server is running (`python test_client.py --test health`)
- Check firewall settings
- Ensure correct URL and port

### Logs

Enable debug logging:
```bash
python start_server.py --log-level debug
```

## 🤝 Integration Examples

### OpenAI Python Client

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # or your API key if auth is enabled
)

response = client.chat.completions.create(
    model="ov-qwen2.5-7b-int4",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### LangChain with Custom LLM

```python
from langchain.llms import OpenAI

# Use as drop-in replacement for OpenAI
llm = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)
```

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Intel OpenVINO team for the GenAI toolkit
- FastAPI for the excellent web framework
- Hugging Face for model hosting and distribution

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Run the test suite to identify specific problems
3. Check Intel OpenVINO documentation for model-specific issues

---

**Happy local AI inference! 🎉**