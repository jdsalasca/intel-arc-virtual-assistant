"""
Test Configuration and Fixtures
Provides common test fixtures and setup for the Intel AI Assistant test suite.
"""

import os
import sys
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import configuration system
from config import ApplicationSettings, EnvironmentManager, IntelProfileManager

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "fixtures"
TEST_MODELS_DIR = TEST_DATA_DIR / "models"
TEST_CACHE_DIR = TEST_DATA_DIR / "cache"

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_MODELS_DIR.mkdir(exist_ok=True)
TEST_CACHE_DIR.mkdir(exist_ok=True)

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Provide test data directory path."""
    return TEST_DATA_DIR

@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture(scope="function")
def test_config_file(temp_dir: Path) -> Path:
    """Create a test configuration file."""
    config_file = temp_dir / "test_config.json"
    
    # Create minimal test configuration
    test_config = {
        "app_name": "Test Assistant",
        "app_version": "0.1.0",
        "log_level": "WARNING",
        "environment": "testing",
        "current_intel_profile": "cpu_only",
        "auto_detect_hardware": False,
        "model": {
            "name": "test-model",
            "provider": "local_openvino",
            "device": "CPU",
            "precision": "FP16",
            "max_tokens": 128,
            "temperature": 0.7,
            "batch_size": 1
        },
        "voice": {
            "tts_enabled": False,
            "stt_enabled": False
        },
        "web": {
            "host": "127.0.0.1",
            "port": 8001,
            "debug": True
        }
    }
    
    import json
    with open(config_file, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    return config_file

@pytest.fixture(scope="function")
def test_settings(test_config_file: Path) -> ApplicationSettings:
    """Provide test application settings."""
    settings = ApplicationSettings(str(test_config_file))
    settings.auto_detect_hardware = False  # Disable auto-detection in tests
    return settings

@pytest.fixture(scope="function")
def test_env_manager() -> EnvironmentManager:
    """Provide test environment manager."""
    # Set test environment variables
    os.environ["MODEL_CACHE_DIR"] = str(TEST_MODELS_DIR)
    os.environ["OPENVINO_CACHE_DIR"] = str(TEST_CACHE_DIR)
    os.environ["ENVIRONMENT"] = "testing"
    
    env_manager = EnvironmentManager()
    return env_manager

@pytest.fixture(scope="function")
def intel_profile_manager() -> IntelProfileManager:
    """Provide Intel profile manager."""
    return IntelProfileManager()

@pytest.fixture(scope="function")
def mock_hardware():
    """Mock hardware information for testing."""
    return {
        "cpu": {
            "available": True,
            "threads": 8,
            "architecture": "x86_64"
        },
        "arc_gpu": {
            "available": False,
            "memory": 0
        },
        "npu": {
            "available": False
        }
    }

@pytest.fixture(scope="function")
def mock_hardware_with_gpu():
    """Mock hardware with GPU for testing."""
    return {
        "cpu": {
            "available": True,
            "threads": 16,
            "architecture": "x86_64"
        },
        "arc_gpu": {
            "available": True,
            "memory": 8192
        },
        "npu": {
            "available": False
        }
    }

@pytest.fixture(scope="function")
def mock_hardware_full():
    """Mock full hardware (CPU + GPU + NPU) for testing."""
    return {
        "cpu": {
            "available": True,
            "threads": 16,
            "architecture": "x86_64"
        },
        "arc_gpu": {
            "available": True,
            "memory": 16384
        },
        "npu": {
            "available": True
        }
    }

@pytest.fixture(scope="function")
def mock_openvino_provider():
    """Mock OpenVINO provider for testing."""
    mock_provider = Mock()
    mock_provider.load_model = Mock(return_value=True)
    mock_provider.unload_model = Mock(return_value=True)
    mock_provider.generate_text = Mock(return_value="Test response")
    mock_provider.is_model_loaded = Mock(return_value=True)
    mock_provider.get_model_info = Mock(return_value={
        "name": "test-model",
        "type": "text",
        "device": "CPU",
        "precision": "FP16"
    })
    return mock_provider

@pytest.fixture(scope="function")
def mock_conversation_manager():
    """Mock conversation manager for testing."""
    mock_manager = Mock()
    mock_manager.create_conversation = Mock(return_value="test-conv-id")
    mock_manager.add_message = Mock(return_value=True)
    mock_manager.get_conversation = Mock(return_value={
        "id": "test-conv-id",
        "messages": [],
        "context": ""
    })
    mock_manager.list_conversations = Mock(return_value=[])
    return mock_manager

@pytest.fixture(scope="function")
def mock_storage_provider():
    """Mock storage provider for testing."""
    mock_storage = Mock()
    mock_storage.connect = Mock(return_value=True)
    mock_storage.disconnect = Mock(return_value=True)
    mock_storage.save_conversation = Mock(return_value=True)
    mock_storage.load_conversation = Mock(return_value=None)
    mock_storage.list_conversations = Mock(return_value=[])
    return mock_storage

@pytest.fixture(scope="function")
def sample_conversation_data():
    """Provide sample conversation data for testing."""
    return {
        "id": "test-conversation-123",
        "title": "Test Conversation",
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2024-01-01T10:00:00Z"
            },
            {
                "role": "assistant", 
                "content": "I'm doing well, thank you! How can I help you today?",
                "timestamp": "2024-01-01T10:00:01Z"
            }
        ],
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:01Z",
        "metadata": {
            "model": "test-model",
            "total_tokens": 50
        }
    }

@pytest.fixture(scope="function") 
def sample_model_config():
    """Provide sample model configuration for testing."""
    return {
        "name": "test-model",
        "provider": "openvino",
        "model_path": "/path/to/test/model",
        "device": "CPU",
        "precision": "FP16",
        "max_tokens": 256,
        "temperature": 0.7,
        "batch_size": 1,
        "context_length": 2048
    }

# Test utility functions
def create_test_model_file(model_dir: Path, model_name: str) -> Path:
    """Create a test model file."""
    model_file = model_dir / f"{model_name}.xml"
    model_file.touch()
    
    # Create weights file
    weights_file = model_dir / f"{model_name}.bin"
    weights_file.write_bytes(b"fake model weights")
    
    return model_file

def assert_model_response_valid(response: str) -> bool:
    """Assert that a model response is valid."""
    return (
        isinstance(response, str) and
        len(response.strip()) > 0 and
        len(response) < 10000  # Reasonable max length
    )

def assert_conversation_valid(conversation: Dict[str, Any]) -> bool:
    """Assert that a conversation structure is valid."""
    required_fields = ["id", "messages", "created_at"]
    return all(field in conversation for field in required_fields)

# Performance test helpers
@pytest.fixture(scope="function")
def performance_monitor():
    """Provide performance monitoring utilities."""
    import time
    import psutil
    import threading
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.cpu_usage = []
            self.memory_usage = []
            self.monitoring = False
            self.monitor_thread = None
        
        def start(self):
            self.start_time = time.time()
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor)
            self.monitor_thread.start()
        
        def stop(self):
            self.end_time = time.time()
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
        
        def _monitor(self):
            while self.monitoring:
                self.cpu_usage.append(psutil.cpu_percent())
                self.memory_usage.append(psutil.virtual_memory().percent)
                time.sleep(0.1)
        
        def get_stats(self):
            return {
                "duration": self.end_time - self.start_time if self.end_time else None,
                "avg_cpu": sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
                "max_cpu": max(self.cpu_usage) if self.cpu_usage else 0,
                "avg_memory": sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
                "max_memory": max(self.memory_usage) if self.memory_usage else 0
            }
    
    return PerformanceMonitor()

# Custom pytest markers for Intel-specific tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "intel: mark test as Intel hardware specific")
    config.addinivalue_line("markers", "gpu: mark test as requiring GPU")
    config.addinivalue_line("markers", "npu: mark test as requiring NPU")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "network: mark test as requiring network")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip tests based on hardware availability."""
    skip_gpu = pytest.mark.skip(reason="GPU not available or not Intel Arc")
    skip_npu = pytest.mark.skip(reason="NPU not available")
    skip_network = pytest.mark.skip(reason="Network tests disabled in CI")
    
    # Check hardware availability (simplified for testing)
    has_gpu = os.getenv("INTEL_ARC_GPU_AVAILABLE") == "true"
    has_npu = os.getenv("INTEL_NPU_AVAILABLE") == "true"
    network_enabled = os.getenv("ENABLE_NETWORK_TESTS") == "true"
    
    for item in items:
        if "gpu" in item.keywords and not has_gpu:
            item.add_marker(skip_gpu)
        if "npu" in item.keywords and not has_npu:
            item.add_marker(skip_npu)
        if "network" in item.keywords and not network_enabled:
            item.add_marker(skip_network)

# Cleanup after tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Clean up test data after test session."""
    yield
    
    # Clean up test cache and temporary files
    if TEST_CACHE_DIR.exists():
        for item in TEST_CACHE_DIR.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    
    # Reset environment variables
    test_env_vars = [
        "MODEL_CACHE_DIR",
        "OPENVINO_CACHE_DIR", 
        "ENVIRONMENT",
        "TEST_MODE"
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]