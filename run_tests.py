#!/usr/bin/env python3
"""
Intel AI Assistant Test Runner
Comprehensive test execution script with Intel hardware optimization.
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """Main test runner for Intel AI Assistant."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = project_root
        self.test_results: Dict[str, Any] = {}
        
    def run_command(self, command: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        if self.verbose:
            print(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root
            )
            return result
        except Exception as e:
            print(f"Error running command {' '.join(command)}: {e}")
            return subprocess.CompletedProcess(command, 1, "", str(e))
    
    def check_dependencies(self) -> bool:
        """Check if test dependencies are available."""
        print("🔍 Checking test dependencies...")
        
        dependencies = ["pytest", "pytest-asyncio", "pytest-cov", "pytest-benchmark"]
        missing = []
        
        for dep in dependencies:
            result = self.run_command([sys.executable, "-c", f"import {dep.replace('-', '_')}"])
            if result.returncode != 0:
                missing.append(dep)
        
        if missing:
            print(f"❌ Missing dependencies: {', '.join(missing)}")
            print("Install with: pip install " + " ".join(missing))
            return False
        
        print("✅ All test dependencies available")
        return True
    
    def validate_environment(self) -> bool:
        """Validate test environment."""
        print("🔧 Validating test environment...")
        
        # Check project structure
        required_dirs = ["tests", "config", "core", "services"]
        missing_dirs = []
        
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            print(f"❌ Missing directories: {', '.join(missing_dirs)}")
            return False
        
        # Check test directories
        test_dirs = ["unit", "integration", "performance", "benchmarks"]
        test_path = self.project_root / "tests"
        
        for test_dir in test_dirs:
            test_subdir = test_path / test_dir
            if not test_subdir.exists():
                print(f"⚠️  Creating missing test directory: {test_subdir}")
                test_subdir.mkdir(parents=True, exist_ok=True)
        
        print("✅ Test environment validated")
        return True
    
    def run_unit_tests(self, coverage: bool = True) -> bool:
        """Run unit tests."""
        print("🧪 Running unit tests...")
        
        command = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v",
            "--tb=short",
            "-m", "unit or not slow"
        ]
        
        if coverage:
            command.extend([
                "--cov=config",
                "--cov=core", 
                "--cov=services",
                "--cov-report=term-missing",
                "--cov-report=html:tests/coverage/unit"
            ])
        
        result = self.run_command(command, capture_output=False)
        
        success = result.returncode == 0
        self.test_results["unit_tests"] = {
            "success": success,
            "return_code": result.returncode
        }
        
        if success:
            print("✅ Unit tests passed")
        else:
            print("❌ Unit tests failed")
        
        return success
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        command = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "-m", "integration or not slow"
        ]
        
        result = self.run_command(command, capture_output=False)
        
        success = result.returncode == 0
        self.test_results["integration_tests"] = {
            "success": success,
            "return_code": result.returncode
        }
        
        if success:
            print("✅ Integration tests passed")
        else:
            print("❌ Integration tests failed")
        
        return success
    
    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        print("⚡ Running performance tests...")
        
        command = [
            sys.executable, "-m", "pytest",
            "tests/performance/",
            "-v",
            "--tb=short",
            "-m", "performance"
        ]
        
        result = self.run_command(command, capture_output=False)
        
        success = result.returncode == 0
        self.test_results["performance_tests"] = {
            "success": success,
            "return_code": result.returncode
        }
        
        if success:
            print("✅ Performance tests passed")
        else:
            print("❌ Performance tests failed")
        
        return success
    
    def run_benchmarks(self, output_file: Optional[str] = None) -> bool:
        """Run benchmark tests."""
        print("📊 Running benchmarks...")
        
        command = [
            sys.executable, "-m", "pytest",
            "tests/benchmarks/",
            "-v",
            "--tb=short",
            "-m", "benchmark",
            "--benchmark-only",
            "--benchmark-sort=mean"
        ]
        
        if output_file:
            command.extend([
                f"--benchmark-json={output_file}"
            ])
        
        result = self.run_command(command, capture_output=False)
        
        success = result.returncode == 0
        self.test_results["benchmarks"] = {
            "success": success,
            "return_code": result.returncode,
            "output_file": output_file
        }
        
        if success:
            print("✅ Benchmarks completed")
        else:
            print("❌ Benchmarks failed")
        
        return success
    
    def run_intel_specific_tests(self) -> bool:
        """Run Intel hardware specific tests."""
        print("💻 Running Intel-specific tests...")
        
        # Check if Intel hardware flags are set
        intel_flags = {
            "gpu": os.getenv("INTEL_ARC_GPU_AVAILABLE") == "true",
            "npu": os.getenv("INTEL_NPU_AVAILABLE") == "true"
        }
        
        if not any(intel_flags.values()):
            print("⚠️  No Intel hardware flags set, running CPU-only tests")
            marker = "intel and not gpu and not npu"
        else:
            marker = "intel"
        
        command = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "-m", marker
        ]
        
        result = self.run_command(command, capture_output=False)
        
        success = result.returncode == 0
        self.test_results["intel_tests"] = {
            "success": success,
            "return_code": result.returncode,
            "hardware_flags": intel_flags
        }
        
        if success:
            print("✅ Intel-specific tests passed")
        else:
            print("❌ Intel-specific tests failed")
        
        return success
    
    def run_slow_tests(self) -> bool:
        """Run slow/comprehensive tests."""
        print("🐌 Running slow tests...")
        
        command = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "-m", "slow",
            "--timeout=600"  # 10 minute timeout for slow tests
        ]
        
        result = self.run_command(command, capture_output=False)
        
        success = result.returncode == 0
        self.test_results["slow_tests"] = {
            "success": success,
            "return_code": result.returncode
        }
        
        if success:
            print("✅ Slow tests passed")
        else:
            print("❌ Slow tests failed")
        
        return success
    
    def run_network_tests(self) -> bool:
        """Run network-dependent tests."""
        if os.getenv("ENABLE_NETWORK_TESTS") != "true":
            print("⚠️  Network tests disabled (set ENABLE_NETWORK_TESTS=true to enable)")
            return True
        
        print("🌐 Running network tests...")
        
        command = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "-m", "network"
        ]
        
        result = self.run_command(command, capture_output=False)
        
        success = result.returncode == 0
        self.test_results["network_tests"] = {
            "success": success,
            "return_code": result.returncode
        }
        
        if success:
            print("✅ Network tests passed")
        else:
            print("❌ Network tests failed")
        
        return success
    
    def generate_test_report(self, output_file: str = "test_report.json") -> bool:
        """Generate comprehensive test report."""
        print("📋 Generating test report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": sys.version,
            "platform": sys.platform,
            "project_root": str(self.project_root),
            "environment": {
                "intel_arc_gpu": os.getenv("INTEL_ARC_GPU_AVAILABLE", "false"),
                "intel_npu": os.getenv("INTEL_NPU_AVAILABLE", "false"),
                "network_tests": os.getenv("ENABLE_NETWORK_TESTS", "false")
            },
            "test_results": self.test_results,
            "summary": {
                "total_test_suites": len(self.test_results),
                "passed_test_suites": sum(1 for r in self.test_results.values() if r.get("success", False)),
                "overall_success": all(r.get("success", False) for r in self.test_results.values())
            }
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"✅ Test report saved to: {output_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to save test report: {e}")
            return False
    
    def run_all_tests(self, include_slow: bool = False, include_benchmarks: bool = False) -> bool:
        """Run all test suites."""
        print("🚀 Running complete test suite for Intel AI Assistant")
        print("=" * 60)
        
        start_time = time.time()
        
        # Check prerequisites
        if not self.check_dependencies():
            return False
        
        if not self.validate_environment():
            return False
        
        # Run test suites
        test_suites = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Intel-Specific Tests", self.run_intel_specific_tests),
            ("Network Tests", self.run_network_tests),
        ]
        
        if include_slow:
            test_suites.append(("Slow Tests", self.run_slow_tests))
        
        if include_benchmarks:
            benchmark_output = f"benchmark_results_{int(time.time())}.json"
            test_suites.append(("Benchmarks", lambda: self.run_benchmarks(benchmark_output)))
        
        # Execute test suites
        all_passed = True
        for suite_name, suite_func in test_suites:
            print(f"\n{'=' * 60}")
            print(f"Running {suite_name}")
            print(f"{'=' * 60}")
            
            try:
                success = suite_func()
                if not success:
                    all_passed = False
            except Exception as e:
                print(f"❌ {suite_name} failed with exception: {e}")
                all_passed = False
        
        # Generate report
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n{'=' * 60}")
        print("TEST SUITE SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total duration: {duration:.2f} seconds")
        print(f"Test suites run: {len(self.test_results)}")
        
        passed_count = sum(1 for r in self.test_results.values() if r.get("success", False))
        print(f"Passed: {passed_count}")
        print(f"Failed: {len(self.test_results) - passed_count}")
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! 🎉")
        else:
            print("\n❌ SOME TESTS FAILED")
        
        # Generate detailed report
        report_file = f"test_report_{int(time.time())}.json"
        self.generate_test_report(report_file)
        
        print(f"{'=' * 60}")
        
        return all_passed

def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Intel AI Assistant Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance", action="store_true", help="Run only performance tests")
    parser.add_argument("--benchmarks", action="store_true", help="Run only benchmarks")
    parser.add_argument("--intel", action="store_true", help="Run only Intel-specific tests")
    parser.add_argument("--slow", action="store_true", help="Include slow tests")
    parser.add_argument("--network", action="store_true", help="Run only network tests")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose)
    
    success = True
    
    if args.unit:
        success = runner.run_unit_tests(coverage=not args.no_coverage)
    elif args.integration:
        success = runner.run_integration_tests()
    elif args.performance:
        success = runner.run_performance_tests()
    elif args.benchmarks:
        benchmark_file = f"benchmark_results_{int(time.time())}.json"
        success = runner.run_benchmarks(benchmark_file)
    elif args.intel:
        success = runner.run_intel_specific_tests()
    elif args.network:
        success = runner.run_network_tests()
    elif args.all or not any([args.unit, args.integration, args.performance, args.benchmarks, args.intel, args.network]):
        success = runner.run_all_tests(include_slow=args.slow, include_benchmarks=args.benchmarks)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()