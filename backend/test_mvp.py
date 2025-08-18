#!/usr/bin/env python3
"""
MVP Test Suite - Core functionality tests without external dependencies.

This script runs only the tests that don't require Redis, ADK artifacts,
or other external services, making it perfect for MVP demos.
"""

import subprocess
import sys
from pathlib import Path


def run_mvp_tests():
    """Run MVP tests without external dependencies."""
    
    # Core tests that should pass without external dependencies
    core_test_files = [
        'tests/test_config.py',
        'tests/test_diagrams.py', 
        'tests/test_monitoring_basic.py',
        'tests/test_monitoring_integration.py',
        'tests/test_performance.py',
        'tests/test_progress_service.py',
        'tests/test_whiteboard.py',
        'tests/test_adk_voice_stream.py',
        'tests/test_api_adk.py',
        'tests/test_assessment.py',
    ]
    
    # Security config tests (some might fail but most should pass)
    security_config_tests = [
        'tests/security/test_security_config.py',
    ]
    
    all_test_files = core_test_files + security_config_tests
    
    print("🚀 Running MVP Test Suite")
    print("=" * 50)
    print(f"Testing {len(all_test_files)} core test files...")
    print()
    
    # Run pytest with the selected test files
    cmd = [
        sys.executable, '-m', 'pytest',
        *all_test_files,
        '-v',
        '--tb=short',
        '--disable-warnings',
        '--cov=app',
        '--cov-report=term-missing',
        '--cov-report=html:htmlcov_mvp'
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Extract summary information
        if "failed" in result.stdout and "passed" in result.stdout:
            # Parse test results
            lines = result.stdout.split('\n')
            summary_line = [line for line in lines if 'failed' in line and 'passed' in line]
            if summary_line:
                print("\n" + "=" * 50)
                print("📊 MVP TEST RESULTS SUMMARY")
                print("=" * 50)
                print(summary_line[0])
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def main():
    """Main entry point."""
    print("MVP Backend Test Suite")
    print("This runs core functionality tests without external dependencies")
    print("(Redis, ADK artifacts, session persistence, security services)\n")
    
    success = run_mvp_tests()
    
    if success:
        print("\n✅ MVP test suite completed successfully!")
        print("🎉 Core functionality is working correctly for the demo.")
        return 0
    else:
        print("\n⚠️  MVP test suite completed with some issues.")
        print("📝 Most core functionality should still work for the demo.")
        print("🔍 Check failing tests - they may be non-critical for MVP.")
        return 1


if __name__ == "__main__":
    sys.exit(main())