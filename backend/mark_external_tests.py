#!/usr/bin/env python3
"""
Script to mark tests with external dependencies for MVP testing.
"""

import os
import re
from pathlib import Path

# Tests that require external dependencies (Redis, ADK artifacts, etc.)
EXTERNAL_DEPENDENCY_TESTS = [
    'test_session_persistence.py',
    'test_session_persistence_simple.py', 
    'test_adk_session_integration.py',
    'test_adk_service.py',
    'test_assessment_e2e.py',
    'test_voice_api.py',
    'security/test_auth_middleware.py',
    'security/test_auth_service.py',
    'security/test_security_integration.py',
    'security/test_security_service.py'
]

def add_external_deps_marker(file_path: Path):
    """Add external_deps marker to all test classes and functions in a file."""
    content = file_path.read_text()
    
    # Skip if already has the marker
    if '@pytest.mark.external_deps' in content:
        print(f"Skipping {file_path} - already has external_deps marker")
        return
    
    # Add import if not present
    if 'import pytest' not in content:
        content = 'import pytest\n' + content
    
    # Find test classes and functions
    lines = content.split('\n')
    modified_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a test class or async test function
        if (re.match(r'^class Test.*:', line) or 
            re.match(r'^\s*async def test_.*:', line) or
            re.match(r'^\s*def test_.*:', line)):
            
            # Add marker before the class/function
            indent = len(line) - len(line.lstrip())
            marker_line = ' ' * indent + '@pytest.mark.external_deps'
            modified_lines.append(marker_line)
        
        modified_lines.append(line)
        i += 1
    
    modified_content = '\n'.join(modified_lines)
    file_path.write_text(modified_content)
    print(f"Added external_deps markers to {file_path}")

def main():
    tests_dir = Path('tests')
    
    for test_file in EXTERNAL_DEPENDENCY_TESTS:
        file_path = tests_dir / test_file
        if file_path.exists():
            add_external_deps_marker(file_path)
        else:
            print(f"Warning: {file_path} not found")

if __name__ == '__main__':
    main()