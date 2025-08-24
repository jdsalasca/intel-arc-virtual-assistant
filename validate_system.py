#!/usr/bin/env python3
"""
Intel AI Assistant System Validation
Validates the complete system setup and runs basic functionality tests.
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class SystemValidator:
    """Validates the Intel AI Assistant system."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = project_root
        self.validation_results: Dict[str, Any] = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        if level == "ERROR":
            print(f"[{timestamp}] ❌ {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        else:
            print(f"[{timestamp}] ℹ️  {message}")
    
    def validate_python_version(self) -> bool:
        """Validate Python version compatibility."""
        self.log("Validating Python version...")
        
        required_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version >= required_version:
            self.log(f"Python {'.'.join(map(str, current_version))} is compatible", "SUCCESS")
            self.validation_results["python_version"] = {
                "valid": True,
                "current": current_version,
                "required": required_version
            }
            return True
        else:
            self.log(f"Python {'.'.join(map(str, current_version))} is too old. Required: {'.'.join(map(str, required_version))}", "ERROR")
            self.validation_results["python_version"] = {
                "valid": False,
                "current": current_version,
                "required": required_version
            }
            return False
    
    def validate_project_structure(self) -> bool:
        """Validate project directory structure."""
        self.log("Validating project structure...")
        
        required_dirs = [
            "config",
            "core",
            "services", 
            "providers",
            "api",
            "web",
            "tests"
        ]
        
        required_files = [
            "main.py",
            "requirements.txt",
            "pytest.ini",
            "conftest.py",
            "run_tests.py"
        ]
        
        missing_dirs = []
        missing_files = []
        
        # Check directories
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
            elif self.verbose:
                self.log(f"Found directory: {dir_name}")
        
        # Check files
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                missing_files.append(file_name)
            elif self.verbose:
                self.log(f"Found file: {file_name}")
        
        if missing_dirs or missing_files:
            if missing_dirs:
                self.log(f"Missing directories: {', '.join(missing_dirs)}", "ERROR")
            if missing_files:
                self.log(f"Missing files: {', '.join(missing_files)}", "ERROR")
            
            self.validation_results["project_structure"] = {
                "valid": False,
                "missing_dirs": missing_dirs,
                "missing_files": missing_files
            }
            return False
        else:
            self.log("Project structure is valid", "SUCCESS")
            self.validation_results["project_structure"] = {"valid": True}
            return True
    
    def validate_dependencies(self) -> bool:
        """Validate required dependencies."""
        self.log("Validating dependencies...")
        
        core_dependencies = [
            "fastapi",
            "uvicorn", 
            "pydantic",
            "psutil"
        ]
        
        test_dependencies = [
            "pytest",
            "pytest_asyncio",
            "pytest_cov"
        ]
        
        optional_dependencies = [
            "openvino_genai",
            "langchain",
            "transformers"
        ]
        
        def check_dependency(dep_name: str) -> bool:
            try:
                __import__(dep_name.replace("-", "_"))
                return True
            except ImportError:
                return False
        
        core_missing = []
        test_missing = []
        optional_missing = []
        
        # Check core dependencies
        for dep in core_dependencies:
            if not check_dependency(dep):
                core_missing.append(dep)
            elif self.verbose:
                self.log(f"Found core dependency: {dep}")
        
        # Check test dependencies
        for dep in test_dependencies:
            if not check_dependency(dep):
                test_missing.append(dep)
            elif self.verbose:
                self.log(f"Found test dependency: {dep}")
        
        # Check optional dependencies
        for dep in optional_dependencies:
            if not check_dependency(dep):
                optional_missing.append(dep)
            elif self.verbose:
                self.log(f"Found optional dependency: {dep}")
        
        self.validation_results["dependencies"] = {
            "core_missing": core_missing,
            "test_missing": test_missing,
            "optional_missing": optional_missing
        }
        
        if core_missing:
            self.log(f"Missing core dependencies: {', '.join(core_missing)}", "ERROR")
            self.log("Install with: pip install " + " ".join(core_missing), "INFO")
            return False
        
        if test_missing:
            self.log(f"Missing test dependencies: {', '.join(test_missing)}", "WARNING")
            self.log("Install with: pip install " + " ".join(test_missing), "INFO")
        
        if optional_missing:
            self.log(f"Missing optional dependencies: {', '.join(optional_missing)}", "WARNING")
        
        self.log("Core dependencies are satisfied", "SUCCESS")
        return True
    
    def validate_configuration_system(self) -> bool:
        """Validate configuration system."""
        self.log("Validating configuration system...")
        
        try:
            # Test configuration imports
            from config import ApplicationSettings, EnvironmentManager, IntelProfileManager
            self.log("Configuration imports successful")
            
            # Test Intel profile manager
            profile_manager = IntelProfileManager()
            profiles = profile_manager.list_profiles()
            if len(profiles) > 0:
                self.log(f"Found {len(profiles)} Intel profiles")
            else:
                self.log("No Intel profiles found", "WARNING")
            
            # Test environment manager
            from unittest.mock import patch
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                env_manager = EnvironmentManager()
                validation = env_manager.validate_environment()
                
                if validation.get("valid", False):
                    self.log("Environment validation passed")
                else:
                    self.log("Environment validation has issues", "WARNING")
                    if self.verbose:
                        for error in validation.get("errors", []):
                            self.log(f"Environment error: {error}", "ERROR")
                        for warning in validation.get("warnings", []):
                            self.log(f"Environment warning: {warning}", "WARNING")
            
            # Test application settings
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                settings = ApplicationSettings()
                issues = settings.validate_settings()
                
                if len(issues) == 0:
                    self.log("Application settings validation passed")
                else:
                    self.log("Application settings have issues", "WARNING")
                    if self.verbose:
                        for issue in issues:
                            self.log(f"Settings issue: {issue}", "WARNING")
            
            self.validation_results["configuration_system"] = {
                "valid": True,
                "profiles_count": len(profiles),
                "env_validation": validation,
                "settings_issues": issues
            }
            
            self.log("Configuration system validation passed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Configuration system validation failed: {e}", "ERROR")
            if self.verbose:
                self.log(traceback.format_exc())
            
            self.validation_results["configuration_system"] = {
                "valid": False,
                "error": str(e)
            }
            return False
    
    def validate_api_system(self) -> bool:
        """Validate API system."""
        self.log("Validating API system...")
        
        try:
            # Test FastAPI imports
            from fastapi import FastAPI
            from api.routes.health import router as health_router
            self.log("API imports successful")
            
            # Test route creation
            app = FastAPI()
            app.include_router(health_router, prefix="/api/v1/health")
            self.log("API routes loaded successfully")
            
            self.validation_results["api_system"] = {"valid": True}
            self.log("API system validation passed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"API system validation failed: {e}", "ERROR")
            if self.verbose:
                self.log(traceback.format_exc())
            
            self.validation_results["api_system"] = {
                "valid": False,
                "error": str(e)
            }
            return False
    
    def validate_test_system(self) -> bool:
        """Validate test system."""
        self.log("Validating test system...")
        
        try:
            # Check pytest configuration
            pytest_ini = self.project_root / "pytest.ini"
            if pytest_ini.exists():
                self.log("Found pytest.ini")
            else:
                self.log("pytest.ini not found", "WARNING")
            
            # Check conftest.py
            conftest = self.project_root / "conftest.py"
            if conftest.exists():
                self.log("Found conftest.py")
            else:
                self.log("conftest.py not found", "WARNING")
            
            # Check test directories
            test_dirs = ["unit", "integration", "performance", "benchmarks"]
            test_path = self.project_root / "tests"
            
            existing_test_dirs = []
            for test_dir in test_dirs:
                test_subdir = test_path / test_dir
                if test_subdir.exists():
                    existing_test_dirs.append(test_dir)
                    # Count test files
                    test_files = list(test_subdir.glob("test_*.py"))
                    if self.verbose and test_files:
                        self.log(f"Found {len(test_files)} test files in {test_dir}")
            
            # Test pytest import
            import pytest
            self.log("pytest import successful")
            
            self.validation_results["test_system"] = {
                "valid": True,
                "pytest_ini_exists": pytest_ini.exists(),
                "conftest_exists": conftest.exists(),
                "test_directories": existing_test_dirs
            }
            
            self.log("Test system validation passed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Test system validation failed: {e}", "ERROR")
            if self.verbose:
                self.log(traceback.format_exc())
            
            self.validation_results["test_system"] = {
                "valid": False,
                "error": str(e)
            }
            return False
    
    def run_basic_functionality_test(self) -> bool:
        """Run basic functionality test."""
        self.log("Running basic functionality test...")
        
        try:
            from unittest.mock import patch
            
            # Test configuration initialization
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                from config import initialize_settings, initialize_environment
                
                env_manager = initialize_environment()
                settings = initialize_settings()
                
                self.log("Configuration initialization successful")
            
            # Test Intel profile operations
            from config import IntelProfileManager
            profile_manager = IntelProfileManager()
            
            # Test profile operations
            profiles = profile_manager.list_profiles()
            if profiles:
                test_profile = profiles[0]
                profile_info = profile_manager.get_profile_details(test_profile)
                model_config = profile_manager.get_model_config("qwen2.5-7b-int4", test_profile)
                recommendations = profile_manager.optimize_for_profile(test_profile)
                
                if all([profile_info, model_config, recommendations]):
                    self.log("Intel profile operations successful")
                else:
                    self.log("Some Intel profile operations failed", "WARNING")
            
            # Test settings operations
            with patch('config.settings.ApplicationSettings._auto_configure_intel_hardware'):
                settings = initialize_settings()
                
                # Test setting operations
                original_temp = settings.model.temperature
                settings.update_setting("model", "temperature", 0.5)
                updated_temp = settings.get_setting("model", "temperature")
                
                if updated_temp == 0.5:
                    self.log("Settings operations successful")
                    # Restore original value
                    settings.update_setting("model", "temperature", original_temp)
                else:
                    self.log("Settings operations failed", "WARNING")
            
            self.validation_results["basic_functionality"] = {"valid": True}
            self.log("Basic functionality test passed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Basic functionality test failed: {e}", "ERROR")
            if self.verbose:
                self.log(traceback.format_exc())
            
            self.validation_results["basic_functionality"] = {
                "valid": False,
                "error": str(e)
            }
            return False
    
    def run_sample_tests(self) -> bool:
        """Run a few sample tests to verify test system."""
        self.log("Running sample tests...")
        
        try:
            import subprocess
            
            # Run a simple unit test
            command = [
                sys.executable, "-m", "pytest",
                "tests/unit/test_intel_profiles.py::TestHardwareCapabilities::test_default_initialization",
                "-v",
                "--tb=short"
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log("Sample unit test passed")
                sample_success = True
            else:
                self.log("Sample unit test failed", "WARNING")
                if self.verbose:
                    self.log(f"Test output: {result.stdout}")
                    self.log(f"Test errors: {result.stderr}")
                sample_success = False
            
            self.validation_results["sample_tests"] = {
                "valid": sample_success,
                "return_code": result.returncode
            }
            
            if sample_success:
                self.log("Sample tests passed", "SUCCESS")
            
            return sample_success
            
        except Exception as e:
            self.log(f"Sample tests failed: {e}", "ERROR")
            if self.verbose:
                self.log(traceback.format_exc())
            
            self.validation_results["sample_tests"] = {
                "valid": False,
                "error": str(e)
            }
            return False
    
    def generate_validation_report(self, output_file: str = "validation_report.json") -> bool:
        """Generate validation report."""
        self.log("Generating validation report...")
        
        summary = {
            "total_checks": len(self.validation_results),
            "passed_checks": sum(1 for r in self.validation_results.values() if r.get("valid", False)),
            "overall_valid": all(r.get("valid", False) for r in self.validation_results.values())
        }
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": sys.version,
            "platform": sys.platform,
            "project_root": str(self.project_root),
            "summary": summary,
            "validation_results": self.validation_results
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.log(f"Validation report saved to: {output_file}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to save validation report: {e}", "ERROR")
            return False
    
    def validate_system(self) -> bool:
        """Run complete system validation."""
        self.log("🚀 Starting Intel AI Assistant System Validation")
        self.log("=" * 60)
        
        start_time = time.time()
        
        validation_steps = [
            ("Python Version", self.validate_python_version),
            ("Project Structure", self.validate_project_structure),
            ("Dependencies", self.validate_dependencies),
            ("Configuration System", self.validate_configuration_system),
            ("API System", self.validate_api_system),
            ("Test System", self.validate_test_system),
            ("Basic Functionality", self.run_basic_functionality_test),
            ("Sample Tests", self.run_sample_tests),
        ]
        
        all_valid = True
        
        for step_name, step_func in validation_steps:
            self.log(f"\n{'=' * 40}")
            self.log(f"Validating: {step_name}")
            self.log(f"{'=' * 40}")
            
            try:
                valid = step_func()
                if not valid:
                    all_valid = False
            except Exception as e:
                self.log(f"Validation step '{step_name}' failed with exception: {e}", "ERROR")
                all_valid = False
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.log(f"\n{'=' * 60}")
        self.log("VALIDATION SUMMARY")
        self.log(f"{'=' * 60}")
        self.log(f"Total duration: {duration:.2f} seconds")
        self.log(f"Validation steps: {len(self.validation_results)}")
        
        passed_count = sum(1 for r in self.validation_results.values() if r.get("valid", False))
        self.log(f"Passed: {passed_count}")
        self.log(f"Failed: {len(self.validation_results) - passed_count}")
        
        if all_valid:
            self.log("\n🎉 SYSTEM VALIDATION PASSED! 🎉", "SUCCESS")
            self.log("The Intel AI Assistant system is ready for use.")
        else:
            self.log("\n❌ SYSTEM VALIDATION FAILED", "ERROR")
            self.log("Please address the issues above before proceeding.")
        
        # Generate report
        report_file = f"validation_report_{int(time.time())}.json"
        self.generate_validation_report(report_file)
        
        self.log(f"{'=' * 60}")
        
        return all_valid

def main():
    """Main entry point for system validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Intel AI Assistant System Validator")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--quick", action="store_true", help="Quick validation (skip sample tests)")
    
    args = parser.parse_args()
    
    validator = SystemValidator(verbose=args.verbose)
    
    if args.quick:
        # Skip sample tests for quick validation
        validator.validation_steps = validator.validation_steps[:-1]
    
    success = validator.validate_system()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()