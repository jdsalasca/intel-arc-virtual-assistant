# Multi-stage Docker build for Intel Virtual Assistant
# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Python Backend with Frontend Assets
FROM python:3.11-slim AS backend

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/
COPY main.py server_openai.py start_server.py ./
COPY config/ ./config/
COPY core/ ./core/
COPY services/ ./services/
COPY providers/ ./providers/
COPY api/ ./api/

# Copy frontend build from previous stage
COPY --from=frontend-builder /app/frontend/dist ./static/

# Create models directory
RUN mkdir -p models logs cache

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1
ENV DEVICE=CPU
ENV LOG_LEVEL=info
ENV SERVE_FRONTEND=true
ENV STATIC_FILES_DIR=static

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the backend API server with frontend serving capability
CMD ["python", "backend/api_server.py"]