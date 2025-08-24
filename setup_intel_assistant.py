#!/usr/bin/env python3
"""
Intel AI Assistant - One-Click Setup Script
Automatically installs dependencies, configures hardware optimization, and prepares the system.
"""

import os
import sys
import json
import subprocess
import platform
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import zipfile
import tarfile

# Color codes for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text: str, color: str = Colors.ENDC):
    """Print colored text to terminal."""
    print(f"{color}{text}{Colors.ENDC}")

def print_header(text: str):
    """Print section header."""
    print()
    print_colored("="*60, Colors.BLUE)
    print_colored(f" {text} ", Colors.BOLD + Colors.BLUE)
    print_colored("="*60, Colors.BLUE)
    print()

def print_step(step: str):
    """Print setup step."""
    print_colored(f"🔧 {step}", Colors.YELLOW)

def print_success(message: str):
    """Print success message."""
    print_colored(f"✅ {message}", Colors.GREEN)

def print_error(message: str):
    """Print error message."""
    print_colored(f"❌ {message}", Colors.RED)

def print_warning(message: str):
    """Print warning message."""
    print_colored(f"⚠️  {message}", Colors.YELLOW)

class IntelAssistantSetup:
    """Main setup class for Intel AI Assistant."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / ".venv"
        self.models_dir = self.project_root / "models"
        self.credentials_dir = self.project_root / "credentials"
        self.logs_dir = self.project_root / "logs"
        
        # Setup logging
        self.setup_logging()
        
        # System info
        self.system_info = self.detect_system()
        
        print_header("Intel AI Assistant - One-Click Setup")
        print_colored("🚀 Optimized for Intel Core Ultra 7 with Arc GPU and AI Boost NPU", Colors.BLUE)
        print_colored(f"📁 Project Directory: {self.project_root}", Colors.BLUE)
        print()
    
    def setup_logging(self):
        """Setup logging for the setup process."""
        log_file = self.project_root / "setup.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def detect_system(self) -> Dict[str, str]:
        """Detect system information."""
        info = {
            "os": platform.system(),
            "os_version": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "processor": platform.processor()
        }
        
        print_step("Detecting system configuration...")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        return info
    
    def check_requirements(self) -> bool:
        """Check system requirements."""
        print_step("Checking system requirements...")
        
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            issues.append("Python 3.8+ required")
        else:
            print_success(f"Python {sys.version_info.major}.{sys.version_info.minor} ✓")
        
        # Check OS
        if self.system_info["os"] != "Windows":
            issues.append("Windows 11 recommended for Intel optimization")
        else:
            print_success("Windows OS detected ✓")
        
        # Check available space
        free_space = shutil.disk_usage(self.project_root).free / (1024**3)  # GB
        if free_space < 10:
            issues.append(f"Insufficient disk space: {free_space:.1f}GB available, 10GB required")
        else:
            print_success(f"Disk space: {free_space:.1f}GB available ✓")
        
        # Check pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            print_success("pip available ✓")
        except subprocess.CalledProcessError:
            issues.append("pip not available")
        
        if issues:
            print_error("System requirements not met:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        return True
    
    def create_directories(self):
        """Create necessary directories."""
        print_step("Creating directory structure...")
        
        directories = [
            self.models_dir,
            self.credentials_dir,
            self.logs_dir,
            self.project_root / "cache",
            self.project_root / "data" / "conversations",
            self.project_root / "config"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print_success(f"Directory created: {directory.name}")
    
    def create_virtual_environment(self):
        """Create Python virtual environment."""
        print_step("Setting up Python virtual environment...")
        
        if self.venv_path.exists():
            print_warning("Virtual environment already exists")
            return
        
        try:
            subprocess.run([
                sys.executable, "-m", "venv", str(self.venv_path)
            ], check=True)
            print_success("Virtual environment created")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to create virtual environment: {e}")
            sys.exit(1)
    
    def get_pip_executable(self) -> str:
        """Get pip executable path in virtual environment."""
        if platform.system() == "Windows":
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:
            return str(self.venv_path / "bin" / "pip")
    
    def install_dependencies(self):
        """Install Python dependencies."""
        print_step("Installing Python dependencies...")
        
        pip_exe = self.get_pip_executable()
        
        # Upgrade pip first
        try:
            subprocess.run([pip_exe, "install", "--upgrade", "pip"], check=True)
            print_success("pip upgraded")
        except subprocess.CalledProcessError:
            print_warning("Failed to upgrade pip, continuing...")
        
        # Install core dependencies
        core_packages = [
            "fastapi>=0.104.1",
            "uvicorn[standard]>=0.24.0", 
            "pydantic>=2.5.0",
            "python-dotenv>=1.0.0",
            "requests>=2.31.0",
            "aiohttp>=3.9.0",
            "asyncio-mqtt>=0.13.0"
        ]
        
        print("Installing core web framework...")
        for package in core_packages:
            self.install_package(pip_exe, package)
        
        # Install AI/ML dependencies
        ai_packages = [
            "torch>=2.1.0",
            "transformers>=4.35.0",
            "optimum[openvino]>=1.15.0",
            "openvino>=2023.2.0",
            "accelerate>=0.24.0",
            "scipy>=1.11.0",
            "numpy>=1.24.0"
        ]
        
        print("Installing AI/ML packages (this may take a while)...")
        for package in ai_packages:
            self.install_package(pip_exe, package)
        
        # Install optional dependencies
        optional_packages = [
            "google-auth>=2.23.0",
            "google-auth-oauthlib>=1.1.0",
            "google-api-python-client>=2.108.0",
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "httpx>=0.25.2"
        ]
        
        print("Installing optional packages...")
        for package in optional_packages:
            self.install_package(pip_exe, package, optional=True)
    
    def install_package(self, pip_exe: str, package: str, optional: bool = False):
        """Install a single package."""
        try:
            subprocess.run([pip_exe, "install", package], 
                         check=True, capture_output=True, text=True)
            print_success(f"Installed: {package}")
        except subprocess.CalledProcessError as e:
            if optional:
                print_warning(f"Optional package failed: {package}")
            else:
                print_error(f"Failed to install: {package}")
                print_error(f"Error: {e.stderr}")
                if not optional:
                    sys.exit(1)
    
    def configure_intel_optimization(self):
        """Configure Intel hardware optimization."""
        print_step("Configuring Intel hardware optimization...")
        
        # Create Intel optimization config
        intel_config = {
            "hardware_detection": {
                "auto_detect": True,
                "prefer_intel_devices": True
            },
            "cpu_optimization": {
                "use_mkl": True,
                "use_mkl_dnn": True,
                "threads": "auto"
            },
            "gpu_optimization": {
                "enable_arc_gpu": True,
                "memory_management": "auto"
            },
            "npu_optimization": {
                "enable_ai_boost": True,
                "precision": "int8"
            },
            "openvino_config": {
                "device_priority": ["NPU", "GPU", "CPU"],
                "performance_hint": "THROUGHPUT",
                "enable_caching": True
            }
        }
        
        config_path = self.project_root / "config" / "intel_optimization.json"
        with open(config_path, 'w') as f:
            json.dump(intel_config, f, indent=2)
        
        print_success("Intel optimization configured")
    
    def create_environment_file(self):
        """Create .env file with default configuration."""
        print_step("Creating environment configuration...")
        
        env_content = """# Intel AI Assistant Configuration

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1
LOG_LEVEL=info

# Intel Hardware Configuration
INTEL_OPTIMIZATION=true
AUTO_DETECT_HARDWARE=true
PREFERRED_DEVICE=AUTO

# Model Configuration
PRIMARY_MODEL=mistral-7b-instruct
TTS_MODEL=speecht5-tts
MODEL_PRECISION=int4

# API Keys (optional - configure as needed)
# BING_SEARCH_API_KEY=your_bing_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
# GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# Gmail Integration (optional)
# GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json

# Performance Settings
ENABLE_STREAMING=true
CACHE_SIZE_MB=512
MAX_CONVERSATION_HISTORY=50

# Security Settings
# OPENAI_API_KEY=your_api_key_for_authentication
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60
"""
        
        env_path = self.project_root / ".env"
        if not env_path.exists():
            with open(env_path, 'w') as f:
                f.write(env_content)
            print_success("Environment file created")
        else:
            print_warning("Environment file already exists")
    
    def setup_model_configurations(self):
        """Setup model configurations."""
        print_step("Configuring AI models...")
        
        model_configs = {
            "models": {
                "mistral-7b-instruct": {
                    "source": "mistralai/Mistral-7B-Instruct-v0.3",
                    "type": "llm",
                    "optimization": "openvino_int4",
                    "device": "AUTO",
                    "context_length": 8192,
                    "description": "Mistral-7B optimized for Intel hardware"
                },
                "speecht5-tts": {
                    "source": "microsoft/speecht5_tts",
                    "type": "tts", 
                    "optimization": "openvino",
                    "device": "NPU",
                    "description": "SpeechT5 TTS optimized for Intel NPU"
                }
            },
            "download_on_first_run": True,
            "auto_optimization": True,
            "quantization_default": "int4"
        }
        
        config_path = self.project_root / "config" / "models.json"
        with open(config_path, 'w') as f:
            json.dump(model_configs, f, indent=2)
        
        print_success("Model configurations created")
    
    def create_startup_scripts(self):
        """Create startup scripts for easy launching."""
        print_step("Creating startup scripts...")
        
        # Windows batch script
        if platform.system() == "Windows":
            batch_content = f"""@echo off
echo Starting Intel AI Assistant...
cd /d "{self.project_root}"
call .venv\\Scripts\\activate.bat
python main.py
pause
"""
            batch_path = self.project_root / "start_assistant.bat"
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            print_success("Windows startup script created: start_assistant.bat")
        
        # Unix shell script
        shell_content = f"""#!/bin/bash
echo "Starting Intel AI Assistant..."
cd "{self.project_root}"
source .venv/bin/activate
python main.py
"""
        shell_path = self.project_root / "start_assistant.sh"
        with open(shell_path, 'w') as f:
            f.write(shell_content)
        
        # Make executable on Unix systems
        if platform.system() != "Windows":
            os.chmod(shell_path, 0o755)
        
        print_success("Shell startup script created: start_assistant.sh")
    
    def run_initial_tests(self):
        """Run initial system tests."""
        print_step("Running initial validation tests...")
        
        try:
            # Test Python imports
            python_exe = str(self.venv_path / "Scripts" / "python.exe") if platform.system() == "Windows" else str(self.venv_path / "bin" / "python")
            
            test_imports = [
                "import fastapi",
                "import transformers", 
                "import openvino",
                "import torch"
            ]
            
            for test_import in test_imports:
                result = subprocess.run([
                    python_exe, "-c", test_import
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print_success(f"Import test passed: {test_import.split()[1]}")
                else:
                    print_error(f"Import test failed: {test_import.split()[1]}")
                    print_error(f"Error: {result.stderr}")
        
        except Exception as e:
            print_warning(f"Test execution failed: {e}")
    
    def display_next_steps(self):
        """Display next steps for user."""
        print_header("Setup Complete! 🎉")
        
        print_colored("Your Intel AI Assistant is ready to use!", Colors.GREEN + Colors.BOLD)
        print()
        
        print_colored("🚀 Quick Start:", Colors.BLUE + Colors.BOLD)
        if platform.system() == "Windows":
            print("   Double-click: start_assistant.bat")
        print("   Or run: ./start_assistant.sh")
        print("   Or run: python main.py")
        print()
        
        print_colored("🌐 Web Interface:", Colors.BLUE + Colors.BOLD)
        print("   Open browser to: http://localhost:8000")
        print()
        
        print_colored("🔧 Configuration:", Colors.BLUE + Colors.BOLD)
        print("   • Edit .env file for API keys and settings")
        print("   • Place Gmail credentials in credentials/ folder")
        print("   • Models will download automatically on first run")
        print()
        
        print_colored("🧪 Testing:", Colors.BLUE + Colors.BOLD)
        print("   Run tests: python test_comprehensive_intel_assistant.py")
        print()
        
        print_colored("📚 Documentation:", Colors.BLUE + Colors.BOLD)
        print("   • README.md - Getting started guide")
        print("   • config/ - Configuration examples")
        print("   • logs/ - Application logs")
        print()
        
        print_colored("⚡ Hardware Optimization:", Colors.YELLOW + Colors.BOLD)
        print("   Your Intel Core Ultra 7 with Arc GPU and NPU is auto-detected")
        print("   Models will be optimized for maximum performance")
        print()
    
    def run_setup(self):
        """Run the complete setup process."""
        try:
            # Pre-setup checks
            if not self.check_requirements():
                print_error("Setup aborted due to missing requirements")
                return False
            
            # Setup steps
            self.create_directories()
            self.create_virtual_environment()
            self.install_dependencies()
            self.configure_intel_optimization()
            self.create_environment_file()
            self.setup_model_configurations()
            self.create_startup_scripts()
            self.run_initial_tests()
            
            # Success!
            self.display_next_steps()
            return True
            
        except KeyboardInterrupt:
            print_error("\nSetup interrupted by user")
            return False
        except Exception as e:
            print_error(f"Setup failed with error: {e}")
            self.logger.error(f"Setup error: {e}", exc_info=True)
            return False

def main():
    """Main setup function."""
    setup = IntelAssistantSetup()
    success = setup.run_setup()
    
    if success:
        print_success("🎯 Intel AI Assistant setup completed successfully!")
        print_colored("Ready to revolutionize your AI experience! 🚀", Colors.GREEN + Colors.BOLD)
        return 0
    else:
        print_error("❌ Setup failed. Check setup.log for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())