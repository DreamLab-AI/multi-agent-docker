#!/usr/bin/env python3
"""Comprehensive test runner for the PBR texture generator.

This script provides various test execution options including:
- Running specific test categories (unit, integration, etc.)
- Coverage reporting
- Performance benchmarking
- CI/CD mode with mock responses
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"\n🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"❌ Command failed with return code {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        sys.exit(result.returncode)
    
    return result


def run_tests(args):
    """Run tests based on command line arguments."""
    pytest_args = ["pytest"]
    
    # Add verbosity
    if args.verbose:
        pytest_args.append("-vv")
    else:
        pytest_args.append("-v")
    
    # Add specific test markers
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.slow:
        markers.append("slow")
    if args.ci:
        markers.append("ci")
    
    if markers:
        pytest_args.extend(["-m", " or ".join(markers)])
    
    # Add coverage options
    if args.coverage:
        pytest_args.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            f"--cov-fail-under={args.coverage_threshold}"
        ])
    
    # Add parallel execution
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # Add specific test file/directory
    if args.test_path:
        pytest_args.append(args.test_path)
    
    # Add extra pytest arguments
    if args.pytest_args:
        pytest_args.extend(args.pytest_args)
    
    # Set environment variables for CI mode
    env = os.environ.copy()
    if args.ci:
        env["CI"] = "true"
        env["OPENAI_API_KEY"] = "test-key-for-ci"
    
    # Run pytest
    result = subprocess.run(pytest_args, env=env)
    return result.returncode


def run_coverage_report():
    """Generate and display coverage report."""
    print("\n📊 Generating coverage report...")
    
    # Generate HTML report
    run_command(["coverage", "html"])
    
    # Display terminal report
    run_command(["coverage", "report"])
    
    print("\n✅ Coverage report generated in htmlcov/index.html")


def run_benchmarks(args):
    """Run performance benchmarks."""
    print("\n⏱️  Running performance benchmarks...")
    
    pytest_args = [
        "pytest",
        "-v",
        "--benchmark-only",
        "--benchmark-verbose",
        "--benchmark-autosave"
    ]
    
    if args.test_path:
        pytest_args.append(args.test_path)
    else:
        pytest_args.append("tests/")
    
    result = subprocess.run(pytest_args)
    return result.returncode


def check_dependencies():
    """Check if all required test dependencies are installed."""
    required = ["pytest", "pytest-cov", "pytest-mock", "pytest-timeout", "pytest-benchmark"]
    missing = []
    
    for package in required:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing test dependencies: {', '.join(missing)}")
        print(f"Run: pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Run tests for PBR texture generator")
    
    # Test selection arguments
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--slow", action="store_true", help="Include slow tests")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode with mocked API calls")
    
    # Coverage arguments
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--coverage-threshold", type=int, default=80, help="Coverage threshold percentage")
    
    # Performance arguments
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")
    
    # Execution arguments
    parser.add_argument("--parallel", type=int, metavar="N", help="Run tests in parallel with N workers")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Path arguments
    parser.add_argument("test_path", nargs="?", help="Specific test file or directory to run")
    
    # Extra pytest arguments
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Additional pytest arguments")
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Run appropriate command
    if args.benchmark:
        exit_code = run_benchmarks(args)
    else:
        exit_code = run_tests(args)
        
        # Generate coverage report if requested
        if args.coverage and exit_code == 0:
            run_coverage_report()
    
    # Exit with appropriate code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()