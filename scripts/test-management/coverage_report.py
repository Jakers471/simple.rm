#!/usr/bin/env python3
"""
Simple Risk Manager - Coverage Report Dashboard
Interactive coverage analysis and visualization
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
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

class CoverageReporter:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.coverage_file = self.project_root / ".coverage"
        self.coverage_dir = self.project_root / "htmlcov"
        self.coverage_xml = self.project_root / "coverage.xml"

    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

    def print_bar(self, label: str, percentage: float, width: int = 40):
        """Print a colored progress bar"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)

        # Color code based on percentage
        if percentage >= 80:
            color = Colors.OKGREEN
        elif percentage >= 60:
            color = Colors.WARNING
        else:
            color = Colors.FAIL

        print(f"{label:30} {color}{bar}{Colors.ENDC} {percentage:5.1f}%")

    def check_coverage_exists(self) -> bool:
        """Check if coverage data exists"""
        return self.coverage_file.exists() or self.coverage_xml.exists()

    def parse_coverage_json(self) -> Dict:
        """Parse coverage data from JSON"""
        try:
            # Try to generate JSON report
            import subprocess
            result = subprocess.run(
                ["coverage", "json", "-o", "coverage.json"],
                cwd=self.project_root,
                capture_output=True
            )

            if result.returncode == 0:
                with open(self.project_root / "coverage.json", 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error parsing coverage JSON: {e}")

        return {}

    def display_overall_summary(self):
        """Display overall coverage summary"""
        self.print_header("COVERAGE SUMMARY")

        if not self.check_coverage_exists():
            print(f"{Colors.WARNING}No coverage data found!{Colors.ENDC}")
            print("Run tests with coverage first: pytest --cov=src")
            return

        # Get coverage data
        import subprocess
        result = subprocess.run(
            ["coverage", "report"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"{Colors.FAIL}Error loading coverage report{Colors.ENDC}")

    def display_module_coverage(self):
        """Display coverage by module"""
        self.print_header("COVERAGE BY MODULE")

        if not self.check_coverage_exists():
            print(f"{Colors.WARNING}No coverage data found!{Colors.ENDC}")
            return

        coverage_data = self.parse_coverage_json()

        if not coverage_data or 'files' not in coverage_data:
            print(f"{Colors.WARNING}Could not parse coverage data{Colors.ENDC}")
            return

        # Group by module
        modules = {}
        for file_path, data in coverage_data['files'].items():
            if '/src/' in file_path:
                # Extract module name
                parts = file_path.split('/src/')[-1].split('/')
                module = parts[0] if len(parts) > 1 else 'root'

                if module not in modules:
                    modules[module] = {
                        'covered': 0,
                        'total': 0,
                        'files': []
                    }

                summary = data['summary']
                modules[module]['covered'] += summary['covered_lines']
                modules[module]['total'] += summary['num_statements']
                modules[module]['files'].append(Path(file_path).name)

        # Display module coverage
        for module, data in sorted(modules.items()):
            if data['total'] > 0:
                percentage = (data['covered'] / data['total']) * 100
                self.print_bar(module, percentage)
                print(f"  Files: {', '.join(data['files'][:3])}")
                if len(data['files']) > 3:
                    print(f"  ... and {len(data['files']) - 3} more")
                print()

    def display_uncovered_lines(self):
        """Display files with uncovered lines"""
        self.print_header("FILES WITH LOW COVERAGE")

        if not self.check_coverage_exists():
            print(f"{Colors.WARNING}No coverage data found!{Colors.ENDC}")
            return

        coverage_data = self.parse_coverage_json()

        if not coverage_data or 'files' not in coverage_data:
            print(f"{Colors.WARNING}Could not parse coverage data{Colors.ENDC}")
            return

        # Find files with low coverage
        low_coverage_files = []

        for file_path, data in coverage_data['files'].items():
            if '/src/' in file_path:
                summary = data['summary']
                total = summary['num_statements']

                if total > 0:
                    covered = summary['covered_lines']
                    percentage = (covered / total) * 100

                    if percentage < 80:
                        low_coverage_files.append({
                            'file': Path(file_path).name,
                            'path': file_path,
                            'percentage': percentage,
                            'missing': summary.get('missing_lines', 0)
                        })

        # Sort by percentage
        low_coverage_files.sort(key=lambda x: x['percentage'])

        if not low_coverage_files:
            print(f"{Colors.OKGREEN}All files have good coverage (>80%)!{Colors.ENDC}")
            return

        for file_info in low_coverage_files[:10]:
            self.print_bar(file_info['file'], file_info['percentage'])
            print(f"  Missing lines: {file_info['missing']}")
            print()

    def display_coverage_trends(self):
        """Display coverage trends (if historical data available)"""
        self.print_header("COVERAGE TRENDS")

        # This would require storing historical coverage data
        print(f"{Colors.WARNING}Historical coverage tracking not yet implemented{Colors.ENDC}")
        print("Future feature: Track coverage over time")

    def display_missing_coverage(self, file_path: str):
        """Display specific missing lines for a file"""
        self.print_header(f"MISSING COVERAGE - {Path(file_path).name}")

        # Run coverage report for specific file
        import subprocess
        result = subprocess.run(
            ["coverage", "report", "-m", file_path],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"{Colors.FAIL}Error loading coverage for file{Colors.ENDC}")

    def generate_html_report(self):
        """Generate HTML coverage report"""
        self.print_header("GENERATING HTML REPORT")

        if not self.check_coverage_exists():
            print(f"{Colors.WARNING}No coverage data found!{Colors.ENDC}")
            print("Run tests with coverage first: pytest --cov=src")
            return

        import subprocess
        result = subprocess.run(
            ["coverage", "html"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"{Colors.OKGREEN}HTML report generated!{Colors.ENDC}")
            print(f"Location: {self.coverage_dir / 'index.html'}")

            # Try to open in browser
            open_report = input("\nOpen in browser? (y/n): ")
            if open_report.lower() == 'y':
                try:
                    import webbrowser
                    webbrowser.open(f"file://{self.coverage_dir / 'index.html'}")
                except Exception as e:
                    print(f"Could not open browser: {e}")
        else:
            print(f"{Colors.FAIL}Error generating HTML report{Colors.ENDC}")
            print(result.stderr)

    def interactive_menu(self):
        """Run interactive coverage dashboard"""
        while True:
            self.print_header("COVERAGE DASHBOARD")

            print(f"{Colors.OKBLUE}Reports:{Colors.ENDC}")
            print("  1. Overall Summary")
            print("  2. Coverage by Module")
            print("  3. Files with Low Coverage")
            print("  4. Generate HTML Report")
            print("  5. Coverage Trends (Coming Soon)")
            print()
            print(f"{Colors.WARNING}  0. Exit{Colors.ENDC}")
            print("="*70)

            choice = input(f"\n{Colors.OKCYAN}Select option:{Colors.ENDC} ").strip()

            if choice == '0':
                break
            elif choice == '1':
                self.display_overall_summary()
            elif choice == '2':
                self.display_module_coverage()
            elif choice == '3':
                self.display_uncovered_lines()
            elif choice == '4':
                self.generate_html_report()
            elif choice == '5':
                self.display_coverage_trends()
            else:
                print(f"{Colors.FAIL}Invalid option{Colors.ENDC}")

            if choice != '0':
                input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")

def main():
    reporter = CoverageReporter()

    # Check if coverage tools are installed
    try:
        import coverage
    except ImportError:
        print(f"{Colors.WARNING}Coverage package not installed!{Colors.ENDC}")
        install = input("Install coverage? (y/n): ")
        if install.lower() == 'y':
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "coverage"])

    reporter.interactive_menu()

if __name__ == "__main__":
    main()
