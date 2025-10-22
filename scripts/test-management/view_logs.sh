#!/bin/bash
# Test Log Viewing Utilities
# Quick commands for viewing and analyzing test logs

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOG_DIR="tests/logs"

# Function to display usage
show_usage() {
    echo -e "${BLUE}Test Log Viewing Utilities${NC}"
    echo ""
    echo "Usage: ./view_logs.sh [command]"
    echo ""
    echo "Commands:"
    echo "  tail-exec      - Live tail of test execution log"
    echo "  tail-results   - Live tail of test results log"
    echo "  results        - Show test results summary"
    echo "  errors         - Show all test errors"
    echo "  failures       - Show failed tests"
    echo "  passes         - Show passed tests"
    echo "  skipped        - Show skipped tests"
    echo "  coverage       - Show coverage statistics"
    echo "  last-run       - Show details of last test run"
    echo "  search [term]  - Search logs for specific term"
    echo "  clean          - Archive old logs and clean directory"
    echo ""
}

# Live tail of test execution log
tail_exec() {
    echo -e "${BLUE}Live Test Execution Log (Ctrl+C to exit)${NC}"
    tail -f "$LOG_DIR/test_execution.log"
}

# Live tail of test results log
tail_results() {
    echo -e "${BLUE}Live Test Results Log (Ctrl+C to exit)${NC}"
    tail -f "$LOG_DIR/test_results.log"
}

# Show test results summary
show_results() {
    if [ ! -f "$LOG_DIR/test_results.log" ]; then
        echo -e "${RED}No test results found. Run tests first.${NC}"
        return 1
    fi

    echo -e "${BLUE}=== Test Results Summary ===${NC}"
    echo ""

    # Count passed, failed, skipped
    PASSED=$(grep -c "PASSED" "$LOG_DIR/test_results.log" 2>/dev/null || echo "0")
    FAILED=$(grep -c "FAILED" "$LOG_DIR/test_results.log" 2>/dev/null || echo "0")
    SKIPPED=$(grep -c "SKIPPED" "$LOG_DIR/test_results.log" 2>/dev/null || echo "0")

    echo -e "${GREEN}Passed:  $PASSED${NC}"
    echo -e "${RED}Failed:  $FAILED${NC}"
    echo -e "${YELLOW}Skipped: $SKIPPED${NC}"
    echo ""

    # Show session info
    echo -e "${BLUE}Latest Session:${NC}"
    grep "TEST SESSION" "$LOG_DIR/test_results.log" | tail -2
}

# Show all errors
show_errors() {
    if [ ! -f "$LOG_DIR/test_errors.log" ]; then
        echo -e "${GREEN}No errors found!${NC}"
        return 0
    fi

    echo -e "${RED}=== Test Errors ===${NC}"
    cat "$LOG_DIR/test_errors.log"
}

# Show failed tests
show_failures() {
    echo -e "${RED}=== Failed Tests ===${NC}"
    echo ""

    if [ -f "$LOG_DIR/test_results.log" ]; then
        grep "FAILED" "$LOG_DIR/test_results.log" || echo -e "${GREEN}No failures!${NC}"
    else
        echo -e "${YELLOW}No test results found.${NC}"
    fi
}

# Show passed tests
show_passes() {
    echo -e "${GREEN}=== Passed Tests ===${NC}"
    echo ""

    if [ -f "$LOG_DIR/test_results.log" ]; then
        grep "PASSED" "$LOG_DIR/test_results.log" || echo -e "${YELLOW}No passes found.${NC}"
    else
        echo -e "${YELLOW}No test results found.${NC}"
    fi
}

# Show skipped tests
show_skipped() {
    echo -e "${YELLOW}=== Skipped Tests ===${NC}"
    echo ""

    if [ -f "$LOG_DIR/test_results.log" ]; then
        grep "SKIPPED" "$LOG_DIR/test_results.log" || echo -e "${GREEN}No skipped tests.${NC}"
    else
        echo -e "${YELLOW}No test results found.${NC}"
    fi
}

# Show coverage statistics
show_coverage() {
    echo -e "${BLUE}=== Coverage Statistics ===${NC}"
    echo ""

    if [ -f "$LOG_DIR/test_execution.log" ]; then
        grep "Coverage:" "$LOG_DIR/test_execution.log" | tail -1 || echo -e "${YELLOW}No coverage data found.${NC}"
    else
        echo -e "${YELLOW}No execution log found.${NC}"
    fi

    # Also check for coverage reports
    if [ -d "$LOG_DIR/coverage" ]; then
        echo ""
        echo -e "${BLUE}Coverage Reports:${NC}"
        ls -lh "$LOG_DIR/coverage/"
    fi
}

# Show last test run details
show_last_run() {
    echo -e "${BLUE}=== Last Test Run Details ===${NC}"
    echo ""

    if [ -f "$LOG_DIR/test_results.log" ]; then
        # Show from last session start to end
        sed -n '/TEST SESSION STARTED/,$p' "$LOG_DIR/test_results.log" | tail -50
    else
        echo -e "${YELLOW}No test results found.${NC}"
    fi
}

# Search logs for term
search_logs() {
    if [ -z "$1" ]; then
        echo -e "${RED}Please provide a search term.${NC}"
        echo "Usage: ./view_logs.sh search [term]"
        return 1
    fi

    echo -e "${BLUE}Searching for: '$1'${NC}"
    echo ""

    echo -e "${YELLOW}In test_execution.log:${NC}"
    grep -n "$1" "$LOG_DIR/test_execution.log" 2>/dev/null || echo "  No matches"

    echo ""
    echo -e "${YELLOW}In test_results.log:${NC}"
    grep -n "$1" "$LOG_DIR/test_results.log" 2>/dev/null || echo "  No matches"

    echo ""
    echo -e "${YELLOW}In test_errors.log:${NC}"
    grep -n "$1" "$LOG_DIR/test_errors.log" 2>/dev/null || echo "  No matches"
}

# Clean and archive old logs
clean_logs() {
    echo -e "${BLUE}Cleaning test logs...${NC}"

    # Create archive directory with timestamp
    ARCHIVE_DIR="$LOG_DIR/archive/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$ARCHIVE_DIR"

    # Move old logs to archive
    if [ -f "$LOG_DIR/test_execution.log" ]; then
        mv "$LOG_DIR/test_execution.log"* "$ARCHIVE_DIR/" 2>/dev/null
        echo -e "${GREEN}Archived execution logs${NC}"
    fi

    if [ -f "$LOG_DIR/test_results.log" ]; then
        mv "$LOG_DIR/test_results.log" "$ARCHIVE_DIR/" 2>/dev/null
        echo -e "${GREEN}Archived results log${NC}"
    fi

    if [ -f "$LOG_DIR/test_errors.log" ]; then
        mv "$LOG_DIR/test_errors.log" "$ARCHIVE_DIR/" 2>/dev/null
        echo -e "${GREEN}Archived errors log${NC}"
    fi

    echo -e "${GREEN}Logs archived to: $ARCHIVE_DIR${NC}"

    # Clean old coverage reports (keep last 5)
    if [ -d "$LOG_DIR/coverage" ]; then
        ls -t "$LOG_DIR/coverage" | tail -n +6 | xargs -I {} rm "$LOG_DIR/coverage/{}" 2>/dev/null
        echo -e "${GREEN}Cleaned old coverage reports${NC}"
    fi
}

# Main command dispatcher
case "$1" in
    tail-exec)
        tail_exec
        ;;
    tail-results)
        tail_results
        ;;
    results)
        show_results
        ;;
    errors)
        show_errors
        ;;
    failures)
        show_failures
        ;;
    passes)
        show_passes
        ;;
    skipped)
        show_skipped
        ;;
    coverage)
        show_coverage
        ;;
    last-run)
        show_last_run
        ;;
    search)
        search_logs "$2"
        ;;
    clean)
        clean_logs
        ;;
    *)
        show_usage
        ;;
esac
