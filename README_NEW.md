# Intel Virtual Assistant

A modern, intelligent virtual assistant optimized for Intel Core Ultra 7 processors with Arc GPU and AI Boost NPU support. Features a React TypeScript frontend and FastAPI backend with real-time WebSocket communication.

## 🚀 Quick Start

### Development Mode

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd wiwin
   ```

2. **Backend Setup**:
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # Windows:
   .venv\\Scripts\\activate
   # Linux/Mac:
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Start Development Servers**:
   ```bash
   # Easy way (Windows):
   start_dev.bat
   
   # Or manually:
   python dev_server.py
   ```

   This will start:
   - Backend API server on `http://localhost:8000`
   - Frontend dev server on `http://localhost:3000`

### Production Build

```bash
# Build everything
python build.py

# Or using Docker
docker-compose up --build
```

## 🏗️ Architecture

### Project Structure

```
wiwin/
├── backend/                    # Backend API server
│   └── api_server.py          # Main API application
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API and WebSocket services  
│   │   ├── hooks/             # Custom React hooks
│   │   ├── types/             # TypeScript definitions
│   │   └── utils/             # Utility functions
│   ├── package.json
│   └── vite.config.ts
├── api/                       # FastAPI routes
│   ├── routes/                # API endpoints
│   └── schemas/               # Request/response models
├── services/                  # Business logic
├── providers/                 # Implementation providers
│   ├── models/                # AI model providers
│   ├── voice/                 # Voice synthesis/recognition
│   ├── tools/                 # Integration tools
│   └── storage/               # Data persistence
├── config/                    # Configuration management
├── core/                      # Core interfaces and exceptions
├── main.py                    # Legacy full application
├── server_openai.py           # Simple OpenAI-compatible API
└── docker-compose.yml         # Container orchestration
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Tanstack Query (state management)
- Axios (HTTP client)
- Native WebSocket (real-time communication)
- Radix UI (components)

**Backend:**
- FastAPI (web framework)
- OpenVINO GenAI (AI inference)
- SQLite (data storage)
- WebSocket (real-time communication)
- Pydantic (data validation)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- Intel OpenVINO optimization

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
```bash
# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
DEV_MODE=true
LOG_LEVEL=info

# Model Configuration
MODEL_CACHE_DIR=./models
DEFAULT_MODEL=qwen2.5-7b-int4

# Hardware Configuration
DEVICE=AUTO  # AUTO, CPU, GPU, NPU
WORKERS=1

# Security
OPENAI_API_KEY=optional_api_key
CORS_ORIGINS=[\"http://localhost:3000\"]
```

**Frontend** (`frontend/.env`):
```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Application Configuration
VITE_APP_NAME=\"Intel Virtual Assistant\"
VITE_DEV_MODE=true
```

## 📡 API Endpoints

### Backend API (`http://localhost:8000`)

**Health & Status:**
- `GET /healthz` - Health check
- `GET /api/v1/health/status` - Detailed system status
- `GET /api/v1/health/hardware` - Hardware information

**Chat & Conversations:**
- `POST /api/v1/chat/message` - Send chat message
- `WS /api/v1/chat/ws/{client_id}` - WebSocket chat
- `GET /api/v1/chat/conversations` - List conversations
- `POST /api/v1/chat/conversations` - Create conversation

**Voice:**
- `POST /api/v1/voice/tts` - Text-to-speech
- `GET /api/v1/voice/status` - Voice system status

**Models & Tools:**
- `GET /api/v1/models` - Available AI models
- `GET /api/v1/tools/available` - Available tools

**Legacy OpenAI Compatible:**
- `POST /v1/chat/completions` - OpenAI chat format
- `POST /v1/completions` - OpenAI completion format
- `GET /v1/models` - OpenAI models format

## 🔌 Development

### Frontend Development

```bash
cd frontend

# Start dev server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
```

### Backend Development

```bash
# Start backend API
python backend/api_server.py

# Start with auto-reload
python backend/api_server.py --reload

# Start legacy full application
python main.py

# Start simple OpenAI server
python server_openai.py
```

### Docker Development

```bash
# Start development environment
docker-compose --profile dev up

# Start production environment
docker-compose up

# Start with reverse proxy
docker-compose --profile proxy up
```

## 🚢 Deployment

### Option 1: Docker (Recommended)

```bash
# Build and deploy
docker-compose up -d --build

# With reverse proxy
docker-compose --profile proxy up -d --build
```

### Option 2: Manual Deployment

```bash
# Build application
python build.py

# Deploy dist/ directory to server
scp -r dist/ user@server:/path/to/deployment/

# On server, install dependencies and run
cd /path/to/deployment/backend
pip install -r requirements.txt
python start_production.py
```

### Option 3: Separate Frontend/Backend

**Backend:**
```bash
python backend/api_server.py
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve dist/ with nginx or any static file server
```

## 🎯 Features

### Core Features
- 💬 **Real-time Chat** - WebSocket-based instant messaging
- 🗣️ **Voice Interaction** - TTS and STT with Intel optimization
- 🧠 **AI Conversations** - Multiple model support (Qwen, Phi-3, etc.)
- 🔧 **Tool Integration** - Web search, Gmail, music control
- 💾 **Conversation History** - Persistent chat storage
- 🎨 **Modern UI** - Responsive React interface

### Intel Optimizations
- 🔥 **Arc GPU Support** - Hardware-accelerated inference
- ⚡ **NPU Integration** - AI Boost NPU optimization
- 🎛️ **Auto Hardware Detection** - Automatic device selection
- 📊 **Performance Monitoring** - Real-time hardware metrics

### Developer Features
- 🔄 **Hot Reload** - Both frontend and backend
- 📝 **TypeScript** - Full type safety
- 🧪 **Testing** - Comprehensive test suite
- 📚 **API Documentation** - Interactive OpenAPI docs
- 🐳 **Docker Support** - Containerized deployment

## 🧪 Testing

```bash
# Backend tests
python -m pytest tests/

# Frontend tests
cd frontend
npm test

# Integration tests
python test_capabilities.py

# System validation
python comprehensive_system_validator.py
```

## 📋 Requirements

### System Requirements
- Python 3.8+
- Node.js 18+
- 8GB+ RAM
- Intel CPU (Core Ultra 7 recommended)
- Optional: Intel Arc GPU, AI Boost NPU

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Node.js Dependencies
```bash
cd frontend
npm install
```

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Run `python -c \"import sys; print(sys.path)\"` to check Python path
2. **Model Loading**: Ensure sufficient disk space (10GB+) for models
3. **GPU Issues**: Check Intel GPU drivers and OpenVINO installation
4. **Port Conflicts**: Change ports in environment variables
5. **WebSocket Issues**: Check firewall settings and CORS configuration

### Debug Mode

```bash
# Backend debug
python backend/api_server.py --log-level debug

# Frontend debug
cd frontend
npm run dev -- --debug
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- 📧 Email: support@example.com
- 🐛 Issues: GitHub Issues
- 📚 Documentation: `/docs` endpoint when running

---

**Powered by Intel OpenVINO • Optimized for Intel Core Ultra 7**