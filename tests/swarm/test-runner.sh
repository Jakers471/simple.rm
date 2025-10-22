#!/bin/bash

# Swarm Strategy Test Runner
# Comprehensive test execution with reporting

echo "=================================="
echo "Swarm Strategy Test Suite Runner"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test execution functions
run_unit_tests() {
    echo -e "${YELLOW}Running Unit Tests...${NC}"
    npm run test:unit
    UNIT_EXIT=$?
    echo ""
    return $UNIT_EXIT
}

run_integration_tests() {
    echo -e "${YELLOW}Running Integration Tests...${NC}"
    npm run test:integration
    INTEGRATION_EXIT=$?
    echo ""
    return $INTEGRATION_EXIT
}

run_performance_tests() {
    echo -e "${YELLOW}Running Performance Tests...${NC}"
    npm run test:performance
    PERFORMANCE_EXIT=$?
    echo ""
    return $PERFORMANCE_EXIT
}

run_coverage_report() {
    echo -e "${YELLOW}Generating Coverage Report...${NC}"
    npm run test:coverage
    COVERAGE_EXIT=$?
    echo ""
    return $COVERAGE_EXIT
}

# Main test execution
main() {
    # Track results
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0

    # Run test suites
    run_unit_tests
    UNIT_RESULT=$?

    run_integration_tests
    INTEGRATION_RESULT=$?

    run_performance_tests
    PERFORMANCE_RESULT=$?

    run_coverage_report
    COVERAGE_RESULT=$?

    # Print summary
    echo ""
    echo "=================================="
    echo "Test Execution Summary"
    echo "=================================="

    if [ $UNIT_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Unit Tests: PASSED${NC}"
    else
        echo -e "${RED}✗ Unit Tests: FAILED${NC}"
    fi

    if [ $INTEGRATION_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Integration Tests: PASSED${NC}"
    else
        echo -e "${RED}✗ Integration Tests: FAILED${NC}"
    fi

    if [ $PERFORMANCE_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Performance Tests: PASSED${NC}"
    else
        echo -e "${RED}✗ Performance Tests: FAILED${NC}"
    fi

    if [ $COVERAGE_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Coverage Report: GENERATED${NC}"
    else
        echo -e "${RED}✗ Coverage Report: FAILED${NC}"
    fi

    echo "=================================="

    # Exit with failure if any test failed
    if [ $UNIT_RESULT -ne 0 ] || [ $INTEGRATION_RESULT -ne 0 ] || [ $PERFORMANCE_RESULT -ne 0 ]; then
        exit 1
    fi

    exit 0
}

# Execute main function
main
