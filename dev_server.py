#!/usr/bin/env python3
"""
Development Server Startup Script
Starts both backend API and frontend development servers.
"""

import os
import sys
import subprocess
import threading
import time
import signal
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

def run_backend():
    """Run the backend API server."""
    print_colored("🚀 Starting Backend API Server...", Colors.OKGREEN)
    
    # Change to project root
    os.chdir(Path(__file__).parent)
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'API_HOST': '127.0.0.1',
        'API_PORT': '8000',
        'DEV_MODE': 'true',
        'LOG_LEVEL': 'debug'
    })
    
    try:
        # Run the backend server
        subprocess.run([
            sys.executable, 'backend/api_server.py'
        ], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Backend server failed: {e}", Colors.FAIL)
    except KeyboardInterrupt:
        print_colored("⏹️ Backend server stopped by user", Colors.WARNING)

def run_frontend():
    """Run the frontend development server."""
    print_colored("🎨 Starting Frontend Development Server...", Colors.OKGREEN)
    
    frontend_dir = Path(__file__).parent / 'frontend'
    
    try:
        # Check if node_modules exists, install if not
        if not (frontend_dir / 'node_modules').exists():
            print_colored("📦 Installing frontend dependencies...", Colors.WARNING)
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
        
        # Start the development server
        subprocess.run(['npm', 'run', 'dev'], cwd=frontend_dir, check=True)
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Frontend server failed: {e}", Colors.FAIL)
    except KeyboardInterrupt:
        print_colored("⏹️ Frontend server stopped by user", Colors.WARNING)

def main():
    """Main function to orchestrate both servers."""
    print_colored("🚀 Intel Virtual Assistant - Development Environment", Colors.HEADER)
    print_colored("=" * 60, Colors.HEADER)
    
    # Check if we're in the right directory
    if not Path('main.py').exists():
        print_colored("❌ Please run this script from the project root directory", Colors.FAIL)
        sys.exit(1)
    
    processes = []
    
    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        
        # Wait a moment for backend to start
        time.sleep(2)
        
        # Start frontend
        print_colored("\n" + "="*60, Colors.HEADER)
        run_frontend()
        
    except KeyboardInterrupt:
        print_colored("\n⏹️ Shutting down development servers...", Colors.WARNING)
    finally:
        # Cleanup
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        
        print_colored("✅ Development environment stopped", Colors.OKGREEN)

if __name__ == "__main__":
    main()