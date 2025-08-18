#!/usr/bin/env python3
"""
Test Dashboard Generator - Creates comprehensive test metrics and reporting.

This script generates HTML dashboards with test results, coverage metrics,
performance data, and trend analysis as specified in Issue #25.
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET


class TestMetricsCollector:
    """Collects and processes test metrics from various sources."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "backend"
        self.frontend_root = project_root / "frontend"
        self.reports_dir = project_root / "test-reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def collect_backend_metrics(self) -> Dict[str, Any]:
        """Collect backend test metrics and coverage data."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "coverage": {},
            "performance": {},
            "errors": []
        }
        
        try:
            # Run MVP test suite and collect metrics
            mvp_result = subprocess.run([
                sys.executable, "test_mvp.py"
            ], cwd=self.backend_root, capture_output=True, text=True)
            
            metrics["test_results"]["mvp_suite"] = {
                "exit_code": mvp_result.returncode,
                "stdout": mvp_result.stdout,
                "stderr": mvp_result.stderr,
                "passed": mvp_result.returncode == 0
            }
            
            # Run full test suite with coverage
            full_result = subprocess.run([
                "pytest", "tests/", "-v", "--cov=app", 
                "--cov-report=xml", "--cov-report=json"
            ], cwd=self.backend_root, capture_output=True, text=True)
            
            metrics["test_results"]["full_suite"] = {
                "exit_code": full_result.returncode,
                "stdout": full_result.stdout,
                "stderr": full_result.stderr
            }
            
            # Parse coverage data
            coverage_xml = self.backend_root / "coverage.xml"
            if coverage_xml.exists():
                metrics["coverage"] = self._parse_coverage_xml(coverage_xml)
            
            coverage_json = self.backend_root / "coverage.json"
            if coverage_json.exists():
                with open(coverage_json) as f:
                    coverage_data = json.load(f)
                    metrics["coverage"]["summary"] = coverage_data.get("totals", {})
            
        except Exception as e:
            metrics["errors"].append(f"Backend metrics collection failed: {str(e)}")
        
        return metrics
    
    def collect_frontend_metrics(self) -> Dict[str, Any]:
        """Collect frontend test metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "coverage": {},
            "errors": []
        }
        
        try:
            # Run frontend tests
            test_result = subprocess.run([
                "npm", "test", "--", "--coverage", "--watchAll=false", "--passWithNoTests"
            ], cwd=self.frontend_root, capture_output=True, text=True)
            
            metrics["test_results"]["unit_tests"] = {
                "exit_code": test_result.returncode,
                "stdout": test_result.stdout,
                "stderr": test_result.stderr,
                "passed": test_result.returncode == 0
            }
            
            # Parse Jest coverage
            coverage_dir = self.frontend_root / "coverage"
            if coverage_dir.exists():
                lcov_file = coverage_dir / "lcov-report" / "index.html"
                if lcov_file.exists():
                    metrics["coverage"]["report_available"] = True
                    metrics["coverage"]["report_path"] = str(lcov_file)
            
        except Exception as e:
            metrics["errors"].append(f"Frontend metrics collection failed: {str(e)}")
        
        return metrics
    
    def collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance test metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "load_tests": {},
            "errors": []
        }
        
        try:
            # Run performance tests
            perf_result = subprocess.run([
                "pytest", "tests/test_load_performance.py", "-v", "-s"
            ], cwd=self.backend_root, capture_output=True, text=True)
            
            metrics["load_tests"] = {
                "exit_code": perf_result.returncode,
                "stdout": perf_result.stdout,
                "stderr": perf_result.stderr,
                "passed": perf_result.returncode == 0
            }
            
            # Extract performance metrics from stdout
            if "Load Test Summary" in perf_result.stdout:
                metrics["load_tests"]["metrics_available"] = True
                
        except Exception as e:
            metrics["errors"].append(f"Performance metrics collection failed: {str(e)}")
        
        return metrics
    
    def collect_e2e_metrics(self) -> Dict[str, Any]:
        """Collect E2E test metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "e2e_results": {},
            "errors": []
        }
        
        try:
            # Check if Playwright results exist
            test_results_dir = self.frontend_root / "test-results"
            playwright_report = self.frontend_root / "playwright-report"
            
            if test_results_dir.exists() or playwright_report.exists():
                metrics["e2e_results"]["reports_available"] = True
                metrics["e2e_results"]["test_results_dir"] = str(test_results_dir)
                metrics["e2e_results"]["playwright_report"] = str(playwright_report)
        
        except Exception as e:
            metrics["errors"].append(f"E2E metrics collection failed: {str(e)}")
        
        return metrics
    
    def _parse_coverage_xml(self, xml_file: Path) -> Dict[str, Any]:
        """Parse coverage XML report."""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            coverage_data = {}
            for coverage in root.findall('.//coverage'):
                coverage_data = {
                    "line_rate": float(coverage.get("line-rate", 0)) * 100,
                    "branch_rate": float(coverage.get("branch-rate", 0)) * 100,
                    "lines_covered": int(coverage.get("lines-covered", 0)),
                    "lines_valid": int(coverage.get("lines-valid", 0)),
                    "branches_covered": int(coverage.get("branches-covered", 0)),
                    "branches_valid": int(coverage.get("branches-valid", 0))
                }
                break
            
            return coverage_data
        except Exception:
            return {"error": "Failed to parse coverage XML"}


class TestDashboardGenerator:
    """Generates HTML test dashboard with metrics and visualizations."""
    
    def __init__(self, metrics_collector: TestMetricsCollector):
        self.collector = metrics_collector
        self.dashboard_file = metrics_collector.reports_dir / "test-dashboard.html"
    
    def generate_dashboard(self) -> str:
        """Generate comprehensive test dashboard."""
        # Collect all metrics
        backend_metrics = self.collector.collect_backend_metrics()
        frontend_metrics = self.collector.collect_frontend_metrics()
        performance_metrics = self.collector.collect_performance_metrics()
        e2e_metrics = self.collector.collect_e2e_metrics()
        
        # Generate HTML
        html = self._generate_html(
            backend_metrics, frontend_metrics, 
            performance_metrics, e2e_metrics
        )
        
        # Save dashboard
        with open(self.dashboard_file, 'w') as f:
            f.write(html)
        
        # Also save metrics as JSON
        metrics_json = {
            "backend": backend_metrics,
            "frontend": frontend_metrics,
            "performance": performance_metrics,
            "e2e": e2e_metrics,
            "generated_at": datetime.now().isoformat()
        }
        
        json_file = self.collector.reports_dir / "test-metrics.json"
        with open(json_file, 'w') as f:
            json.dump(metrics_json, f, indent=2)
        
        return str(self.dashboard_file)
    
    def _generate_html(self, backend: Dict, frontend: Dict, 
                      performance: Dict, e2e: Dict) -> str:
        """Generate HTML dashboard content."""
        
        # Determine overall status
        backend_status = "✅ Pass" if backend.get("test_results", {}).get("mvp_suite", {}).get("passed", False) else "❌ Fail"
        frontend_status = "✅ Pass" if frontend.get("test_results", {}).get("unit_tests", {}).get("passed", False) else "❌ Fail"
        performance_status = "✅ Pass" if performance.get("load_tests", {}).get("passed", False) else "❌ Fail"
        
        # Get coverage data
        backend_coverage = backend.get("coverage", {}).get("line_rate", 0)
        coverage_status = "✅ Good" if backend_coverage >= 90 else "⚠️ Needs Improvement" if backend_coverage >= 70 else "❌ Poor"
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learn with AI - Test Dashboard</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5; color: #333;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;
            text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metrics-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }}
        .metric-card {{ 
            background: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #667eea;
        }}
        .metric-title {{ font-size: 18px; font-weight: 600; margin-bottom: 15px; }}
        .metric-value {{ font-size: 24px; font-weight: 700; margin-bottom: 10px; }}
        .status-pass {{ color: #10b981; }}
        .status-fail {{ color: #ef4444; }}
        .status-warn {{ color: #f59e0b; }}
        .coverage-bar {{ 
            width: 100%; height: 20px; background: #e5e5e5; border-radius: 10px;
            overflow: hidden; margin: 10px 0;
        }}
        .coverage-fill {{ 
            height: 100%; background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
            transition: width 0.3s ease;
        }}
        .details-section {{ 
            background: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;
        }}
        .timestamp {{ color: #666; font-size: 14px; margin-top: 10px; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .tab-container {{ margin-top: 20px; }}
        .tab-button {{ 
            background: #e5e7eb; border: none; padding: 10px 20px;
            cursor: pointer; margin-right: 5px; border-radius: 5px 5px 0 0;
        }}
        .tab-button.active {{ background: #667eea; color: white; }}
        .tab-content {{ background: white; padding: 20px; border-radius: 0 10px 10px 10px; }}
        .hidden {{ display: none; }}
        .error {{ color: #ef4444; background: #fef2f2; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Learn with AI - Test Dashboard</h1>
            <p>Comprehensive Testing Suite Results</p>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Backend Tests</div>
                <div class="metric-value status-{'pass' if 'Pass' in backend_status else 'fail'}">{backend_status}</div>
                <div>MVP Suite: {backend.get('test_results', {}).get('mvp_suite', {}).get('exit_code', 'N/A')}</div>
                <div class="timestamp">Last run: {backend.get('timestamp', 'N/A')}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Frontend Tests</div>
                <div class="metric-value status-{'pass' if 'Pass' in frontend_status else 'fail'}">{frontend_status}</div>
                <div>Unit Tests: {frontend.get('test_results', {}).get('unit_tests', {}).get('exit_code', 'N/A')}</div>
                <div class="timestamp">Last run: {frontend.get('timestamp', 'N/A')}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Code Coverage</div>
                <div class="metric-value">{backend_coverage:.1f}%</div>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: {min(backend_coverage, 100)}%"></div>
                </div>
                <div class="status-{'pass' if backend_coverage >= 90 else 'warn' if backend_coverage >= 70 else 'fail'}">{coverage_status}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Performance Tests</div>
                <div class="metric-value status-{'pass' if 'Pass' in performance_status else 'fail'}">{performance_status}</div>
                <div>Load Tests: {performance.get('load_tests', {}).get('exit_code', 'N/A')}</div>
                <div class="timestamp">Last run: {performance.get('timestamp', 'N/A')}</div>
            </div>
        </div>
        
        <div class="tab-container">
            <button class="tab-button active" onclick="showTab('backend-details')">Backend Details</button>
            <button class="tab-button" onclick="showTab('frontend-details')">Frontend Details</button>
            <button class="tab-button" onclick="showTab('performance-details')">Performance Details</button>
            <button class="tab-button" onclick="showTab('e2e-details')">E2E Details</button>
        </div>
        
        <div id="backend-details" class="tab-content">
            <h3>Backend Test Results</h3>
            {self._format_backend_details(backend)}
        </div>
        
        <div id="frontend-details" class="tab-content hidden">
            <h3>Frontend Test Results</h3>
            {self._format_frontend_details(frontend)}
        </div>
        
        <div id="performance-details" class="tab-content hidden">
            <h3>Performance Test Results</h3>
            {self._format_performance_details(performance)}
        </div>
        
        <div id="e2e-details" class="tab-content hidden">
            <h3>End-to-End Test Results</h3>
            {self._format_e2e_details(e2e)}
        </div>
    </div>
    
    <script>
        function showTab(tabId) {{
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.add('hidden');
            }});
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabId).classList.remove('hidden');
            
            // Add active class to clicked button
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>"""
        
        return html
    
    def _format_backend_details(self, metrics: Dict) -> str:
        """Format backend test details."""
        details = []
        
        # MVP test results
        mvp_results = metrics.get("test_results", {}).get("mvp_suite", {})
        if mvp_results.get("stdout"):
            details.append(f"""
            <h4>MVP Test Suite Output</h4>
            <pre>{mvp_results['stdout'][:2000]}{'...' if len(mvp_results['stdout']) > 2000 else ''}</pre>
            """)
        
        # Coverage details
        coverage = metrics.get("coverage", {})
        if coverage:
            details.append(f"""
            <h4>Coverage Details</h4>
            <p>Line Coverage: {coverage.get('line_rate', 0):.1f}%</p>
            <p>Branch Coverage: {coverage.get('branch_rate', 0):.1f}%</p>
            <p>Lines Covered: {coverage.get('lines_covered', 0)} / {coverage.get('lines_valid', 0)}</p>
            """)
        
        # Errors
        if metrics.get("errors"):
            for error in metrics["errors"]:
                details.append(f'<div class="error">Error: {error}</div>')
        
        return '\n'.join(details) if details else "<p>No backend details available.</p>"
    
    def _format_frontend_details(self, metrics: Dict) -> str:
        """Format frontend test details."""
        details = []
        
        test_results = metrics.get("test_results", {}).get("unit_tests", {})
        if test_results.get("stdout"):
            details.append(f"""
            <h4>Frontend Test Output</h4>
            <pre>{test_results['stdout'][:2000]}{'...' if len(test_results['stdout']) > 2000 else ''}</pre>
            """)
        
        if metrics.get("errors"):
            for error in metrics["errors"]:
                details.append(f'<div class="error">Error: {error}</div>')
        
        return '\n'.join(details) if details else "<p>No frontend details available.</p>"
    
    def _format_performance_details(self, metrics: Dict) -> str:
        """Format performance test details."""
        details = []
        
        load_tests = metrics.get("load_tests", {})
        if load_tests.get("stdout"):
            details.append(f"""
            <h4>Load Test Results</h4>
            <pre>{load_tests['stdout'][:3000]}{'...' if len(load_tests['stdout']) > 3000 else ''}</pre>
            """)
        
        if metrics.get("errors"):
            for error in metrics["errors"]:
                details.append(f'<div class="error">Error: {error}</div>')
        
        return '\n'.join(details) if details else "<p>No performance test results available.</p>"
    
    def _format_e2e_details(self, metrics: Dict) -> str:
        """Format E2E test details."""
        details = []
        
        e2e_results = metrics.get("e2e_results", {})
        if e2e_results.get("reports_available"):
            details.append(f"""
            <h4>E2E Test Reports</h4>
            <p>Playwright Report: {e2e_results.get('playwright_report', 'N/A')}</p>
            <p>Test Results: {e2e_results.get('test_results_dir', 'N/A')}</p>
            """)
        
        if metrics.get("errors"):
            for error in metrics["errors"]:
                details.append(f'<div class="error">Error: {error}</div>')
        
        return '\n'.join(details) if details else "<p>No E2E test results available.</p>"


def main():
    """Main function to generate test dashboard."""
    project_root = Path(__file__).parent.parent.parent
    
    print("🧪 Generating comprehensive test dashboard...")
    
    # Initialize collector and generator
    collector = TestMetricsCollector(project_root)
    generator = TestDashboardGenerator(collector)
    
    # Generate dashboard
    dashboard_path = generator.generate_dashboard()
    
    print(f"✅ Test dashboard generated: {dashboard_path}")
    print(f"📊 Test metrics JSON saved: {collector.reports_dir / 'test-metrics.json'}")
    
    # Print summary
    metrics_file = collector.reports_dir / 'test-metrics.json'
    if metrics_file.exists():
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        print("\n📈 Test Summary:")
        print(f"  Backend MVP Tests: {'✅ Pass' if metrics['backend'].get('test_results', {}).get('mvp_suite', {}).get('passed', False) else '❌ Fail'}")
        print(f"  Frontend Tests: {'✅ Pass' if metrics['frontend'].get('test_results', {}).get('unit_tests', {}).get('passed', False) else '❌ Fail'}")
        print(f"  Performance Tests: {'✅ Pass' if metrics['performance'].get('load_tests', {}).get('passed', False) else '❌ Fail'}")
        
        coverage = metrics['backend'].get('coverage', {}).get('line_rate', 0)
        print(f"  Backend Coverage: {coverage:.1f}%")
    
    return dashboard_path


if __name__ == "__main__":
    main()