#!/bin/bash
# Simple Risk Manager - Quick Test Runner Scripts
# Usage: source this file or run individual commands

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function definitions for direct execution

# Run all tests
test-all() {
    print_info "Running all tests..."
    pytest tests/ -v --tb=short
}

# Run unit tests only
test-unit() {
    print_info "Running unit tests..."
    pytest tests/unit/ -v
}

# Run integration tests only
test-integration() {
    print_info "Running integration tests..."
    pytest tests/integration/ -v
}

# Run E2E tests only
test-e2e() {
    print_info "Running E2E tests..."
    pytest tests/e2e/ -v
}

# Run tests with coverage
test-cov() {
    print_info "Running tests with coverage..."
    pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v

    if [ -f "htmlcov/index.html" ]; then
        print_success "Coverage report generated at: htmlcov/index.html"

        # Try to open in browser
        if command -v xdg-open > /dev/null 2>&1; then
            xdg-open htmlcov/index.html
        elif command -v open > /dev/null 2>&1; then
            open htmlcov/index.html
        fi
    fi
}

# Run specific module tests
test-mod() {
    if [ -z "$1" ]; then
        print_error "Usage: test-mod <module_name>"
        print_info "Example: test-mod database_manager"
        return 1
    fi

    print_info "Running tests for module: $1"
    pytest "tests/unit/test_${1}.py" -v
}

# Run tests in parallel (requires pytest-xdist)
test-fast() {
    print_info "Running tests in parallel..."

    if ! python -c "import xdist" 2>/dev/null; then
        print_warning "pytest-xdist not installed. Installing..."
        pip install pytest-xdist
    fi

    pytest tests/unit/ -n auto -v
}

# Run quick smoke tests
test-smoke() {
    print_info "Running smoke tests (fast)..."
    pytest tests/unit/ -m smoke -v --tb=line
}

# Run tests and watch for changes
test-watch() {
    print_info "Starting watch mode (Ctrl+C to stop)..."

    if ! python -c "import pytest_watch" 2>/dev/null; then
        print_warning "pytest-watch not installed. Installing..."
        pip install pytest-watch
    fi

    pytest-watch tests/
}

# Clean test cache
test-clean() {
    print_info "Cleaning test cache..."

    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -type f -name "*.pyc" -delete 2>/dev/null
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage

    print_success "Test cache cleaned!"
}

# Run failed tests only
test-failed() {
    print_info "Re-running failed tests..."
    pytest --lf -v
}

# Run tests with specific marker
test-mark() {
    if [ -z "$1" ]; then
        print_error "Usage: test-mark <marker>"
        print_info "Example: test-mark smoke"
        return 1
    fi

    print_info "Running tests with marker: $1"
    pytest tests/ -m "$1" -v
}

# Show test collection
test-list() {
    print_info "Collecting tests..."
    pytest tests/ --collect-only -q
}

# Run tests with specific pattern
test-pattern() {
    if [ -z "$1" ]; then
        print_error "Usage: test-pattern <pattern>"
        print_info "Example: test-pattern 'test_validate'"
        return 1
    fi

    print_info "Running tests matching pattern: $1"
    pytest tests/ -k "$1" -v
}

# Install test dependencies
test-setup() {
    print_info "Installing test dependencies..."
    pip install -r requirements-test.txt
    print_success "Test dependencies installed!"
}

# Generate test report
test-report() {
    print_info "Generating test report..."
    pytest tests/ --html=reports/test_report.html --self-contained-html -v

    if [ -f "reports/test_report.html" ]; then
        print_success "Test report generated at: reports/test_report.html"
    fi
}

# Run tests with timeout
test-timeout() {
    TIMEOUT=${1:-300}
    print_info "Running tests with ${TIMEOUT}s timeout..."
    pytest tests/ --timeout=$TIMEOUT -v
}

# Run tests with verbose output
test-verbose() {
    print_info "Running tests with verbose output..."
    pytest tests/ -vv --tb=long
}

# Show test coverage summary
test-cov-summary() {
    if [ ! -f ".coverage" ]; then
        print_warning "No coverage data found. Run test-cov first."
        return 1
    fi

    coverage report -m
}

# Export test results to JSON
test-json() {
    print_info "Running tests and exporting to JSON..."
    pytest tests/ --json-report --json-report-file=reports/test_results.json -v

    if [ -f "reports/test_results.json" ]; then
        print_success "Test results exported to: reports/test_results.json"
    fi
}

# Main menu function
test-menu() {
    python3 "$SCRIPT_DIR/test_menu.py"
}

# Help function
test-help() {
    echo ""
    echo "Simple Risk Manager - Test Runner Commands"
    echo "=========================================="
    echo ""
    echo "Quick Commands:"
    echo "  test-all          - Run all tests"
    echo "  test-unit         - Run unit tests only"
    echo "  test-integration  - Run integration tests"
    echo "  test-e2e          - Run E2E tests"
    echo "  test-smoke        - Run quick smoke tests"
    echo "  test-fast         - Run tests in parallel"
    echo ""
    echo "Coverage:"
    echo "  test-cov          - Run tests with coverage report"
    echo "  test-cov-summary  - Show coverage summary"
    echo ""
    echo "Specific Tests:"
    echo "  test-mod <name>   - Run specific module tests"
    echo "  test-mark <mark>  - Run tests with specific marker"
    echo "  test-pattern <p>  - Run tests matching pattern"
    echo "  test-failed       - Re-run failed tests only"
    echo ""
    echo "Monitoring:"
    echo "  test-watch        - Watch mode (auto-run on changes)"
    echo "  test-list         - List all available tests"
    echo ""
    echo "Maintenance:"
    echo "  test-clean        - Clean test cache"
    echo "  test-setup        - Install test dependencies"
    echo ""
    echo "Reports:"
    echo "  test-report       - Generate HTML test report"
    echo "  test-json         - Export results to JSON"
    echo ""
    echo "Advanced:"
    echo "  test-timeout <s>  - Run with timeout (default 300s)"
    echo "  test-verbose      - Run with verbose output"
    echo ""
    echo "Interactive Menu:"
    echo "  test-menu         - Launch interactive test menu"
    echo ""
}

# If script is executed (not sourced), show help
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    test-help
    echo ""
    echo "TIP: Source this file to use commands:"
    echo "  source run_tests.sh"
    echo ""
    echo "Or run the interactive menu:"
    echo "  ./test_menu.py"
fi
