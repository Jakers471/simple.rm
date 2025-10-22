#!/usr/bin/env python3
"""
Test Results Viewer - For Agents and Developers
Displays latest test results and coverage metrics
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ResultsViewer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.results_dir = self.project_root / "test-results"
        self.coverage_json = self.results_dir / "coverage" / "coverage.json"
        self.junit_xml = self.results_dir / "reports" / "junit.xml"

    def print_header(self, text):
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

    def print_section(self, text):
        print(f"{Colors.BOLD}{Colors.OKBLUE}{text}{Colors.ENDC}")

    def show_coverage_summary(self):
        """Display coverage summary from coverage.json"""
        if not self.coverage_json.exists():
            print(f"{Colors.FAIL}❌ No coverage data found. Run tests first.{Colors.ENDC}")
            return

        with open(self.coverage_json) as f:
            data = json.load(f)

        totals = data['totals']
        percent = totals['percent_covered']

        # Color based on coverage percentage
        if percent >= 90:
            color = Colors.OKGREEN
            status = "✅ EXCELLENT"
        elif percent >= 80:
            color = Colors.WARNING
            status = "⚠️  GOOD"
        else:
            color = Colors.FAIL
            status = "❌ NEEDS WORK"

        self.print_section("📊 COVERAGE SUMMARY")
        print(f"Overall Coverage: {color}{percent:.1f}%{Colors.ENDC} {status}")
        print(f"Total Statements: {totals['num_statements']}")
        print(f"Covered: {totals['covered_lines']}")
        print(f"Missing: {totals['missing_lines']}")
        print(f"Excluded: {totals['excluded_lines']}")

        # Show files with low coverage
        print(f"\n{Colors.WARNING}Files Below 90% Coverage:{Colors.ENDC}")
        low_coverage = []
        for filepath, file_data in data['files'].items():
            file_percent = file_data['summary']['percent_covered']
            if file_percent < 90:
                low_coverage.append((filepath, file_percent))

        if low_coverage:
            low_coverage.sort(key=lambda x: x[1])
            for filepath, percent in low_coverage[:10]:  # Show top 10
                filename = Path(filepath).name
                print(f"  {filename:40s} {percent:5.1f}%")
        else:
            print(f"  {Colors.OKGREEN}None! All files ≥90% covered{Colors.ENDC}")

    def show_test_summary(self):
        """Display test summary from junit.xml"""
        if not self.junit_xml.exists():
            print(f"{Colors.FAIL}❌ No test results found. Run tests first.{Colors.ENDC}")
            return

        tree = ET.parse(self.junit_xml)
        root = tree.getroot()

        # Get test suite data
        testsuite = root.find('testsuite')
        if testsuite is None:
            testsuite = root

        total = int(testsuite.get('tests', 0))
        failures = int(testsuite.get('failures', 0))
        errors = int(testsuite.get('errors', 0))
        skipped = int(testsuite.get('skipped', 0))
        time = float(testsuite.get('time', 0))
        passed = total - failures - errors - skipped

        # Color based on results
        if failures == 0 and errors == 0:
            status_color = Colors.OKGREEN
            status = "✅ ALL PASSED"
        else:
            status_color = Colors.FAIL
            status = "❌ FAILURES DETECTED"

        self.print_section("🧪 TEST SUMMARY")
        print(f"Status: {status_color}{status}{Colors.ENDC}")
        print(f"Total Tests: {total}")
        print(f"{Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
        if failures > 0:
            print(f"{Colors.FAIL}Failed: {failures}{Colors.ENDC}")
        if errors > 0:
            print(f"{Colors.FAIL}Errors: {errors}{Colors.ENDC}")
        if skipped > 0:
            print(f"{Colors.WARNING}Skipped: {skipped}{Colors.ENDC}")
        print(f"Execution Time: {time:.2f}s")

        # Show failed tests
        if failures > 0 or errors > 0:
            print(f"\n{Colors.FAIL}Failed Tests:{Colors.ENDC}")
            for testcase in testsuite.findall('.//testcase'):
                failure = testcase.find('failure')
                error = testcase.find('error')
                if failure is not None or error is not None:
                    classname = testcase.get('classname', '')
                    name = testcase.get('name', '')
                    print(f"  ❌ {classname}.{name}")
                    if failure is not None:
                        message = failure.get('message', '')
                        print(f"     {message[:80]}")

    def show_recent_runs(self):
        """Show recent test runs from logs"""
        logs_dir = self.project_root / "logs" / "tests"
        if not logs_dir.exists():
            return

        log_files = sorted(logs_dir.glob("test_run_*.log"), reverse=True)[:5]

        if log_files:
            self.print_section("📝 RECENT TEST RUNS")
            for log_file in log_files:
                # Parse timestamp from filename
                timestamp_str = log_file.stem.replace('test_run_', '')
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = timestamp_str

                size_kb = log_file.stat().st_size / 1024
                print(f"  {time_str} - {log_file.name} ({size_kb:.1f}KB)")

    def show_quick_actions(self):
        """Show quick actions to view reports"""
        self.print_section("🚀 QUICK ACTIONS")
        print("View HTML Coverage Report:")
        print(f"  {Colors.OKCYAN}open test-results/coverage/html/index.html{Colors.ENDC}")
        print("\nView HTML Test Report:")
        print(f"  {Colors.OKCYAN}open test-results/reports/report.html{Colors.ENDC}")
        print("\nView Coverage JSON (for agents):")
        print(f"  {Colors.OKCYAN}cat test-results/coverage/coverage.json | jq{Colors.ENDC}")
        print("\nView JUnit XML (for agents):")
        print(f"  {Colors.OKCYAN}cat test-results/reports/junit.xml{Colors.ENDC}")

    def show_all(self):
        """Show complete results dashboard"""
        self.print_header("SIMPLE RISK MANAGER - TEST RESULTS DASHBOARD")
        self.show_test_summary()
        print()
        self.show_coverage_summary()
        print()
        self.show_recent_runs()
        print()
        self.show_quick_actions()
        print()

def main():
    viewer = ResultsViewer()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "coverage":
            viewer.show_coverage_summary()
        elif command == "tests":
            viewer.show_test_summary()
        elif command == "history":
            viewer.show_recent_runs()
        elif command == "actions":
            viewer.show_quick_actions()
        else:
            print(f"Unknown command: {command}")
            print("Usage: view_results.py [coverage|tests|history|actions]")
    else:
        viewer.show_all()

if __name__ == "__main__":
    main()
