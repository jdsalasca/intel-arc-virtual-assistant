#!/usr/bin/env python3
"""
Production Build Script
Builds the frontend and prepares for deployment.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.OKBLUE):
    print(f"{color}{message}{Colors.ENDC}")

def build_frontend():
    """Build the React frontend for production."""
    print_colored("🏗️ Building React Frontend...", Colors.OKGREEN)
    
    frontend_dir = Path(__file__).parent / 'frontend'
    
    try:
        # Install dependencies if needed
        if not (frontend_dir / 'node_modules').exists():
            print_colored("📦 Installing frontend dependencies...", Colors.WARNING)
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
        
        # Run type check
        print_colored("🔍 Running TypeScript type check...", Colors.OKBLUE)
        subprocess.run(['npm', 'run', 'type-check'], cwd=frontend_dir, check=True)
        
        # Build for production
        print_colored("📦 Building production bundle...", Colors.OKBLUE)
        subprocess.run(['npm', 'run', 'build'], cwd=frontend_dir, check=True)
        
        print_colored("✅ Frontend build complete!", Colors.OKGREEN)
        return True
        
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Frontend build failed: {e}", Colors.FAIL)
        return False

def prepare_backend():
    """Prepare backend for production."""
    print_colored("🔧 Preparing Backend...", Colors.OKGREEN)
    
    try:
        # Create backend distribution directory
        backend_dist = Path('dist/backend')
        backend_dist.mkdir(parents=True, exist_ok=True)
        
        # Copy backend files
        files_to_copy = [
            'backend/api_server.py',
            'main.py',
            'server_openai.py',
            'start_server.py',
            'requirements.txt',
            'config/',
            'core/',
            'services/',
            'providers/',
            'api/',
        ]
        
        for item in files_to_copy:
            src = Path(item)
            if src.exists():
                if src.is_file():
                    dst = backend_dist / src.name
                    shutil.copy2(src, dst)
                else:
                    dst = backend_dist / src.name
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    
                print_colored(f"📄 Copied {item}", Colors.OKBLUE)
        
        print_colored("✅ Backend preparation complete!", Colors.OKGREEN)
        return True
        
    except Exception as e:
        print_colored(f"❌ Backend preparation failed: {e}", Colors.FAIL)
        return False

def create_deployment_package():
    """Create deployment package."""
    print_colored("📦 Creating Deployment Package...", Colors.OKGREEN)
    
    try:
        # Copy frontend build to backend static files
        frontend_dist = Path('frontend/dist')
        backend_static = Path('dist/backend/static')
        
        if frontend_dist.exists():
            if backend_static.exists():
                shutil.rmtree(backend_static)
            shutil.copytree(frontend_dist, backend_static)
            print_colored("📁 Frontend assets copied to backend static files", Colors.OKBLUE)
        
        # Create production configuration
        prod_config = Path('dist/backend/.env.production')
        with open(prod_config, 'w') as f:
            f.write("""# Production Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEV_MODE=false
LOG_LEVEL=info
WORKERS=4

# Frontend Configuration
SERVE_FRONTEND=true
STATIC_FILES_DIR=static

# Security
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# Models
MODEL_CACHE_DIR=./models
DEFAULT_MODEL=qwen2.5-7b-int4

# Voice
VOICE_CACHE_DIR=./voice_cache
""")
        
        print_colored("⚙️ Production configuration created", Colors.OKBLUE)
        
        # Create startup script for production
        startup_script = Path('dist/backend/start_production.py')
        with open(startup_script, 'w') as f:
            f.write("""#!/usr/bin/env python3
import os
import uvicorn
from dotenv import load_dotenv

# Load production environment
load_dotenv('.env.production')

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        workers=int(os.getenv("WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info"),
        reload=False
    )
""")
        
        startup_script.chmod(0o755)
        print_colored("🚀 Production startup script created", Colors.OKBLUE)
        
        print_colored("✅ Deployment package ready in dist/ directory!", Colors.OKGREEN)
        return True
        
    except Exception as e:
        print_colored(f"❌ Deployment package creation failed: {e}", Colors.FAIL)
        return False

def main():
    """Main build function."""
    print_colored("🏗️ Intel Virtual Assistant - Production Build", Colors.HEADER)
    print_colored("=" * 60, Colors.HEADER)
    
    # Check if we're in the right directory
    if not Path('main.py').exists():
        print_colored("❌ Please run this script from the project root directory", Colors.FAIL)
        sys.exit(1)
    
    # Clean previous build
    dist_dir = Path('dist')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print_colored("🧹 Cleaned previous build", Colors.WARNING)
    
    dist_dir.mkdir()
    
    # Build steps
    steps = [
        ("Frontend Build", build_frontend),
        ("Backend Preparation", prepare_backend),
        ("Deployment Package", create_deployment_package),
    ]
    
    for step_name, step_func in steps:
        print_colored(f"\n{'='*20} {step_name} {'='*20}", Colors.HEADER)
        if not step_func():
            print_colored(f"❌ Build failed at: {step_name}", Colors.FAIL)
            sys.exit(1)
    
    print_colored("\n" + "="*60, Colors.HEADER)
    print_colored("🎉 Production build completed successfully!", Colors.OKGREEN)
    print_colored("\nTo deploy:", Colors.OKBLUE)
    print_colored("1. Copy the dist/ directory to your server", Colors.OKBLUE)
    print_colored("2. Install Python dependencies: pip install -r requirements.txt", Colors.OKBLUE)
    print_colored("3. Run: python start_production.py", Colors.OKBLUE)

if __name__ == "__main__":
    main()