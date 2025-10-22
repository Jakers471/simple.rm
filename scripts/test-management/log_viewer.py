#!/usr/bin/env python3
"""
Simple Risk Manager - Interactive Test Log Viewer
View and analyze test execution logs
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import re

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class LogViewer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.logs_dir = self.project_root / "logs" / "tests"

        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}{text}{Colors.ENDC}")

    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}{text}{Colors.ENDC}")

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKCYAN}{text}{Colors.ENDC}")

    def get_log_files(self) -> List[Path]:
        """Get all test log files"""
        return sorted(
            self.logs_dir.glob("test_run_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

    def format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp string"""
        try:
            dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return timestamp_str

    def parse_log_summary(self, log_content: str) -> dict:
        """Parse log file and extract summary"""
        summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'duration': '0s',
            'failures': [],
            'errors_list': []
        }

        # Parse test results line
        # Example: "===== 10 passed, 2 failed in 5.23s ====="
        results_pattern = r'(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+error'

        for match in re.finditer(results_pattern, log_content):
            if match.group(1):  # passed
                summary['passed'] = int(match.group(1))
            elif match.group(2):  # failed
                summary['failed'] = int(match.group(2))
            elif match.group(3):  # skipped
                summary['skipped'] = int(match.group(3))
            elif match.group(4):  # errors
                summary['errors'] = int(match.group(4))

        summary['total'] = summary['passed'] + summary['failed'] + summary['skipped']

        # Parse duration
        duration_pattern = r'in\s+([\d.]+)s'
        duration_match = re.search(duration_pattern, log_content)
        if duration_match:
            summary['duration'] = f"{duration_match.group(1)}s"

        # Find failed tests
        failed_pattern = r'FAILED\s+([\w/.:]+)\s+-\s+(.+)'
        summary['failures'] = re.findall(failed_pattern, log_content)

        # Find errors
        error_pattern = r'ERROR\s+([\w/.:]+)\s+-\s+(.+)'
        summary['errors_list'] = re.findall(error_pattern, log_content)

        return summary

    def display_log_list(self):
        """Display list of available logs"""
        log_files = self.get_log_files()

        if not log_files:
            self.print_error("No test logs found")
            return None

        print(f"\n{Colors.BOLD}Available Test Logs:{Colors.ENDC}\n")

        for i, log_file in enumerate(log_files[:20], 1):
            # Parse filename
            timestamp_str = log_file.stem.replace("test_run_", "")
            timestamp = self.format_timestamp(timestamp_str)

            # Get file size
            size_kb = log_file.stat().st_size / 1024

            # Try to parse summary
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                summary = self.parse_log_summary(content)

                # Color code based on results
                if summary['failed'] > 0 or summary['errors'] > 0:
                    color = Colors.FAIL
                    status = "FAILED"
                elif summary['passed'] > 0:
                    color = Colors.OKGREEN
                    status = "PASSED"
                else:
                    color = Colors.WARNING
                    status = "UNKNOWN"

                print(f"  {i:2}. {timestamp} - {color}{status}{Colors.ENDC} "
                      f"({summary['passed']} passed, {summary['failed']} failed, "
                      f"{size_kb:.1f} KB)")
            except Exception:
                print(f"  {i:2}. {timestamp} - ({size_kb:.1f} KB)")

        return log_files[:20]

    def display_log_summary(self, log_file: Path):
        """Display summary of a log file"""
        self.print_header(f"Test Log Summary - {log_file.name}")

        try:
            with open(log_file, 'r') as f:
                content = f.read()

            summary = self.parse_log_summary(content)

            # Display summary
            print(f"{Colors.BOLD}Results:{Colors.ENDC}")
            print(f"  Total Tests:  {summary['total']}")
            self.print_success(f"  Passed:       {summary['passed']}")

            if summary['failed'] > 0:
                self.print_error(f"  Failed:       {summary['failed']}")
            else:
                print(f"  Failed:       {summary['failed']}")

            if summary['skipped'] > 0:
                print(f"  Skipped:      {summary['skipped']}")

            if summary['errors'] > 0:
                self.print_error(f"  Errors:       {summary['errors']}")

            print(f"  Duration:     {summary['duration']}")

            # Show failures
            if summary['failures']:
                print(f"\n{Colors.BOLD}Failed Tests:{Colors.ENDC}")
                for test_name, reason in summary['failures']:
                    self.print_error(f"  • {test_name}")
                    print(f"    Reason: {reason}")

            # Show errors
            if summary['errors_list']:
                print(f"\n{Colors.BOLD}Errors:{Colors.ENDC}")
                for test_name, reason in summary['errors_list']:
                    self.print_error(f"  • {test_name}")
                    print(f"    Reason: {reason}")

        except Exception as e:
            self.print_error(f"Error reading log file: {e}")

    def display_full_log(self, log_file: Path):
        """Display full log file"""
        self.print_header(f"Full Test Log - {log_file.name}")

        try:
            with open(log_file, 'r') as f:
                content = f.read()

            # Color code output
            for line in content.split('\n'):
                if 'PASSED' in line:
                    self.print_success(line)
                elif 'FAILED' in line or 'ERROR' in line:
                    self.print_error(line)
                elif 'WARNING' in line:
                    print(f"{Colors.WARNING}{line}{Colors.ENDC}")
                else:
                    print(line)

        except Exception as e:
            self.print_error(f"Error reading log file: {e}")

    def filter_log(self, log_file: Path, filter_term: str):
        """Display filtered log lines"""
        self.print_header(f"Filtered Log - {log_file.name} (filter: {filter_term})")

        try:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if filter_term.lower() in line.lower():
                        # Highlight the filter term
                        highlighted = line.replace(
                            filter_term,
                            f"{Colors.BOLD}{Colors.WARNING}{filter_term}{Colors.ENDC}"
                        )
                        print(f"{line_num:4}: {highlighted}", end='')

        except Exception as e:
            self.print_error(f"Error reading log file: {e}")

    def interactive_mode(self):
        """Run interactive log viewer"""
        while True:
            log_files = self.display_log_list()

            if not log_files:
                return

            print(f"\n{Colors.BOLD}Options:{Colors.ENDC}")
            print("  [number]  - View log summary")
            print("  [number]f - View full log")
            print("  [number]s - Search/filter log")
            print("  q         - Quit")

            choice = input(f"\n{Colors.OKCYAN}Select option:{Colors.ENDC} ").strip()

            if choice.lower() == 'q':
                break

            # Parse choice
            if choice.endswith('f'):
                try:
                    idx = int(choice[:-1]) - 1
                    if 0 <= idx < len(log_files):
                        self.display_full_log(log_files[idx])
                except ValueError:
                    self.print_error("Invalid option")
            elif choice.endswith('s'):
                try:
                    idx = int(choice[:-1]) - 1
                    if 0 <= idx < len(log_files):
                        filter_term = input("Enter search term: ").strip()
                        if filter_term:
                            self.filter_log(log_files[idx], filter_term)
                except ValueError:
                    self.print_error("Invalid option")
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(log_files):
                        self.display_log_summary(log_files[idx])
                except ValueError:
                    self.print_error("Invalid option")

            input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")

def main():
    viewer = LogViewer()
    viewer.interactive_mode()

if __name__ == "__main__":
    main()
