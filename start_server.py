#!/usr/bin/env python3
"""
OpenVINO GenAI Server Startup Script
Provides easy server management with configuration options.
"""

import os
import sys
import argparse
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_server(host="0.0.0.0", port=8000, workers=1, reload=False, log_level="info"):
    """Start the FastAPI server with OpenVINO GenAI backend."""
    
    print(f"🚀 Starting OpenVINO GenAI Server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"👥 Workers: {workers}")
    print(f"🔄 Reload: {reload}")
    print(f"📝 Log Level: {log_level}")
    
    # Check if model directory exists
    model_dir = os.getenv("MODEL_CACHE_DIR", "./models")
    if not os.path.exists(model_dir):
        print(f"📁 Creating model cache directory: {model_dir}")
        os.makedirs(model_dir, exist_ok=True)
    
    try:
        uvicorn.run(
            "server_openai:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,  # reload doesn't work with multiple workers
            reload=reload,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="OpenVINO GenAI Server")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"), 
                       help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), 
                       help="Port to bind to (default: 8000)")
    parser.add_argument("--workers", type=int, default=int(os.getenv("WORKERS", 1)), 
                       help="Number of worker processes (default: 1)")
    parser.add_argument("--reload", action="store_true", 
                       help="Enable auto-reload for development")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "info"), 
                       choices=["debug", "info", "warning", "error"],
                       help="Log level (default: info)")
    
    args = parser.parse_args()
    
    start_server(
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()