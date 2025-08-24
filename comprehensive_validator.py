#!/usr/bin/env python3
"""
Intel AI Assistant - Comprehensive System Validator
Tests all components, identifies issues, and provides fixes.
"""

import sys
import os
import time
import traceback
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class ComprehensiveValidator:
    """Comprehensive system validator and issue resolver."""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {
            "validation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": self.get_system_info(),
            "component_tests": {},
            "integration_tests": {},
            "fixes_applied": [],
            "recommendations": []
        }
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        import platform
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            memory_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        except ImportError:
            cpu_count = os.cpu_count()
            memory_gb = "unknown"
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": cpu_count,
            "memory_gb": memory_gb,
            "architecture": platform.architecture()[0],
            "machine": platform.machine()
        }
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """Validate all dependencies."""
        print("🔍 Validating dependencies...")
        
        required_deps = {
            "core": [
                "speech_recognition", "pyttsx3", "requests", "beautifulsoup4",
                "fastapi", "uvicorn", "pydantic"
            ],
            "ai": [
                "torch", "transformers", "openvino"
            ],
            "voice": [
                "pyaudio", "pygame"
            ],
            "search": [
                "duckduckgo_search", "wikipedia"
            ],
            "testing": [
                "pytest", "pytest_asyncio", "pytest_cov"
            ]
        }
        
        results = {"available": {}, "missing": {}, "errors": {}}
        
        for category, deps in required_deps.items():
            results["available"][category] = []
            results["missing"][category] = []
            results["errors"][category] = []
            
            for dep in deps:
                try:
                    # Try importing the dependency
                    module_name = dep.replace("-", "_").replace("_search", "_search")
                    __import__(module_name)
                    results["available"][category].append(dep)
                    print(f"  ✅ {dep}")
                except ImportError as e:
                    results["missing"][category].append(dep)
                    print(f"  ❌ {dep} - {e}")
                except Exception as e:
                    results["errors"][category].append(f"{dep}: {e}")
                    print(f"  ⚠️  {dep} - {e}")
        
        # Calculate summary
        total_available = sum(len(deps) for deps in results["available"].values())
        total_missing = sum(len(deps) for deps in results["missing"].values())
        total_errors = sum(len(deps) for deps in results["errors"].values())
        
        results["summary"] = {
            "total_dependencies": total_available + total_missing + total_errors,
            "available": total_available,
            "missing": total_missing,
            "errors": total_errors,
            "success_rate": round(total_available / (total_available + total_missing + total_errors) * 100, 1) if (total_available + total_missing + total_errors) > 0 else 0
        }
        
        return results
    
    def test_voice_system(self) -> Dict[str, Any]:
        """Test voice system components."""
        print("\\n🎤 Testing voice system...")
        
        results = {
            "robust_adapter": {"available": False, "error": None},
            "enhanced_service": {"available": False, "error": None},
            "microphone": {"available": False, "error": None},
            "tts": {"available": False, "error": None},
            "integration": {"working": False, "error": None}
        }
        
        # Test robust voice adapter
        try:
            from services.robust_voice_adapter import create_voice_adapter
            
            adapter = create_voice_adapter()
            status = adapter.get_status()
            
            results["robust_adapter"]["available"] = True
            results["microphone"]["available"] = status.get("microphone_available", False)
            results["tts"]["available"] = status.get("tts_available", False)
            
            # Test voice capabilities
            if adapter.is_available:
                test_results = adapter.test_voice_capabilities()
                results["integration"]["working"] = test_results["tests_passed"] > 0
                
            adapter.safe_shutdown()
            print("  ✅ Robust voice adapter working")
            
        except Exception as e:
            results["robust_adapter"]["error"] = str(e)
            print(f"  ❌ Robust voice adapter failed: {e}")
        
        # Test enhanced voice service directly
        try:
            from services.enhanced_voice_service import EnhancedVoiceService
            
            service = EnhancedVoiceService()
            status = service.get_voice_status()
            
            results["enhanced_service"]["available"] = True
            if not results["microphone"]["available"]:
                results["microphone"]["available"] = status.get("microphone_available", False)
            if not results["tts"]["available"]:
                results["tts"]["available"] = status.get("tts_available", False)
            
            print("  ✅ Enhanced voice service working")
            
        except Exception as e:
            results["enhanced_service"]["error"] = str(e)
            print(f"  ❌ Enhanced voice service failed: {e}")
        
        return results
    
    def test_search_system(self) -> Dict[str, Any]:
        """Test search system components."""
        print("\\n🔍 Testing search system...")
        
        results = {
            "service_available": False,
            "engines": {},
            "test_search": {"success": False, "results_count": 0, "error": None}
        }
        
        try:
            from services.enhanced_web_search import EnhancedWebSearchService
            
            search = EnhancedWebSearchService()
            results["service_available"] = True
            
            # Test each search engine
            for engine_name in search.search_engines.keys():
                try:
                    test_results = search.search_engines[engine_name]("test query", 1)
                    results["engines"][engine_name] = {
                        "working": True,
                        "results_count": len(test_results) if test_results else 0
                    }
                    print(f"  ✅ {engine_name} working")
                except Exception as e:
                    results["engines"][engine_name] = {
                        "working": False,
                        "error": str(e)
                    }
                    print(f"  ❌ {engine_name} failed: {e}")
            
            # Test the "im alive" search specifically
            try:
                test_results = search.search("im alive", max_results=2)
                results["test_search"]["success"] = True
                results["test_search"]["results_count"] = len(test_results)
                print(f"  ✅ 'im alive' search returned {len(test_results)} results")
            except Exception as e:
                results["test_search"]["error"] = str(e)
                print(f"  ❌ 'im alive' search failed: {e}")
            
        except Exception as e:
            results["error"] = str(e)
            print(f"  ❌ Search system failed: {e}")
        
        return results
    
    def test_ai_brain(self) -> Dict[str, Any]:
        """Test AI brain integration."""
        print("\\n🧠 Testing AI brain...")
        
        results = {
            "initialization": {"success": False, "error": None},
            "voice_integration": {"working": False, "error": None},
            "search_integration": {"working": False, "error": None},
            "conversation": {"working": False, "error": None}
        }
        
        try:
            from ai_assistant_brain import AIAssistantBrain
            
            # Test initialization
            brain = AIAssistantBrain()
            results["initialization"]["success"] = True
            print("  ✅ AI brain initialization successful")
            
            # Test voice integration
            if brain.voice_adapter:
                results["voice_integration"]["working"] = True
                print("  ✅ Voice integration working")
            else:
                print("  ⚠️  Voice integration not available")
            
            # Test search integration
            if brain.search_service:
                results["search_integration"]["working"] = True
                print("  ✅ Search integration working")
            else:
                print("  ⚠️  Search integration not available")
            
            # Test conversation processing
            try:
                response = brain.process_input("hello")
                if response and len(response) > 0:
                    results["conversation"]["working"] = True
                    print("  ✅ Conversation processing working")
                else:
                    print("  ❌ Conversation processing returned empty response")
            except Exception as e:
                results["conversation"]["error"] = str(e)
                print(f"  ❌ Conversation processing failed: {e}")
            
            # Test specific "im alive" functionality
            try:
                response = brain.process_input("im alive")
                if "search" in response.lower() or "alive" in response.lower():
                    print("  ✅ 'im alive' functionality working")
                else:
                    print("  ⚠️  'im alive' functionality may not be working correctly")
            except Exception as e:
                print(f"  ❌ 'im alive' test failed: {e}")
            
            # Cleanup
            brain.stop()
            
        except Exception as e:
            results["initialization"]["error"] = str(e)
            print(f"  ❌ AI brain failed: {e}")
        
        return results
    
    def test_existing_architecture(self) -> Dict[str, Any]:
        """Test integration with existing project architecture."""
        print("\\n🏗️ Testing existing architecture integration...")
        
        results = {
            "intel_optimizer": {"available": False, "error": None},
            "voice_interfaces": {"available": False, "error": None},
            "api_routes": {"available": False, "error": None},
            "configuration": {"available": False, "error": None}
        }
        
        # Test Intel optimizer
        try:
            from services.intel_optimizer import IntelOptimizer
            
            optimizer = IntelOptimizer()
            hardware = optimizer.get_hardware_summary()
            
            results["intel_optimizer"]["available"] = True
            print(f"  ✅ Intel optimizer working (hardware: {hardware})")
            
        except Exception as e:
            results["intel_optimizer"]["error"] = str(e)
            print(f"  ❌ Intel optimizer failed: {e}")
        
        # Test voice interfaces
        try:
            from core.interfaces.voice_provider import IVoiceInput, IVoiceOutput
            
            results["voice_interfaces"]["available"] = True
            print("  ✅ Voice interfaces available")
            
        except Exception as e:
            results["voice_interfaces"]["error"] = str(e)
            print(f"  ⚠️  Voice interfaces not available: {e}")
        
        # Test API routes
        try:
            from api.routes import health
            
            results["api_routes"]["available"] = True
            print("  ✅ API routes available")
            
        except Exception as e:
            results["api_routes"]["error"] = str(e)
            print(f"  ⚠️  API routes not available: {e}")
        
        # Test configuration system
        try:
            from config.settings import get_settings
            
            settings = get_settings()
            
            results["configuration"]["available"] = True
            print("  ✅ Configuration system working")
            
        except Exception as e:
            results["configuration"]["error"] = str(e)
            print(f"  ⚠️  Configuration system issue: {e}")
        
        return results
    
    def run_integration_test(self) -> Dict[str, Any]:
        """Run end-to-end integration test."""
        print("\\n🔗 Running integration test...")
        
        results = {
            "full_system": {"working": False, "error": None},
            "voice_to_search": {"working": False, "error": None},
            "im_alive_test": {"working": False, "results": None, "error": None}
        }
        
        try:
            # Test full system startup
            from ai_assistant_brain import AIAssistantBrain
            
            brain = AIAssistantBrain()
            
            # Check if both voice and search are available
            if brain.voice_adapter and brain.search_service:
                results["full_system"]["working"] = True
                print("  ✅ Full system integration working")
                
                # Test the specific "im alive" integration
                try:
                    print("  🧪 Testing 'im alive' functionality...")
                    response = brain.process_input("im alive")
                    
                    # Wait a moment for any async operations
                    time.sleep(1)
                    
                    if response and ("search" in response.lower() or "alive" in response.lower()):
                        results["im_alive_test"]["working"] = True
                        results["im_alive_test"]["results"] = response
                        print("  ✅ 'im alive' integration test passed")
                    else:
                        print(f"  ⚠️  'im alive' test returned: {response}")
                        
                except Exception as e:
                    results["im_alive_test"]["error"] = str(e)
                    print(f"  ❌ 'im alive' integration test failed: {e}")
            else:
                missing = []
                if not brain.voice_adapter:
                    missing.append("voice")
                if not brain.search_service:
                    missing.append("search")
                print(f"  ⚠️  Full system integration limited (missing: {', '.join(missing)})")
            
            brain.stop()
            
        except Exception as e:
            results["full_system"]["error"] = str(e)
            print(f"  ❌ Integration test failed: {e}")
        
        return results
    
    def provide_recommendations(self) -> List[str]:
        """Provide recommendations based on test results."""
        recommendations = []
        
        # Check dependencies
        deps = self.results["component_tests"].get("dependencies", {})
        if deps and deps["summary"]["missing"] > 0:
            recommendations.append("Install missing dependencies with: pip install " + 
                                 " ".join([dep for category in deps["missing"].values() for dep in category]))
        
        # Check voice system
        voice = self.results["component_tests"].get("voice", {})
        if voice and not voice.get("microphone", {}).get("available", False):
            recommendations.append("Check microphone permissions and drivers for voice input")
        
        if voice and not voice.get("tts", {}).get("available", False):
            recommendations.append("Install additional TTS engines or check audio output")
        
        # Check search system
        search = self.results["component_tests"].get("search", {})
        if search and not search.get("service_available", False):
            recommendations.append("Check internet connection and search engine APIs")
        
        # Check integration
        integration = self.results["integration_tests"]
        if integration and not integration.get("full_system", {}).get("working", False):
            recommendations.append("Review component initialization order and error handling")
        
        # General recommendations
        if not recommendations:
            recommendations.append("System appears to be working well!")
            recommendations.append("Try running: python ai_assistant_brain.py --demo")
        
        return recommendations
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete system validation."""
        print("🚀 Intel AI Assistant - Comprehensive System Validation")
        print("=" * 60)
        
        start_time = time.time()
        
        # Component tests
        print("\\n📦 COMPONENT TESTS")
        print("-" * 30)
        
        self.results["component_tests"]["dependencies"] = self.validate_dependencies()
        self.results["component_tests"]["voice"] = self.test_voice_system()
        self.results["component_tests"]["search"] = self.test_search_system()
        self.results["component_tests"]["ai_brain"] = self.test_ai_brain()
        self.results["component_tests"]["existing_architecture"] = self.test_existing_architecture()
        
        # Integration tests
        print("\\n🔗 INTEGRATION TESTS")
        print("-" * 30)
        
        self.results["integration_tests"] = self.run_integration_test()
        
        # Generate recommendations
        self.results["recommendations"] = self.provide_recommendations()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Validation completed in {duration:.2f} seconds")
        
        # Component summary
        working_components = 0
        total_components = 0
        
        for component, results in self.results["component_tests"].items():
            if component == "dependencies":
                continue
            total_components += 1
            if self._is_component_working(results):
                working_components += 1
        
        print(f"Working components: {working_components}/{total_components}")
        
        # Dependencies summary
        deps = self.results["component_tests"]["dependencies"]
        print(f"Dependencies: {deps['summary']['available']}/{deps['summary']['total_dependencies']} available " +
              f"({deps['summary']['success_rate']:.1f}%)")
        
        # Integration summary
        integration_working = self.results["integration_tests"].get("full_system", {}).get("working", False)
        print(f"Integration: {'✅ Working' if integration_working else '❌ Issues detected'}")
        
        # IM Alive test
        im_alive_working = self.results["integration_tests"].get("im_alive_test", {}).get("working", False)
        print(f"'Im Alive' test: {'✅ Passed' if im_alive_working else '⚠️ Issues detected'}")
        
        # Recommendations
        print("\\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(self.results["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        # Overall status
        overall_success = (
            working_components >= total_components * 0.7 and  # 70% components working
            deps['summary']['success_rate'] >= 70 and  # 70% dependencies available
            integration_working  # Integration working
        )
        
        print("\\n" + "=" * 60)
        if overall_success:
            print("🎉 SYSTEM VALIDATION PASSED! 🎉")
            print("Your Intel AI Assistant is ready to use!")
        else:
            print("⚠️ SYSTEM VALIDATION COMPLETED WITH ISSUES")
            print("Please address the recommendations above.")
        
        print("=" * 60)
        
        return self.results
    
    def _is_component_working(self, component_results: Dict[str, Any]) -> bool:
        """Check if a component is considered working."""
        if isinstance(component_results, dict):
            if "available" in component_results:
                return component_results["available"]
            if "working" in component_results:
                return component_results["working"]
            if "success" in component_results:
                return component_results["success"]
            # Count sub-components
            working_count = 0
            total_count = 0
            for v in component_results.values():
                if isinstance(v, dict):
                    total_count += 1
                    if v.get("available") or v.get("working"):
                        working_count += 1
                elif isinstance(v, bool):
                    total_count += 1
                    if v:
                        working_count += 1
            return working_count > total_count * 0.5 if total_count > 0 else False
        return False
    
    def save_report(self, filename: str = None) -> str:
        """Save validation report to file."""
        if not filename:
            filename = f"validation_report_{int(time.time())}.json"
        
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"\\n📄 Validation report saved: {filename}")
            return filename
        except Exception as e:
            print(f"Failed to save report: {e}")
            return ""

def main():
    """Main entry point."""
    validator = ComprehensiveValidator()
    
    try:
        results = validator.run_complete_validation()
        
        # Save report
        report_file = validator.save_report()
        
        # Return appropriate exit code
        integration_working = results["integration_tests"].get("full_system", {}).get("working", False)
        exit_code = 0 if integration_working else 1
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\\n🛑 Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\\n❌ Validation failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)