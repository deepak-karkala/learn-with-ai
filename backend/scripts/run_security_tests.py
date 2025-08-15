#!/usr/bin/env python3
"""
Security test runner script.

Usage:
    python scripts/run_security_tests.py [--coverage] [--verbose] [--specific=test_name]
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_command(cmd, description=""):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def run_security_tests(coverage=False, verbose=False, specific=None):
    """Run security tests with optional coverage and verbosity."""
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    if specific:
        # Run specific test
        test_path = f"tests/security/{specific}" if not specific.startswith("tests/") else specific
        cmd.append(test_path)
    else:
        # Run all security tests
        cmd.append("tests/security/")
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=app.services.auth_service",
            "--cov=app.services.security_service", 
            "--cov=app.middleware.auth_middleware",
            "--cov=app.config.security",
            "--cov-report=html:htmlcov/security",
            "--cov-report=term-missing"
        ])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",  # Shorter tracebacks
        "--strict-markers",  # Strict marker checking
        "-W", "ignore::DeprecationWarning"  # Ignore deprecation warnings
    ])
    
    success = run_command(cmd, "Security Tests")
    
    if coverage and success:
        print(f"\n{'='*60}")
        print("Coverage report generated in htmlcov/security/")
        print("Open htmlcov/security/index.html in your browser to view the report")
        print(f"{'='*60}")
    
    return success


def run_security_linting():
    """Run security-focused linting."""
    print(f"\n{'='*60}")
    print("Running Security Linting")
    print(f"{'='*60}")
    
    # Security-focused tools
    tools = [
        {
            "cmd": ["python", "-m", "bandit", "-r", "app/", "-f", "json"],
            "description": "Bandit security linter",
            "optional": True
        },
        {
            "cmd": ["python", "-m", "safety", "check"],
            "description": "Safety vulnerability scanner",
            "optional": True
        },
        {
            "cmd": ["python", "-m", "semgrep", "--config=auto", "app/"],
            "description": "Semgrep security scanner", 
            "optional": True
        }
    ]
    
    results = []
    for tool in tools:
        print(f"\n{'-'*40}")
        print(f"Running: {tool['description']}")
        print(f"{'-'*40}")
        
        try:
            result = subprocess.run(tool["cmd"], capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                print("✅ PASSED")
                if result.stdout:
                    print(result.stdout)
                results.append(True)
            else:
                print("❌ FAILED" if not tool["optional"] else "⚠️  ISSUES FOUND")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                results.append(tool["optional"])  # Optional tools don't fail the build
                
        except FileNotFoundError:
            print(f"⚠️  Tool not installed: {tool['cmd'][0]}")
            print(f"Install with: pip install {tool['cmd'][0]}")
            results.append(True)  # Don't fail if tool isn't installed
        except Exception as e:
            print(f"❌ Error running {tool['description']}: {e}")
            results.append(tool["optional"])
    
    return all(results)


def validate_security_config():
    """Validate security configuration."""
    print(f"\n{'='*60}")
    print("Validating Security Configuration")
    print(f"{'='*60}")
    
    try:
        # Import and validate configuration
        from app.config.security import get_security_config_manager
        
        manager = get_security_config_manager()
        config = manager.get_config()
        
        # Validate configuration
        errors = config.validate()
        
        if errors:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("✅ Security configuration is valid")
            print(f"Security level: {config.security_level.value}")
            return True
            
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False


def check_security_dependencies():
    """Check security-related dependencies."""
    print(f"\n{'='*60}")
    print("Checking Security Dependencies")
    print(f"{'='*60}")
    
    required_packages = [
        "bcrypt",
        "pyjwt", 
        "cryptography",
        "python-jose"
    ]
    
    optional_packages = [
        "bandit",
        "safety",
        "semgrep"
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (REQUIRED)")
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} (optional)")
        except ImportError:
            print(f"⚠️  {package} (optional)")
            missing_optional.append(package)
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print(f"Install with: pip install {' '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print(f"Install with: pip install {' '.join(missing_optional)}")
    
    return True


def generate_security_report():
    """Generate comprehensive security report."""
    print(f"\n{'='*60}")
    print("Generating Security Report")
    print(f"{'='*60}")
    
    report_lines = [
        "# Security Test Report",
        f"Generated: {os.popen('date').read().strip()}",
        "",
        "## Test Results",
        ""
    ]
    
    # Run tests and collect results
    results = {
        "dependencies": check_security_dependencies(),
        "config": validate_security_config(),
        "tests": run_security_tests(coverage=True, verbose=False),
        "linting": run_security_linting()
    }
    
    # Add results to report
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        report_lines.append(f"- {test_name.title()}: {status}")
    
    report_lines.extend([
        "",
        "## Summary", 
        f"Total tests: {len(results)}",
        f"Passed: {sum(results.values())}",
        f"Failed: {len(results) - sum(results.values())}",
        ""
    ])
    
    if all(results.values()):
        report_lines.append("🎉 All security tests passed!")
    else:
        report_lines.append("⚠️  Some security tests failed. Review the output above.")
    
    # Save report
    report_content = "\n".join(report_lines)
    with open("security_report.md", "w") as f:
        f.write(report_content)
    
    print(f"\n{'='*60}")
    print("Security report saved to: security_report.md")
    print(f"{'='*60}")
    
    return all(results.values())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run security tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--specific", help="Run specific test file or function")
    parser.add_argument("--lint", action="store_true", help="Run security linting only")
    parser.add_argument("--config", action="store_true", help="Validate config only")
    parser.add_argument("--deps", action="store_true", help="Check dependencies only")
    parser.add_argument("--report", action="store_true", help="Generate full security report")
    
    args = parser.parse_args()
    
    if args.lint:
        success = run_security_linting()
    elif args.config:
        success = validate_security_config()
    elif args.deps:
        success = check_security_dependencies()
    elif args.report:
        success = generate_security_report()
    else:
        # Check dependencies first
        if not check_security_dependencies():
            print("\n❌ Dependency check failed. Cannot run tests.")
            return 1
        
        # Validate configuration
        if not validate_security_config():
            print("\n❌ Configuration validation failed. Cannot run tests.")
            return 1
        
        # Run tests
        success = run_security_tests(
            coverage=args.coverage,
            verbose=args.verbose,
            specific=args.specific
        )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())