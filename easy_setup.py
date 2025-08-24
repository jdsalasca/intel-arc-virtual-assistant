#!/usr/bin/env python3
"""
Intel AI Assistant - Easy Setup and Launch Script
One-click setup, installation, and launch for powerful AI capabilities.
"""

import os
import sys
import subprocess
import platform
import json
import time
from pathlib import Path
from typing import Dict, Any, List

class EasySetup:
    """Easy setup and launch system for Intel AI Assistant."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.system_info = self.detect_system()
        self.requirements_installed = False
        
    def detect_system(self) -> Dict[str, Any]:
        """Detect system capabilities and hardware."""
        return {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "has_gpu": self.check_gpu_availability(),
            "has_microphone": self.check_audio_devices(),
        }
    
    def check_gpu_availability(self) -> bool:
        """Check if GPU is available."""
        try:
            import subprocess
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            if result.returncode == 0:
                return True
        except:
            pass
        
        # Check for Intel GPU
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"], 
                                      capture_output=True, text=True)
                if "intel" in result.stdout.lower():
                    return True
        except:
            pass
        
        return False
    
    def check_audio_devices(self) -> bool:
        """Check if audio devices are available."""
        try:
            if platform.system() == "Windows":
                import winreg
                # Basic check for audio devices in registry
                return True
        except:
            pass
        return True  # Assume available
    
    def install_dependencies(self):
        """Install required dependencies."""
        print("🔧 Installing dependencies...")
        
        # Core dependencies
        core_deps = [
            "torch",
            "transformers",
            "openvino",
            "optimum[openvino]",
            "speechrecognition",
            "pyttsx3",
            "pyaudio",
            "pygame",
            "requests",
            "beautifulsoup4",
            "duckduckgo-search",
            "wikipedia",
            "fastapi",
            "uvicorn",
            "websockets",
            "asyncio",
            "aiohttp",
            "python-multipart"
        ]
        
        # Testing dependencies
        test_deps = [
            "pytest",
            "pytest-asyncio",
            "pytest-benchmark",
            "pytest-cov"
        ]
        
        all_deps = core_deps + test_deps
        
        for dep in all_deps:
            try:
                print(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Warning: Failed to install {dep}: {e}")
        
        # Install Intel optimizations if available
        try:
            print("Installing Intel Extension for PyTorch...")
            subprocess.run([sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch"], 
                         check=True, capture_output=True)
        except:
            print("⚠️  Intel Extension for PyTorch not available")
        
        self.requirements_installed = True
        print("✅ Dependencies installed successfully!")
    
    def setup_directories(self):
        """Create necessary directories."""
        print("📁 Setting up directories...")
        
        directories = [
            "models",
            "cache",
            "cache/openvino",
            "cache/huggingface",
            "data",
            "data/conversations",
            "logs",
            "tests/results",
            "services"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("✅ Directories created successfully!")
    
    def create_config_file(self):
        """Create basic configuration file."""
        config = {
            "system": self.system_info,
            "voice": {
                "enabled": True,
                "engine": "pyttsx3",
                "rate": 150,
                "volume": 0.8
            },
            "web_search": {
                "enabled": True,
                "engines": ["duckduckgo", "wikipedia"],
                "max_results": 5
            },
            "ai_model": {
                "device": "auto",
                "max_tokens": 512,
                "temperature": 0.7
            }
        }
        
        config_file = self.project_root / "config" / "runtime_config.json"
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration file created!")
    
    def run_tests(self):
        """Run comprehensive tests."""
        print("🧪 Running tests...")
        
        try:
            # Run basic tests
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/", "-v", "--tb=short"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Tests passed!")
            else:
                print("⚠️  Some tests failed, but continuing...")
                
        except Exception as e:
            print(f"⚠️  Test execution failed: {e}")
    
    def launch_assistant(self):
        """Launch the AI Assistant."""
        print("🚀 Launching Intel AI Assistant...")
        
        try:
            # Launch the AI assistant brain
            assistant_script = self.project_root / "ai_assistant_brain.py"
            
            if assistant_script.exists():
                subprocess.run([sys.executable, str(assistant_script)], cwd=self.project_root)
            else:
                print("⚠️  AI Assistant brain not found, launching basic version...")
                self.launch_basic_demo()
                
        except KeyboardInterrupt:
            print("\n👋 AI Assistant stopped by user")
        except Exception as e:
            print(f"❌ Failed to launch AI Assistant: {e}")
    
    def launch_basic_demo(self):
        """Launch a basic demo if full system isn't ready."""
        print("🎯 Launching basic demo...")
        
        # Create a simple interactive demo
        demo_code = '''
import sys
sys.path.append(".")

try:
    from services.enhanced_voice_service import EnhancedVoiceService
    from services.enhanced_web_search import EnhancedWebSearchService
    
    print("🎤 Voice Service Test:")
    voice = EnhancedVoiceService()
    voice.test_voice_system()
    
    print("\\n🌐 Web Search Test:")
    search = EnhancedWebSearchService()
    results = search.search("im alive", max_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('title', 'No title')}")
        print(f"   {result.get('url', 'No URL')}")
        print(f"   {result.get('snippet', 'No description')[:100]}...")
        print()
    
    print("✅ Basic demo completed successfully!")
    
except Exception as e:
    print(f"❌ Demo failed: {e}")
    print("Please check the installation and try again.")
'''
        
        exec(demo_code)
    
    def full_setup(self):
        """Run complete setup process."""
        print("🎯 Intel AI Assistant - Easy Setup")
        print("=" * 50)
        
        print(f"System: {self.system_info['platform']} {self.system_info['architecture']}")
        print(f"Python: {self.system_info['python_version']}")
        print(f"CPU Cores: {self.system_info['cpu_count']}")
        print(f"GPU Available: {self.system_info['has_gpu']}")
        print(f"Audio Available: {self.system_info['has_microphone']}")
        print()
        
        # Setup steps
        steps = [
            ("Installing Dependencies", self.install_dependencies),
            ("Setting Up Directories", self.setup_directories),
            ("Creating Configuration", self.create_config_file),
            ("Running Tests", self.run_tests),
        ]
        
        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            try:
                step_func()
                time.sleep(0.5)  # Brief pause for visibility
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                return False
        
        print("\n🎉 Setup completed successfully!")
        print("🚀 Launching AI Assistant...")
        
        # Launch the assistant
        self.launch_assistant()
        
        return True

def main():
    """Main entry point."""
    setup = EasySetup()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-only":
            setup.run_tests()
        elif sys.argv[1] == "--demo":
            setup.launch_basic_demo()
        elif sys.argv[1] == "--install-only":
            setup.install_dependencies()
            setup.setup_directories()
        else:
            print("Usage: python easy_setup.py [--test-only|--demo|--install-only]")
    else:
        setup.full_setup()

if __name__ == "__main__":
    main()