#!/usr/bin/env python3
"""
System Validation Test
Tests the basic functionality of the restructured Intel Virtual Assistant.
"""

import os
import sys
import time
import requests
import subprocess
import threading
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

def print_colored(message, color=Colors.OKBLUE):
    print(f"{color}{message}{Colors.ENDC}")

def test_backend_health():
    """Test backend health endpoint."""
    try:
        print_colored("🏥 Testing Backend Health...", Colors.OKBLUE)
        response = requests.get("http://localhost:8000/healthz", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_colored(f"✅ Backend health: {data.get('status', 'unknown')}", Colors.OKGREEN)
            return True
        else:
            print_colored(f"❌ Backend health check failed: {response.status_code}", Colors.FAIL)
            return False
    
    except requests.exceptions.RequestException as e:
        print_colored(f"❌ Backend connection failed: {e}", Colors.FAIL)
        return False

def test_api_endpoints():
    """Test basic API endpoints."""
    endpoints = [
        ("/healthz", "Health check"),
        ("/api/v1/health/status", "Detailed health"),
        ("/api/v1/models", "Models list"),
        ("/", "API info"),
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            print_colored(f"🔌 Testing {description}: {endpoint}", Colors.OKBLUE)
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print_colored(f"✅ {description} - OK", Colors.OKGREEN)
                results.append(True)
            else:
                print_colored(f"❌ {description} - Failed ({response.status_code})", Colors.FAIL)
                results.append(False)
                
        except Exception as e:
            print_colored(f"❌ {description} - Error: {e}", Colors.FAIL)
            results.append(False)
    
    return all(results)

def test_frontend_build():
    """Test if frontend can be built."""
    try:
        print_colored("🏗️ Testing Frontend Build...", Colors.OKBLUE)
        
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print_colored("❌ Frontend directory not found", Colors.FAIL)
            return False
        
        # Check if package.json exists
        if not (frontend_dir / "package.json").exists():
            print_colored("❌ Frontend package.json not found", Colors.FAIL)
            return False
        
        print_colored("✅ Frontend structure looks good", Colors.OKGREEN)
        return True
        
    except Exception as e:
        print_colored(f"❌ Frontend test failed: {e}", Colors.FAIL)
        return False

def test_imports():
    """Test critical imports."""
    try:
        print_colored("📦 Testing Critical Imports...", Colors.OKBLUE)
        
        # Test backend imports
        sys.path.insert(0, str(Path(__file__).parent))
        
        from services.intel_optimizer import IntelOptimizer
        print_colored("✅ Intel Optimizer import - OK", Colors.OKGREEN)
        
        from services.model_manager import ModelManager
        print_colored("✅ Model Manager import - OK", Colors.OKGREEN)
        
        from services.conversation_manager import ConversationManager
        print_colored("✅ Conversation Manager import - OK", Colors.OKGREEN)
        
        from api.routes import chat_router, voice_router, health_router
        print_colored("✅ API Routes import - OK", Colors.OKGREEN)
        
        return True
        
    except ImportError as e:
        print_colored(f"❌ Import failed: {e}", Colors.FAIL)
        return False
    except Exception as e:
        print_colored(f"❌ Import test error: {e}", Colors.FAIL)
        return False

def start_backend_server():
    """Start the backend server for testing."""
    try:
        print_colored("🚀 Starting Backend Server for Testing...", Colors.OKBLUE)
        
        # Change to project directory
        os.chdir(Path(__file__).parent)
        
        # Start the backend server
        process = subprocess.Popen([
            sys.executable, "backend/api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print_colored("✅ Backend server started successfully", Colors.OKGREEN)
            return process
        else:
            stdout, stderr = process.communicate()
            print_colored(f"❌ Backend server failed to start", Colors.FAIL)
            print_colored(f"STDOUT: {stdout}", Colors.WARNING)
            print_colored(f"STDERR: {stderr}", Colors.WARNING)
            return None
            
    except Exception as e:
        print_colored(f"❌ Failed to start backend server: {e}", Colors.FAIL)
        return None

def run_validation():
    """Run the complete validation suite."""
    print_colored("🧪 Intel Virtual Assistant - System Validation", Colors.HEADER)
    print_colored("=" * 60, Colors.HEADER)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print_colored("❌ Please run this script from the project root directory", Colors.FAIL)
        return False
    
    tests = [
        ("Import Tests", test_imports),
        ("Frontend Structure", test_frontend_build),
    ]
    
    results = []
    
    # Run basic tests first
    for test_name, test_func in tests:
        print_colored(f"\n{'='*20} {test_name} {'='*20}", Colors.HEADER)
        result = test_func()
        results.append((test_name, result))
    
    # Try to start backend and test endpoints
    print_colored(f"\n{'='*20} Backend Server Tests {'='*20}", Colors.HEADER)
    
    server_process = start_backend_server()
    backend_results = []
    
    if server_process:
        try:
            # Run backend tests
            backend_tests = [
                ("Backend Health", test_backend_health),
                ("API Endpoints", test_api_endpoints),
            ]
            
            for test_name, test_func in backend_tests:
                print_colored(f"\n--- {test_name} ---", Colors.OKBLUE)
                result = test_func()
                backend_results.append((test_name, result))
            
        finally:
            # Clean up server
            print_colored("\n🛑 Stopping test server...", Colors.WARNING)
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print_colored("✅ Test server stopped", Colors.OKGREEN)
    
    # Print results
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored("📋 VALIDATION RESULTS", Colors.HEADER)
    print_colored("=" * 60, Colors.HEADER)
    
    all_passed = True
    
    for test_name, result in results + backend_results:
        status = "✅ PASS" if result else "❌ FAIL"
        color = Colors.OKGREEN if result else Colors.FAIL
        print_colored(f"{test_name:<30} {status}", color)
        if not result:
            all_passed = False
    
    print_colored("=" * 60, Colors.HEADER)
    
    if all_passed:
        print_colored("🎉 All tests passed! System is ready.", Colors.OKGREEN)
        print_colored("", Colors.OKGREEN)
        print_colored("Next steps:", Colors.OKBLUE)
        print_colored("1. Run 'python dev_server.py' to start development", Colors.OKBLUE)
        print_colored("2. Run 'python build.py' to create production build", Colors.OKBLUE)
        print_colored("3. Check README_NEW.md for detailed instructions", Colors.OKBLUE)
    else:
        print_colored("⚠️ Some tests failed. Please check the errors above.", Colors.WARNING)
    
    return all_passed

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)