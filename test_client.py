"""
Test Client for OpenVINO GenAI Server
Comprehensive testing script to validate all server endpoints.
"""

import requests
import json
import time
from typing import Dict, Any, List, Optional

class OpenVINOTestClient:
    """Test client for OpenVINO GenAI server."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def test_health(self) -> Dict[str, Any]:
        """Test health endpoint."""
        print("🏥 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/healthz", timeout=10)
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200
            }
            print(f"   ✅ Health check: {result['response']}" if result['success'] else f"   ❌ Health check failed: {result}")
            return result
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_models(self) -> Dict[str, Any]:
        """Test models endpoint."""
        print("📋 Testing models endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/v1/models", timeout=10)
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200
            }
            if result['success']:
                models = [model['id'] for model in result['response']['data']]
                print(f"   ✅ Available models: {models}")
            else:
                print(f"   ❌ Models endpoint failed: {result}")
            return result
        except Exception as e:
            print(f"   ❌ Models endpoint error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_simple_generate(self, prompt: str = "Hello, how are you?") -> Dict[str, Any]:
        """Test simple generate endpoint."""
        print(f"⚡ Testing simple generate with prompt: '{prompt}'...")
        try:
            payload = {
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 50
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200,
                "duration": end_time - start_time
            }
            
            if result['success']:
                print(f"   ✅ Generated text: {result['response']['text'][:100]}...")
                print(f"   ⏱️  Duration: {result['duration']:.2f}s")
            else:
                print(f"   ❌ Generate failed: {result}")
            
            return result
        except Exception as e:
            print(f"   ❌ Generate error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_chat_completion(self, messages: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Test chat completion endpoint."""
        if messages is None:
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Explain quantum computing in simple terms."}
            ]
        
        print(f"💬 Testing chat completion...")
        try:
            payload = {
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 100
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200,
                "duration": end_time - start_time
            }
            
            if result['success']:
                content = result['response']['choices'][0]['message']['content']
                print(f"   ✅ Chat response: {content[:100]}...")
                print(f"   ⏱️  Duration: {result['duration']:.2f}s")
            else:
                print(f"   ❌ Chat completion failed: {result}")
            
            return result
        except Exception as e:
            print(f"   ❌ Chat completion error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_completion(self, prompt: str = "The future of AI is") -> Dict[str, Any]:
        """Test legacy completion endpoint."""
        print(f"📝 Testing completion with prompt: '{prompt}'...")
        try:
            payload = {
                "prompt": prompt,
                "temperature": 0.6,
                "max_tokens": 75
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200,
                "duration": end_time - start_time
            }
            
            if result['success']:
                text = result['response']['choices'][0]['text']
                print(f"   ✅ Completion: {text[:100]}...")
                print(f"   ⏱️  Duration: {result['duration']:.2f}s")
            else:
                print(f"   ❌ Completion failed: {result}")
            
            return result
        except Exception as e:
            print(f"   ❌ Completion error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_authentication(self) -> Dict[str, Any]:
        """Test authentication if API key is configured."""
        print("🔐 Testing authentication...")
        
        # Test without auth header
        test_session = requests.Session()
        try:
            response = test_session.post(
                f"{self.base_url}/generate",
                json={"prompt": "test", "max_tokens": 10},
                timeout=10
            )
            
            if response.status_code == 401:
                print("   ✅ Authentication is properly enforced")
                return {"success": True, "auth_required": True}
            elif response.status_code == 200:
                print("   ℹ️  No authentication required")
                return {"success": True, "auth_required": False}
            else:
                print(f"   ❌ Unexpected response: {response.status_code}")
                return {"success": False, "status_code": response.status_code}
                
        except Exception as e:
            print(f"   ❌ Authentication test error: {e}")
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary."""
        print("🚀 Running comprehensive tests for OpenVINO GenAI Server")
        print("=" * 60)
        
        results = {}
        
        # Test server connectivity
        results['health'] = self.test_health()
        if not results['health']['success']:
            print("❌ Server is not accessible. Stopping tests.")
            return results
        
        # Test all endpoints
        results['models'] = self.test_models()
        results['simple_generate'] = self.test_simple_generate()
        results['chat_completion'] = self.test_chat_completion()
        results['completion'] = self.test_completion()
        results['authentication'] = self.test_authentication()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result.get('success', False))
        
        for test_name, result in results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Your OpenVINO GenAI server is working perfectly.")
        elif passed_tests > 0:
            print("⚠️  Some tests passed. Check the failed tests above.")
        else:
            print("💥 All tests failed. Please check your server configuration.")
        
        return results

def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OpenVINO GenAI Server")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Server URL (default: http://localhost:8000)")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--test", choices=['health', 'models', 'generate', 'chat', 'completion', 'auth'],
                       help="Run specific test only")
    
    args = parser.parse_args()
    
    client = OpenVINOTestClient(base_url=args.url, api_key=args.api_key)
    
    if args.test:
        # Run specific test
        test_methods = {
            'health': client.test_health,
            'models': client.test_models,
            'generate': client.test_simple_generate,
            'chat': client.test_chat_completion,
            'completion': client.test_completion,
            'auth': client.test_authentication
        }
        
        if args.test in test_methods:
            test_methods[args.test]()
        else:
            print(f"Unknown test: {args.test}")
    else:
        # Run all tests
        client.run_all_tests()

if __name__ == "__main__":
    main()