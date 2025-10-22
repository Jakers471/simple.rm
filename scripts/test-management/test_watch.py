#!/usr/bin/env python3
"""
Simple Risk Manager - Test File Watcher
Automatically runs tests when source files change
"""

import time
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Set, Dict
import hashlib

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class TestWatcher:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.file_hashes: Dict[Path, str] = {}
        self.watch_patterns = ["*.py"]
        self.ignore_patterns = ["__pycache__", ".pytest_cache", ".git"]

    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    def print_info(self, text: str):
        """Print info message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.OKCYAN}[{timestamp}] ℹ {text}{Colors.ENDC}")

    def print_success(self, text: str):
        """Print success message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.OKGREEN}[{timestamp}] ✓ {text}{Colors.ENDC}")

    def print_warning(self, text: str):
        """Print warning message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.WARNING}[{timestamp}] ⚠ {text}{Colors.ENDC}")

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        path_str = str(path)
        return any(pattern in path_str for pattern in self.ignore_patterns)

    def get_watched_files(self) -> Set[Path]:
        """Get all files to watch"""
        watched_files = set()

        # Watch source files
        if self.src_dir.exists():
            for pattern in self.watch_patterns:
                for file_path in self.src_dir.rglob(pattern):
                    if not self.should_ignore(file_path):
                        watched_files.add(file_path)

        # Watch test files
        if self.tests_dir.exists():
            for pattern in self.watch_patterns:
                for file_path in self.tests_dir.rglob(pattern):
                    if not self.should_ignore(file_path):
                        watched_files.add(file_path)

        return watched_files

    def initialize_hashes(self):
        """Initialize file hashes"""
        watched_files = self.get_watched_files()
        self.file_hashes = {
            file_path: self.get_file_hash(file_path)
            for file_path in watched_files
        }

    def check_changes(self) -> Set[Path]:
        """Check for file changes"""
        changed_files = set()
        current_files = self.get_watched_files()

        # Check for modified files
        for file_path in current_files:
            current_hash = self.get_file_hash(file_path)
            old_hash = self.file_hashes.get(file_path, "")

            if current_hash != old_hash:
                changed_files.add(file_path)
                self.file_hashes[file_path] = current_hash

        # Check for deleted files
        deleted_files = set(self.file_hashes.keys()) - current_files
        for file_path in deleted_files:
            del self.file_hashes[file_path]
            changed_files.add(file_path)

        return changed_files

    def get_related_tests(self, changed_file: Path) -> list:
        """Get test files related to changed file"""
        related_tests = []

        # If it's a test file, run it directly
        if "test_" in changed_file.name:
            related_tests.append(str(changed_file))
            return related_tests

        # If it's a source file, find corresponding test
        if changed_file.is_relative_to(self.src_dir):
            relative_path = changed_file.relative_to(self.src_dir)
            module_name = changed_file.stem

            # Look for test files
            possible_test_paths = [
                self.tests_dir / "unit" / f"test_{module_name}.py",
                self.tests_dir / "integration" / f"test_{module_name}.py",
                self.tests_dir / f"test_{module_name}.py",
            ]

            for test_path in possible_test_paths:
                if test_path.exists():
                    related_tests.append(str(test_path))

        # If no specific tests found, run all unit tests
        if not related_tests:
            related_tests.append("tests/unit/")

        return related_tests

    def run_tests(self, test_paths: list):
        """Run tests for given paths"""
        self.print_info(f"Running tests: {', '.join(test_paths)}")

        cmd = ["pytest"] + test_paths + ["-v", "--tb=short", "-x"]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=False
            )

            if result.returncode == 0:
                self.print_success("All tests passed!")
            else:
                self.print_warning("Some tests failed")

        except Exception as e:
            self.print_warning(f"Error running tests: {e}")

    def watch(self, interval: float = 1.0):
        """Watch for file changes and run tests"""
        self.print_header("TEST WATCHER - Monitoring file changes")

        self.print_info(f"Watching {len(self.file_hashes)} files...")
        self.print_info("Press Ctrl+C to stop")

        # Run initial test suite
        self.print_info("Running initial test suite...")
        self.run_tests(["tests/unit/"])

        try:
            while True:
                time.sleep(interval)

                changed_files = self.check_changes()

                if changed_files:
                    print()  # Blank line for readability

                    for changed_file in changed_files:
                        self.print_info(f"Detected change: {changed_file.name}")

                    # Collect all related tests
                    all_tests = set()
                    for changed_file in changed_files:
                        related_tests = self.get_related_tests(changed_file)
                        all_tests.update(related_tests)

                    # Run tests
                    self.run_tests(list(all_tests))

                    print()  # Blank line after tests
                    self.print_info("Watching for changes...")

        except KeyboardInterrupt:
            print("\n")
            self.print_info("Watcher stopped")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Watch for file changes and automatically run tests"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Check interval in seconds (default: 1.0)"
    )

    args = parser.parse_args()

    watcher = TestWatcher()
    watcher.initialize_hashes()
    watcher.watch(interval=args.interval)

if __name__ == "__main__":
    main()
