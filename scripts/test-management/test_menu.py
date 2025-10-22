#!/usr/bin/env python3
"""
Simple Risk Manager - Test Management CLI
Interactive menu for running tests, viewing logs, and managing test workflows
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.tests_dir = self.project_root / "tests"
        self.logs_dir = self.project_root / "logs" / "tests"
        self.coverage_dir = self.project_root / "htmlcov"

        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

    def show_menu(self):
        """Display main test menu"""
        self.print_header("SIMPLE RISK MANAGER - TEST MANAGEMENT SYSTEM")

        print(f"{Colors.OKBLUE}TEST EXECUTION:{Colors.ENDC}")
        print("  1. Run All Tests")
        print("  2. Run Unit Tests Only")
        print("  3. Run Integration Tests Only")
        print("  4. Run E2E Tests Only")
        print("  5. Run Specific Module Tests")
        print("  6. Run Tests with Coverage Report")
        print("  7. Run Tests in Parallel (Fast)")
        print("  8. Quick Smoke Test (Fastest)")

        print(f"\n{Colors.OKBLUE}TEST ANALYSIS:{Colors.ENDC}")
        print("  9. View Test Results Dashboard (Summary)")
        print("  10. View Coverage Report (HTML)")
        print("  11. View Test Report (HTML)")
        print("  12. View Agent Data (JSON/XML)")
        print("  13. View Test Logs")

        print(f"\n{Colors.OKBLUE}MAINTENANCE:{Colors.ENDC}")
        print("  14. Clean Test Cache")
        print("  15. Install/Update Test Dependencies")
        print("  16. Watch Mode (Auto-run on changes)")

        print(f"\n{Colors.WARNING}  0. Exit{Colors.ENDC}")
        print("="*60)

    def run_pytest(self, args: list, description: str) -> bool:
        """Run pytest with given arguments"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"test_run_{timestamp}.log"

        self.print_info(f"Running: {description}")
        self.print_info(f"Log file: {log_file}")

        # Force color output in pytest
        cmd = ["pytest", "--color=yes"] + args

        try:
            # Run with both stdout and log file, preserving colors
            with open(log_file, 'w') as f:
                # Use unbuffered output to preserve colors
                env = os.environ.copy()
                env['PYTEST_CURRENT_TEST'] = ''
                env['FORCE_COLOR'] = '1'
                env['TERM'] = 'xterm-256color'

                process = subprocess.Popen(
                    cmd,
                    cwd=self.project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                    bufsize=1  # Line buffered
                )

                # Stream output to both console and file
                for line in process.stdout:
                    print(line, end='')
                    f.write(line)

                process.wait()

            if process.returncode == 0:
                self.print_success(f"{description} completed successfully!")
                return True
            else:
                self.print_error(f"{description} failed with exit code {process.returncode}")
                return False

        except Exception as e:
            self.print_error(f"Error running tests: {e}")
            return False

    def option_1_all_tests(self):
        """Run all tests"""
        self.run_pytest(
            ["tests/", "-v", "--tb=short"],
            "All Tests"
        )

    def option_2_unit_tests(self):
        """Run unit tests only"""
        self.run_pytest(
            ["tests/unit/", "-v"],
            "Unit Tests"
        )

    def option_3_integration_tests(self):
        """Run integration tests only"""
        self.run_pytest(
            ["tests/integration/", "-v"],
            "Integration Tests"
        )

    def option_4_e2e_tests(self):
        """Run E2E tests only"""
        self.run_pytest(
            ["tests/e2e/", "-v"],
            "E2E Tests"
        )

    def option_5_specific_module(self):
        """Run specific module tests"""
        print("\nAvailable test modules:")

        # List available test files
        unit_tests = list((self.tests_dir / "unit").glob("test_*.py"))
        for i, test_file in enumerate(unit_tests, 1):
            print(f"  {i}. {test_file.stem}")

        choice = input("\nEnter module number (or 0 to cancel): ")

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(unit_tests):
                test_file = unit_tests[idx]
                self.run_pytest(
                    [str(test_file), "-v"],
                    f"Module: {test_file.stem}"
                )
        except (ValueError, IndexError):
            self.print_error("Invalid selection")

    def option_6_coverage(self):
        """Run tests with coverage report"""
        self.run_pytest(
            [
                "tests/",
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term-missing",
                "-v"
            ],
            "Tests with Coverage"
        )

        if self.coverage_dir.exists():
            self.print_success(f"Coverage report generated: {self.coverage_dir / 'index.html'}")

            # Ask to open report
            open_report = input("\nOpen coverage report in browser? (y/n): ")
            if open_report.lower() == 'y':
                self.open_coverage_report()

    def option_7_parallel(self):
        """Run tests in parallel"""
        # Check if pytest-xdist is installed
        try:
            import xdist
            self.run_pytest(
                ["tests/", "-n", "auto", "-v"],
                "Parallel Test Execution"
            )
        except ImportError:
            self.print_warning("pytest-xdist not installed!")
            install = input("Install pytest-xdist? (y/n): ")
            if install.lower() == 'y':
                subprocess.run([sys.executable, "-m", "pip", "install", "pytest-xdist"])
                self.run_pytest(
                    ["tests/", "-n", "auto", "-v"],
                    "Parallel Test Execution"
                )

    def option_8_smoke_test(self):
        """Run quick smoke tests"""
        self.run_pytest(
            ["tests/unit/", "-m", "smoke", "-v", "--tb=line"],
            "Smoke Tests (Quick)"
        )

    def option_9_view_logs(self):
        """View test logs"""
        log_files = sorted(self.logs_dir.glob("test_run_*.log"), reverse=True)

        if not log_files:
            self.print_warning("No test logs found")
            return

        print("\nRecent test logs:")
        for i, log_file in enumerate(log_files[:10], 1):
            size_kb = log_file.stat().st_size / 1024
            timestamp = log_file.stem.replace("test_run_", "")
            print(f"  {i}. {timestamp} ({size_kb:.1f} KB)")

        choice = input("\nEnter log number to view (or 0 to cancel): ")

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(log_files):
                log_file = log_files[idx]

                # Use less for viewing if available, otherwise cat
                if os.system("which less > /dev/null 2>&1") == 0:
                    subprocess.run(["less", str(log_file)])
                else:
                    with open(log_file, 'r') as f:
                        print(f.read())
        except (ValueError, IndexError):
            self.print_error("Invalid selection")

    def option_10_view_coverage(self):
        """View coverage report"""
        coverage_html = self.project_root / "test-results" / "coverage" / "html" / "index.html"

        if not coverage_html.exists():
            self.print_warning("No coverage report found. Run tests first (option 1-8).")
            return

        self.print_info("Opening coverage report in browser...")

        # Try multiple methods to open
        success = False

        # Method 1: Try webbrowser module (more reliable for HTML)
        try:
            import webbrowser
            webbrowser.open(f"file://{coverage_html.absolute()}")
            self.print_success("Coverage report opened in browser")
            success = True
        except:
            pass

        # Method 2: Try cmd.exe start (better for HTML on WSL)
        if not success and os.path.exists("/mnt/c"):
            try:
                result = subprocess.run(
                    ["wslpath", "-w", str(coverage_html)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    windows_path = result.stdout.strip()
                    subprocess.run(["cmd.exe", "/c", "start", windows_path], check=False)
                    self.print_success("Coverage report opened with cmd.exe")
                    success = True
            except:
                pass

        # Method 3: Show path with instructions
        if not success:
            self.print_warning("Could not open automatically. Use one of these methods:")
            print()

            if os.path.exists("/mnt/c"):
                try:
                    result = subprocess.run(
                        ["wslpath", "-w", str(coverage_html)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        windows_path = result.stdout.strip()
                        print(f"  1. Copy to browser: file:///{windows_path.replace(chr(92), '/')}")
                        print(f"  2. Or use File Explorer: {windows_path}")
                except:
                    pass

            print(f"  3. Linux path: file://{coverage_html.absolute()}")
            print()

    def option_9_view_dashboard(self):
        """View test results dashboard"""
        dashboard_script = self.project_root / "scripts" / "test-management" / "view_results.py"
        if dashboard_script.exists():
            subprocess.run([sys.executable, str(dashboard_script)])
        else:
            self.print_error("Dashboard script not found")

    def option_11_view_test_report(self):
        """View HTML test report"""
        report_file = self.project_root / "test-results" / "reports" / "report.html"

        if not report_file.exists():
            self.print_warning("No test report found. Run tests first (option 1-8).")
            return

        self.print_info("Opening test report in browser...")

        # Try multiple methods to open
        success = False

        # Method 1: Try webbrowser module (more reliable for HTML)
        try:
            import webbrowser
            webbrowser.open(f"file://{report_file.absolute()}")
            self.print_success("Test report opened in browser")
            success = True
        except Exception as e:
            pass

        # Method 2: Try cmd.exe start (better for HTML on WSL)
        if not success and os.path.exists("/mnt/c"):
            try:
                result = subprocess.run(
                    ["wslpath", "-w", str(report_file)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    windows_path = result.stdout.strip()
                    subprocess.run(["cmd.exe", "/c", "start", windows_path], check=False)
                    self.print_success("Test report opened with cmd.exe")
                    success = True
            except:
                pass

        # Method 3: Show path with instructions
        if not success:
            self.print_warning("Could not open automatically. Use one of these methods:")
            print()

            # Show WSL path
            if os.path.exists("/mnt/c"):
                try:
                    result = subprocess.run(
                        ["wslpath", "-w", str(report_file)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        windows_path = result.stdout.strip()
                        print(f"  1. Copy to browser: file:///{windows_path.replace(chr(92), '/')}")
                        print(f"  2. Or use File Explorer: {windows_path}")
                except:
                    pass

            print(f"  3. Linux path: file://{report_file.absolute()}")
            print()

    def option_12_view_agent_data(self):
        """View what agents see (JSON/XML data)"""
        self.print_header("AGENT-READABLE TEST DATA")

        coverage_json = self.project_root / "test-results" / "coverage" / "coverage.json"
        junit_xml = self.project_root / "test-results" / "reports" / "junit.xml"

        # Check if files exist
        if not coverage_json.exists() and not junit_xml.exists():
            self.print_warning("No test data found. Run tests first (option 1-8).")
            return

        print(f"\n{Colors.BOLD}What Agents Can Read:{Colors.ENDC}\n")

        # Show coverage JSON
        if coverage_json.exists():
            import json
            with open(coverage_json) as f:
                data = json.load(f)

            print(f"{Colors.OKBLUE}📊 Coverage Data (JSON):{Colors.ENDC}")
            print(f"   File: {coverage_json}")
            print(f"   Format: JSON (machine-readable)")
            print()

            totals = data['totals']
            percent = totals['percent_covered']

            if percent >= 90:
                color = Colors.OKGREEN
            elif percent >= 80:
                color = Colors.WARNING
            else:
                color = Colors.FAIL

            print(f"   Overall Coverage: {color}{percent:.1f}%{Colors.ENDC}")
            print(f"   Total Statements: {totals['num_statements']}")
            print(f"   Covered Lines: {totals['covered_lines']}")
            print(f"   Missing Lines: {totals['missing_lines']}")
            print()

            # Show sample agent commands
            print(f"{Colors.OKCYAN}   Agent Commands:{Colors.ENDC}")
            print(f"   cat {coverage_json} | jq '.totals.percent_covered'")
            print(f"   cat {coverage_json} | jq '.files | keys'")
            print()

        # Show JUnit XML
        if junit_xml.exists():
            import xml.etree.ElementTree as ET
            tree = ET.parse(junit_xml)
            root = tree.getroot()

            testsuite = root.find('testsuite')
            if testsuite is None:
                testsuite = root

            total = int(testsuite.get('tests', 0))
            failures = int(testsuite.get('failures', 0))
            errors = int(testsuite.get('errors', 0))
            skipped = int(testsuite.get('skipped', 0))
            time = float(testsuite.get('time', 0))

            print(f"{Colors.OKBLUE}🧪 Test Results (XML):{Colors.ENDC}")
            print(f"   File: {junit_xml}")
            print(f"   Format: JUnit XML (machine-readable)")
            print()

            if failures == 0 and errors == 0:
                status_color = Colors.OKGREEN
            else:
                status_color = Colors.FAIL

            print(f"   Total Tests: {total}")
            print(f"   {Colors.OKGREEN}Passed: {total - failures - errors - skipped}{Colors.ENDC}")
            if failures > 0:
                print(f"   {Colors.FAIL}Failed: {failures}{Colors.ENDC}")
            if errors > 0:
                print(f"   {Colors.FAIL}Errors: {errors}{Colors.ENDC}")
            if skipped > 0:
                print(f"   {Colors.WARNING}Skipped: {skipped}{Colors.ENDC}")
            print(f"   Execution Time: {time:.2f}s")
            print()

            # Show sample agent commands
            print(f"{Colors.OKCYAN}   Agent Commands:{Colors.ENDC}")
            print(f"   cat {junit_xml} | grep '<testsuite'")
            print(f"   cat {junit_xml} | grep -oP 'tests=\"\\d+\"'")
            print()

        # Show file locations
        print(f"{Colors.BOLD}Files for Agent Access:{Colors.ENDC}")
        if coverage_json.exists():
            print(f"   📊 {coverage_json}")
        if junit_xml.exists():
            print(f"   🧪 {junit_xml}")
        print()

        # Offer to show raw data
        choice = input(f"\nView raw JSON/XML data? (y/n): ")
        if choice.lower() == 'y':
            print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")

            if coverage_json.exists():
                print(f"\n{Colors.OKBLUE}Coverage JSON (first 50 lines):{Colors.ENDC}\n")
                subprocess.run(["head", "-50", str(coverage_json)])

            if junit_xml.exists():
                print(f"\n{Colors.OKBLUE}JUnit XML (first 50 lines):{Colors.ENDC}\n")
                subprocess.run(["head", "-50", str(junit_xml)])

    def option_13_view_logs(self):
        """View test logs"""
        log_files = sorted(self.logs_dir.glob("test_run_*.log"), reverse=True)

        if not log_files:
            self.print_warning("No test logs found")
            return

        print("\nRecent test logs:")
        for i, log_file in enumerate(log_files[:10], 1):
            size_kb = log_file.stat().st_size / 1024
            timestamp = log_file.stem.replace("test_run_", "")
            print(f"  {i}. {timestamp} ({size_kb:.1f} KB)")

        choice = input("\nEnter log number to view (or 0 to cancel): ")

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(log_files):
                log_file = log_files[idx]

                # Use less for viewing if available, otherwise cat
                if os.system("which less > /dev/null 2>&1") == 0:
                    subprocess.run(["less", str(log_file)])
                else:
                    with open(log_file, 'r') as f:
                        print(f.read())
        except (ValueError, IndexError):
            self.print_error("Invalid selection")

    def option_14_clean_cache(self):
        """Clean test cache"""
        self.print_info("Cleaning test cache...")

        # Remove pytest cache
        cache_dirs = [
            self.project_root / ".pytest_cache",
            self.project_root / "__pycache__",
        ]

        # Find all __pycache__ directories
        for pycache in self.project_root.rglob("__pycache__"):
            cache_dirs.append(pycache)

        # Find all .pyc files
        pyc_files = list(self.project_root.rglob("*.pyc"))

        removed_count = 0

        for cache_dir in cache_dirs:
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                removed_count += 1
                self.print_success(f"Removed: {cache_dir}")

        for pyc_file in pyc_files:
            pyc_file.unlink()
            removed_count += 1

        self.print_success(f"Cleaned {removed_count} cache items")

    def option_15_install_deps(self):
        """Install/update test dependencies"""
        self.print_info("Installing test dependencies...")

        deps = [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-xdist>=3.3.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.11.0",
            "pytest-timeout>=2.1.0",
        ]

        for dep in deps:
            print(f"\nInstalling {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep])

        self.print_success("Test dependencies installed!")

    def option_16_watch_mode(self):
        """Watch mode - auto-run tests on changes"""
        self.print_info("Watch mode - tests will run automatically on file changes")
        self.print_warning("Press Ctrl+C to exit")

        try:
            # Check if pytest-watch is installed
            try:
                import pytest_watch
                subprocess.run(
                    ["pytest-watch", "tests/"],
                    cwd=self.project_root
                )
            except ImportError:
                self.print_warning("pytest-watch not installed!")
                install = input("Install pytest-watch? (y/n): ")
                if install.lower() == 'y':
                    subprocess.run([sys.executable, "-m", "pip", "install", "pytest-watch"])
                    subprocess.run(
                        ["pytest-watch", "tests/"],
                        cwd=self.project_root
                    )
        except KeyboardInterrupt:
            self.print_info("\nWatch mode stopped")

    def run(self):
        """Main menu loop"""
        while True:
            try:
                self.show_menu()
                choice = input("\nSelect option: ").strip()

                if choice == '0':
                    self.print_info("Goodbye!")
                    sys.exit(0)
                elif choice == '1':
                    self.option_1_all_tests()
                elif choice == '2':
                    self.option_2_unit_tests()
                elif choice == '3':
                    self.option_3_integration_tests()
                elif choice == '4':
                    self.option_4_e2e_tests()
                elif choice == '5':
                    self.option_5_specific_module()
                elif choice == '6':
                    self.option_6_coverage()
                elif choice == '7':
                    self.option_7_parallel()
                elif choice == '8':
                    self.option_8_smoke_test()
                elif choice == '9':
                    self.option_9_view_dashboard()
                elif choice == '10':
                    self.option_10_view_coverage()
                elif choice == '11':
                    self.option_11_view_test_report()
                elif choice == '12':
                    self.option_12_view_agent_data()
                elif choice == '13':
                    self.option_13_view_logs()
                elif choice == '14':
                    self.option_14_clean_cache()
                elif choice == '15':
                    self.option_15_install_deps()
                elif choice == '16':
                    self.option_16_watch_mode()
                else:
                    self.print_error("Invalid option. Please try again.")

                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n")
                self.print_info("Goodbye!")
                sys.exit(0)
            except Exception as e:
                self.print_error(f"Unexpected error: {e}")
                input("\nPress Enter to continue...")

def main():
    manager = TestManager()
    manager.run()

if __name__ == "__main__":
    main()
