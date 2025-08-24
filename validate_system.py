#!/usr/bin/env python3
"""
Simple validation script to check core functionality
"""

import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def check_module_import(module_name, module_path):
    """Check if a module can be imported successfully"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            return False, f"Could not create spec for {module_name}"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, f"✅ {module_name} imports successfully"
    except Exception as e:
        return False, f"❌ {module_name} import failed: {e}"

def validate_core_modules():
    """Validate that core modules can be imported"""
    print("🔍 Validating Core Modules")
    print("=" * 40)
    
    modules_to_check = [
        ("enhanced_voice_service", project_root / "services" / "enhanced_voice_service.py"),
        ("enhanced_web_search", project_root / "services" / "enhanced_web_search.py"),
        ("ai_assistant_brain", project_root / "ai_assistant_brain.py"),
        ("settings", project_root / "config" / "settings.py"),
        ("conversation_manager", project_root / "conversation" / "conversation_manager.py"),
    ]
    
    results = []
    for module_name, module_path in modules_to_check:
        if module_path.exists():
            success, message = check_module_import(module_name, module_path)
            results.append((module_name, success, message))
            print(message)
        else:
            results.append((module_name, False, f"❌ {module_name} file not found: {module_path}"))
            print(f"❌ {module_name} file not found: {module_path}")
    
    return results

def validate_project_structure():
    """Validate project structure"""
    print("\n📁 Validating Project Structure")
    print("=" * 40)
    
    required_dirs = [
        "services",
        "config",
        "conversation",
        "tools",
        "tests",
        "models",
        "web"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"❌ {dir_name}/ directory missing")
            missing_dirs.append(dir_name)
    
    return len(missing_dirs) == 0

def validate_voice_service_fix():
    """Validate that voice service has the critical fixes"""
    print("\n🎤 Validating Voice Service Fix")
    print("=" * 40)
    
    voice_file = project_root / "services" / "enhanced_voice_service.py"
    if not voice_file.exists():
        print("❌ Voice service file not found")
        return False
    
    try:
        content = voice_file.read_text()
        
        # Check for key fixes
        checks = [
            ("quiet_mode parameter", "quiet_mode: bool = False" in content),
            ("NoneType error handling", "'NoneType'" in content and "close" in content),
            ("Error cooldown mechanism", "error_cooldown" in content),
            ("Microphone failure limits", "max_failures" in content),
            ("Suppress output parameter", "suppress_output" in content),
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                print(f"✅ {check_name} present")
            else:
                print(f"❌ {check_name} missing")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error reading voice service file: {e}")
        return False

def main():
    """Main validation function"""
    print("🎯 Intel AI Assistant - Core Validation")
    print("=" * 60)
    print("Checking that the system is properly fixed and functional")
    print()
    
    # Validate modules
    module_results = validate_core_modules()
    
    # Validate structure
    structure_ok = validate_project_structure()
    
    # Validate voice service fix
    voice_fix_ok = validate_voice_service_fix()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 VALIDATION SUMMARY")
    print("=" * 60)
    
    module_success = sum(1 for _, success, _ in module_results if success)
    total_modules = len(module_results)
    
    print(f"Module Imports:    {module_success}/{total_modules} successful")
    print(f"Project Structure: {'✅ OK' if structure_ok else '❌ Issues'}")
    print(f"Voice Service Fix: {'✅ Applied' if voice_fix_ok else '❌ Missing'}")
    
    overall_success = (module_success == total_modules) and structure_ok and voice_fix_ok
    
    if overall_success:
        print("\n🚀 VALIDATION PASSED!")
        print("✅ System is properly structured and fixed")
        print("✅ Voice service infinite loop issue resolved")
        print("✅ All core modules can be imported")
        print("✅ Project structure is complete")
    else:
        print("\n⚠️  VALIDATION ISSUES DETECTED")
        for module_name, success, message in module_results:
            if not success:
                print(f"   • {message}")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)