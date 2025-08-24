"""
Test script to validate the virtual assistant core architecture.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.intel_optimizer import IntelOptimizer
from core.models.conversation import Conversation, Message, MessageRole, MessageType

async def test_core_architecture():
    """Test the core architecture components."""
    
    print("🧪 Testing Virtual Assistant Core Architecture\n")
    
    # Test 1: Intel Optimizer
    print("1️⃣ Testing Intel Optimizer...")
    try:
        optimizer = IntelOptimizer()
        
        # Test hardware detection
        hardware = optimizer.get_hardware_summary()
        print(f"   ✅ Hardware detected: {hardware}")
        
        # Test device selection
        device = optimizer.select_optimal_device("qwen2.5-7b-int4", "llm")
        print(f"   ✅ Optimal device for Qwen2.5-7B: {device}")
        
        # Test model configuration
        config = optimizer.get_model_config("qwen2.5-7b-int4", device)
        print(f"   ✅ Model config: {config}")
        
        # Test inference optimization
        params = optimizer.optimize_inference_params("qwen2.5-7b-int4", device, 256)
        print(f"   ✅ Inference params: {params}")
        
    except Exception as e:
        print(f"   ❌ Intel Optimizer test failed: {e}")
        return False
    
    # Test 2: Data Models
    print("\n2️⃣ Testing Data Models...")
    try:
        # Test conversation model
        conversation = Conversation(
            user_id="test_user",
            title="Test Conversation"
        )
        print(f"   ✅ Conversation created: {conversation.id}")
        
        # Test message model
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Hello, virtual assistant!",
            message_type=MessageType.TEXT
        )
        print(f"   ✅ Message created: {message.id}")
        
        # Test serialization
        conv_dict = conversation.dict()
        msg_dict = message.dict()
        print(f"   ✅ Serialization works")
        
    except Exception as e:
        print(f"   ❌ Data Models test failed: {e}")
        return False
    
    # Test 3: Model Suggestions
    print("\n3️⃣ Testing Model Suggestions...")
    try:
        # Test different task suggestions
        tasks = [
            "I need a quick response",
            "Help me with complex analysis", 
            "Simple tool routing task",
            "Convert speech to text",
            "Generate speech from text"
        ]
        
        for task in tasks:
            model, device = optimizer.suggest_model_for_task(task.lower())
            print(f"   ✅ Task: '{task}' → Model: {model}, Device: {device}")
            
    except Exception as e:
        print(f"   ❌ Model Suggestions test failed: {e}")
        return False
    
    # Test 4: Performance Monitoring
    print("\n4️⃣ Testing Performance Monitoring...")
    try:
        perf = optimizer.monitor_performance()
        print(f"   ✅ Performance metrics: {perf}")
        
    except Exception as e:
        print(f"   ❌ Performance Monitoring test failed: {e}")
        return False
    
    print("\n🎉 All core architecture tests passed!")
    print("\n📊 Summary:")
    print(f"   • Intel hardware optimization: ✅")
    print(f"   • Data models and serialization: ✅") 
    print(f"   • Model selection intelligence: ✅")
    print(f"   • Performance monitoring: ✅")
    
    return True

async def test_conversation_flow():
    """Test a basic conversation flow."""
    print("\n🗣️ Testing Conversation Flow...")
    
    try:
        # Create a conversation
        conversation = Conversation(
            user_id="test_user",
            title="Architecture Test Chat"
        )
        
        # Add system message
        system_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.SYSTEM,
            content="You are a helpful AI assistant optimized for Intel hardware.",
            message_type=MessageType.TEXT
        )
        
        # Add user message
        user_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="What can you tell me about Intel Arc GPUs?",
            message_type=MessageType.TEXT
        )
        
        # Add assistant response
        assistant_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Intel Arc GPUs are high-performance graphics cards optimized for AI workloads and content creation.",
            message_type=MessageType.TEXT
        )
        
        # Test conversation history format
        messages = [system_msg, user_msg, assistant_msg]
        history = [{"role": msg.role.value, "content": msg.content} for msg in messages]
        
        print(f"   ✅ Conversation flow: {len(messages)} messages")
        print(f"   ✅ OpenAI format: {len(history)} entries")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Conversation flow test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        success = await test_core_architecture()
        if success:
            await test_conversation_flow()
            print("\n🚀 Ready to implement remaining components!")
        else:
            print("\n❌ Core architecture needs fixes before proceeding.")
    
    asyncio.run(main())