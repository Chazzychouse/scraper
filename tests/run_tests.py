#!/usr/bin/env python3
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run scraper tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "crawler", "extractors", "api"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )
    parser.add_argument(
        "--file", "-f",
        help="Run tests from a specific file"
    )
    
    args = parser.parse_args()
    
    cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=scraper", "--cov-report=html", "--cov-report=term"])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.file:
        cmd.append(args.file)
    elif args.type == "all":
        cmd.append("tests/")
    elif args.type == "unit":
        cmd.extend(["tests/test_scraper.py", "tests/test_utils.py", "tests/test_extractors.py"])
    elif args.type == "integration":
        cmd.append("tests/test_integration.py")
    elif args.type == "crawler":
        cmd.append("tests/test_crawler.py")
    elif args.type == "extractors":
        cmd.append("tests/test_extractors.py")
    elif args.type == "api":
        cmd.append("tests/test_api.py")
    
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
    ])
    
    success = run_command(cmd, f"Running {args.type} tests")
    
    if success:
        print(f"\n[SUCCESS] All {args.type} tests passed!")
        if args.coverage:
            print("[INFO] Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n[FAILED] Some {args.type} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
