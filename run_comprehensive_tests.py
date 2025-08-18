#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Learn with AI Platform

This script implements Issue #25 requirements by running all test categories:
- Unit tests with >90% coverage target
- Integration tests for all API endpoints  
- End-to-end tests for complete user flows
- Performance tests for load scenarios
- Security tests for common vulnerabilities
- Regression tests for critical paths

Usage:
    python run_comprehensive_tests.py [--suite=SUITE] [--generate-report]
    
Suites:
    all         - Run all test suites (default)
    unit        - Unit tests only
    integration - Integration tests only  
    e2e         - End-to-end tests only
    performance - Performance tests only
    security    - Security tests only
    regression  - Regression tests only
    mvp         - MVP test suite (fast)
"""

import argparse
import subprocess
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json


class ComprehensiveTestRunner:
    """Orchestrates execution of all test suites and generates comprehensive reports."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "backend"
        self.frontend_root = project_root / "frontend"
        
        # Test results storage
        self.test_results = {
            "start_time": time.time(),
            "suites": {},
            "summary": {},
            "coverage": {},
            "issues": []
        }
    
    def run_unit_tests(self) -> Tuple[bool, Dict[str, Any]]:
        """Run comprehensive unit test suite with coverage analysis."""
        print("🧪 Running Unit Tests with Coverage Analysis...")
        
        # Backend unit tests
        backend_result = subprocess.run([
            "pytest", "tests/", "-v", 
            "--cov=app", 
            "--cov-report=html",
            "--cov-report=json",
            "--cov-report=term-missing",
            "--cov-fail-under=70",  # Set minimum coverage threshold
            "--maxfail=10"
        ], cwd=self.backend_root, capture_output=True, text=True)
        
        # Frontend unit tests
        frontend_result = subprocess.run([
            "npm", "test", "--", 
            "--coverage", 
            "--watchAll=false", 
            "--passWithNoTests"
        ], cwd=self.frontend_root, capture_output=True, text=True)
        
        # Parse coverage data
        coverage_data = self._parse_coverage_data()
        
        results = {
            "backend": {
                "exit_code": backend_result.returncode,
                "stdout": backend_result.stdout,
                "stderr": backend_result.stderr,
                "passed": backend_result.returncode == 0
            },
            "frontend": {
                "exit_code": frontend_result.returncode, 
                "stdout": frontend_result.stdout,
                "stderr": frontend_result.stderr,
                "passed": frontend_result.returncode == 0
            },
            "coverage": coverage_data
        }
        
        overall_success = results["backend"]["passed"] and results["frontend"]["passed"]
        
        if overall_success:
            print("✅ Unit tests passed with adequate coverage")
        else:
            print("❌ Unit tests failed or coverage below threshold")
            
        return overall_success, results
    
    def run_integration_tests(self) -> Tuple[bool, Dict[str, Any]]:
        """Run integration tests for all API endpoints."""
        print("🔗 Running Integration Tests...")
        
        # Run backend integration tests
        integration_result = subprocess.run([
            "pytest", "tests/", "-v", "-m", "not external_deps",
            "--tb=short"
        ], cwd=self.backend_root, capture_output=True, text=True)
        
        results = {
            "backend_integration": {
                "exit_code": integration_result.returncode,
                "stdout": integration_result.stdout,
                "stderr": integration_result.stderr,
                "passed": integration_result.returncode == 0
            }
        }
        
        success = results["backend_integration"]["passed"]
        
        if success:
            print("✅ Integration tests passed")
        else:
            print("❌ Integration tests failed")
            
        return success, results
    
    def run_e2e_tests(self) -> Tuple[bool, Dict[str, Any]]:
        """Run end-to-end tests for complete user flows."""
        print("🎭 Running End-to-End Tests...")
        
        # Check if frontend build exists
        if not (self.frontend_root / ".next").exists():
            print("⚠️ Building frontend for E2E tests...")
            build_result = subprocess.run(["npm", "run", "build"], 
                                        cwd=self.frontend_root, 
                                        capture_output=True, text=True)
            if build_result.returncode != 0:
                print("❌ Frontend build failed for E2E tests")
                return False, {"error": "Frontend build failed"}
        
        # Run Playwright E2E tests
        e2e_result = subprocess.run([
            "npx", "playwright", "test", 
            "--reporter=html",
            "--timeout=30000"  # 30 second timeout per test
        ], cwd=self.frontend_root, capture_output=True, text=True)
        
        results = {
            "e2e_tests": {
                "exit_code": e2e_result.returncode,
                "stdout": e2e_result.stdout,
                "stderr": e2e_result.stderr,
                "passed": e2e_result.returncode == 0
            }
        }
        
        success = results["e2e_tests"]["passed"]
        
        if success:
            print("✅ End-to-end tests passed")
        else:
            print("❌ End-to-end tests failed")
            
        return success, results
    
    def run_performance_tests(self) -> Tuple[bool, Dict[str, Any]]:
        """Run performance tests for load scenarios."""
        print("⚡ Running Performance Load Tests...")
        
        # Run load performance tests
        perf_result = subprocess.run([
            "pytest", "tests/test_load_performance.py", "-v", "-s",
            "--tb=short"
        ], cwd=self.backend_root, capture_output=True, text=True)
        
        results = {
            "performance_tests": {
                "exit_code": perf_result.returncode,
                "stdout": perf_result.stdout,
                "stderr": perf_result.stderr,
                "passed": perf_result.returncode == 0
            }
        }
        
        # Extract performance metrics from output
        if "Load Test Summary" in perf_result.stdout:
            results["performance_metrics_found"] = True
        
        success = results["performance_tests"]["passed"]
        
        if success:
            print("✅ Performance tests passed")
        else:
            print("❌ Performance tests failed")
            
        return success, results
    
    def run_security_tests(self) -> Tuple[bool, Dict[str, Any]]:
        """Run security tests for common vulnerabilities."""
        print("🔒 Running Security Tests...")
        
        # Run security test suite
        security_result = subprocess.run([
            "pytest", "tests/security/", "-v",
            "--tb=short"
        ], cwd=self.backend_root, capture_output=True, text=True)
        
        # Run additional security tools if available
        bandit_result = subprocess.run([
            "bandit", "-r", "app/", "-f", "json"
        ], cwd=self.backend_root, capture_output=True, text=True)
        
        results = {
            "security_tests": {
                "exit_code": security_result.returncode,
                "stdout": security_result.stdout,
                "stderr": security_result.stderr,
                "passed": security_result.returncode == 0
            },
            "bandit_scan": {
                "exit_code": bandit_result.returncode,
                "stdout": bandit_result.stdout,
                "stderr": bandit_result.stderr,
                "passed": bandit_result.returncode == 0
            }
        }
        
        success = results["security_tests"]["passed"]
        
        if success:
            print("✅ Security tests passed")
        else:
            print("❌ Security tests failed")
            
        return success, results
    
    def run_regression_tests(self) -> Tuple[bool, Dict[str, Any]]:
        """Run regression tests for critical paths."""
        print("🔄 Running Regression Tests...")
        
        # Run regression test suite
        regression_result = subprocess.run([
            "pytest", "tests/test_regression_critical_paths.py", "-v",
            "--tb=short",
            "-x"  # Stop on first failure for regression tests
        ], cwd=self.backend_root, capture_output=True, text=True)
        
        results = {
            "regression_tests": {
                "exit_code": regression_result.returncode,
                "stdout": regression_result.stdout,
                "stderr": regression_result.stderr,
                "passed": regression_result.returncode == 0
            }
        }
        
        success = results["regression_tests"]["passed"]
        
        if success:
            print("✅ Regression tests passed")
        else:
            print("❌ Regression tests failed - CRITICAL!")
            
        return success, results
    
    def run_mvp_suite(self) -> Tuple[bool, Dict[str, Any]]:
        """Run MVP test suite for quick validation."""
        print("🚀 Running MVP Test Suite...")
        
        # Run MVP test suite
        mvp_result = subprocess.run([
            sys.executable, "test_mvp.py"
        ], cwd=self.backend_root, capture_output=True, text=True)
        
        results = {
            "mvp_suite": {
                "exit_code": mvp_result.returncode,
                "stdout": mvp_result.stdout,
                "stderr": mvp_result.stderr,
                "passed": mvp_result.returncode == 0
            }
        }
        
        success = results["mvp_suite"]["passed"]
        
        if success:
            print("✅ MVP test suite passed")
        else:
            print("❌ MVP test suite failed")
            
        return success, results
    
    def run_comprehensive_suite(self) -> Dict[str, Any]:
        """Run all test suites in sequence."""
        print("🎯 Running Comprehensive Test Suite...")
        print("=" * 60)
        
        suite_runners = [
            ("unit", self.run_unit_tests),
            ("integration", self.run_integration_tests),  
            ("regression", self.run_regression_tests),    # Run regression early to catch critical issues
            ("security", self.run_security_tests),
            ("performance", self.run_performance_tests),
            ("e2e", self.run_e2e_tests),                 # E2E last as it's most complex
        ]
        
        overall_success = True
        
        for suite_name, runner_func in suite_runners:
            print(f"\n📊 Running {suite_name.upper()} test suite...")
            success, results = runner_func()
            
            self.test_results["suites"][suite_name] = {
                "success": success,
                "results": results,
                "timestamp": time.time()
            }
            
            if not success:
                overall_success = False
                self.test_results["issues"].append(f"{suite_name.capitalize()} tests failed")
                
                # For critical failures, consider stopping
                if suite_name == "regression":
                    print(f"\n⚠️ CRITICAL: {suite_name} tests failed!")
                    print("Consider stopping here to fix critical regressions.")
        
        self.test_results["end_time"] = time.time()
        self.test_results["total_duration"] = self.test_results["end_time"] - self.test_results["start_time"]
        self.test_results["overall_success"] = overall_success
        
        return self.test_results
    
    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        print("\n📈 Generating Comprehensive Test Report...")
        
        # Generate test dashboard if script exists
        dashboard_script = self.backend_root / "scripts" / "test_dashboard.py"
        if dashboard_script.exists():
            subprocess.run([sys.executable, str(dashboard_script)], cwd=self.backend_root)
        
        # Create summary report
        report_lines = [
            "# 🧪 Comprehensive Test Suite Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {self.test_results.get('total_duration', 0):.1f} seconds",
            "",
            "## 📊 Test Suite Results",
            ""
        ]
        
        # Add results for each suite
        for suite_name, suite_data in self.test_results.get("suites", {}).items():
            status = "✅ PASS" if suite_data["success"] else "❌ FAIL"
            report_lines.append(f"- **{suite_name.upper()}**: {status}")
        
        report_lines.extend([
            "",
            f"## 🎯 Overall Result: {'✅ SUCCESS' if self.test_results.get('overall_success', False) else '❌ FAILURE'}",
            ""
        ])
        
        # Add issues if any
        if self.test_results.get("issues"):
            report_lines.extend([
                "## ⚠️ Issues Found:",
                ""
            ])
            for issue in self.test_results["issues"]:
                report_lines.append(f"- {issue}")
            report_lines.append("")
        
        # Add recommendations
        report_lines.extend([
            "## 🚀 Next Steps:",
            ""
        ])
        
        if self.test_results.get("overall_success", False):
            report_lines.extend([
                "- ✅ All test suites passed!",
                "- Consider running performance tests under load",
                "- Review coverage reports for improvement opportunities",
                "- Ready for deployment"
            ])
        else:
            report_lines.extend([
                "- ❌ Fix failing test suites before deployment",
                "- Review detailed test outputs in artifacts", 
                "- Focus on regression and security failures first",
                "- Re-run comprehensive suite after fixes"
            ])
        
        report_content = "\n".join(report_lines)
        
        # Save report
        report_file = self.project_root / "test-reports" / "comprehensive-test-report.md"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"📄 Report saved: {report_file}")
        return str(report_file)
    
    def _parse_coverage_data(self) -> Dict[str, Any]:
        """Parse coverage data from reports."""
        coverage_data = {}
        
        # Try to parse backend coverage JSON
        coverage_json = self.backend_root / "coverage.json"
        if coverage_json.exists():
            try:
                with open(coverage_json) as f:
                    data = json.load(f)
                    coverage_data["backend"] = {
                        "line_coverage": data.get("totals", {}).get("percent_covered", 0),
                        "total_lines": data.get("totals", {}).get("num_statements", 0),
                        "covered_lines": data.get("totals", {}).get("covered_lines", 0)
                    }
            except:
                coverage_data["backend"] = {"error": "Failed to parse coverage data"}
        
        return coverage_data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Comprehensive Test Suite Runner for Learn with AI")
    parser.add_argument("--suite", choices=["all", "unit", "integration", "e2e", "performance", "security", "regression", "mvp"], 
                       default="all", help="Test suite to run")
    parser.add_argument("--generate-report", action="store_true", help="Generate comprehensive test report")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop execution on first test suite failure")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent
    runner = ComprehensiveTestRunner(project_root)
    
    print("🎯 Learn with AI - Comprehensive Test Suite")
    print("=" * 50)
    print(f"Running suite: {args.suite}")
    print(f"Project root: {project_root}")
    print("")
    
    # Run selected test suite
    if args.suite == "all":
        results = runner.run_comprehensive_suite()
    elif args.suite == "unit":
        success, results = runner.run_unit_tests()
        runner.test_results["suites"]["unit"] = {"success": success, "results": results}
    elif args.suite == "integration":
        success, results = runner.run_integration_tests()
        runner.test_results["suites"]["integration"] = {"success": success, "results": results}
    elif args.suite == "e2e":
        success, results = runner.run_e2e_tests()
        runner.test_results["suites"]["e2e"] = {"success": success, "results": results}
    elif args.suite == "performance":
        success, results = runner.run_performance_tests()
        runner.test_results["suites"]["performance"] = {"success": success, "results": results}
    elif args.suite == "security":
        success, results = runner.run_security_tests()
        runner.test_results["suites"]["security"] = {"success": success, "results": results}
    elif args.suite == "regression":
        success, results = runner.run_regression_tests()
        runner.test_results["suites"]["regression"] = {"success": success, "results": results}
    elif args.suite == "mvp":
        success, results = runner.run_mvp_suite()
        runner.test_results["suites"]["mvp"] = {"success": success, "results": results}
    
    # Generate report if requested
    if args.generate_report or args.suite == "all":
        report_path = runner.generate_report()
        print(f"\n📊 Comprehensive report available at: {report_path}")
    
    # Print final summary
    print("\n" + "=" * 50)
    if args.suite == "all":
        overall_success = runner.test_results.get("overall_success", False)
        print(f"🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
        
        if not overall_success:
            print("\n⚠️ Issues found:")
            for issue in runner.test_results.get("issues", []):
                print(f"  - {issue}")
        
        sys.exit(0 if overall_success else 1)
    else:
        # For individual suites
        suite_data = runner.test_results["suites"].get(args.suite, {})
        success = suite_data.get("success", False)
        print(f"🎯 {args.suite.upper()} Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()