#!/bin/bash

# MCP Server Test Runner Script
# This script provides convenient commands for running tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
VERBOSE=false
COVERAGE=false
MARKERS=""
TEST_PATH="tests/server/"  # Default to server tests for now

# Function to print colored output
print_colored() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_help() {
    echo "MCP Server Test Runner"
    echo ""
    echo "Usage: ./run_tests.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help           Show this help message"
    echo "  -v, --verbose        Run tests in verbose mode"
    echo "  -c, --coverage       Run with coverage report"
    echo "  -u, --unit           Run only unit tests (server)"
    echo "  -i, --integration    Run only integration tests (server)"
    echo "  -s, --server         Run all server tests (default)"
    echo "  -a, --all            Run all tests"
    echo "  -w, --watch          Run tests in watch mode"
    echo "  -f, --file PATH      Run specific test file"
    echo "  --html-coverage      Generate HTML coverage report"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh              # Run server tests (default)"
    echo "  ./run_tests.sh -u -v        # Run server unit tests verbosely"
    echo "  ./run_tests.sh -s -c --html # Run server tests with HTML coverage"
    echo "  ./run_tests.sh -a           # Run all tests (when client/backend added)"
    echo "  ./run_tests.sh -w           # Run in watch mode"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -u|--unit)
            MARKERS="unit"
            TEST_PATH="tests/server/unit/"
            shift
            ;;
        -i|--integration)
            MARKERS="integration"
            TEST_PATH="tests/server/integration/"
            shift
            ;;
        -s|--server)
            MARKERS=""
            TEST_PATH="tests/server/"
            shift
            ;;
        -a|--all)
            MARKERS=""
            TEST_PATH="tests/"
            shift
            ;;
        -w|--watch)
            WATCH=true
            shift
            ;;
        -f|--file)
            TEST_PATH="$2"
            shift 2
            ;;
        --html-coverage)
            COVERAGE=true
            HTML_COVERAGE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="uv run pytest"

# Add test path
PYTEST_CMD="$PYTEST_CMD $TEST_PATH"

# Add markers if specified
if [ ! -z "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
fi

# Add verbose flag
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
fi

# Add coverage flags
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=term-missing"
    if [ "$HTML_COVERAGE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi
fi

# Handle watch mode
if [ "$WATCH" = true ]; then
    print_colored "$YELLOW" "🔄 Running tests in watch mode..."
    print_colored "$YELLOW" "Press Ctrl+C to stop"
    # Check if pytest-watch is installed
    if ! uv run python -c "import pytest_watch" 2>/dev/null; then
        print_colored "$YELLOW" "Installing pytest-watch..."
        uv add --dev pytest-watch
    fi
    uv run ptw -- $TEST_PATH $([[ ! -z "$MARKERS" ]] && echo "-m $MARKERS")
    exit 0
fi

# Run tests
print_colored "$GREEN" "🧪 Running MCP Server Tests..."
print_colored "$GREEN" "Command: $PYTEST_CMD"
echo ""

# Execute pytest
if $PYTEST_CMD; then
    echo ""
    print_colored "$GREEN" "✅ All tests passed!"
    
    if [ "$HTML_COVERAGE" = true ]; then
        print_colored "$GREEN" "📊 Coverage report generated at: htmlcov/index.html"
        # Optionally open the report
        if command -v open &> /dev/null; then
            read -p "Open coverage report in browser? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                open htmlcov/index.html
            fi
        fi
    fi
else
    echo ""
    print_colored "$RED" "❌ Some tests failed. Please check the output above."
    exit 1
fi