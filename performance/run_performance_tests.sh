#!/bin/bash
# Performance Test Runner Script
#
# This script runs performance tests and generates reports.
#
# Usage:
#   ./performance/run_performance_tests.sh [options]
#
# Options:
#   --quick       Run quick performance tests (excludes slow tests)
#   --full        Run all performance tests including slow ones
#   --benchmark   Run only benchmark tests
#   --concurrency Run only concurrency tests
#   --report      Generate HTML report
#   --compare     Compare with baseline (requires baseline.json)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="quick"
GENERATE_REPORT=false
COMPARE_BASELINE=false
OUTPUT_DIR="performance/reports"
BENCHMARK_FILE="$OUTPUT_DIR/benchmark_$(date +%Y%m%d_%H%M%S).json"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            TEST_TYPE="quick"
            shift
            ;;
        --full)
            TEST_TYPE="full"
            shift
            ;;
        --benchmark)
            TEST_TYPE="benchmark"
            shift
            ;;
        --concurrency)
            TEST_TYPE="concurrency"
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --compare)
            COMPARE_BASELINE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--quick|--full|--benchmark|--concurrency] [--report] [--compare]"
            exit 1
            ;;
    esac
done

# Create reports directory
mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Performance Test Suite              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
python -c "import pytest_benchmark" 2>/dev/null || {
    echo -e "${RED}Error: pytest-benchmark not installed${NC}"
    echo "Install with: pip install pytest-benchmark"
    exit 1
}

echo -e "${GREEN}✓ All dependencies satisfied${NC}"
echo ""

# Run tests based on type
case $TEST_TYPE in
    quick)
        echo -e "${BLUE}Running quick performance tests (excluding slow)...${NC}"
        pytest performance/ \
            -m "performance and not slow" \
            -v \
            --benchmark-only \
            --benchmark-json="$BENCHMARK_FILE"
        ;;
    full)
        echo -e "${BLUE}Running full performance test suite...${NC}"
        pytest performance/ \
            -v \
            --benchmark-only \
            --benchmark-json="$BENCHMARK_FILE"
        ;;
    benchmark)
        echo -e "${BLUE}Running benchmark tests only...${NC}"
        pytest performance/ \
            -m "benchmark" \
            -v \
            --benchmark-only \
            --benchmark-json="$BENCHMARK_FILE"
        ;;
    concurrency)
        echo -e "${BLUE}Running concurrency tests only...${NC}"
        pytest performance/test_concurrency.py \
            -v \
            --benchmark-json="$BENCHMARK_FILE"
        ;;
esac

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All performance tests passed!${NC}"
    echo -e "${GREEN}Benchmark results saved to: $BENCHMARK_FILE${NC}"
else
    echo ""
    echo -e "${RED}✗ Some performance tests failed${NC}"
    exit 1
fi

# Generate HTML report if requested
if [ "$GENERATE_REPORT" = true ]; then
    echo ""
    echo -e "${BLUE}Generating HTML report...${NC}"

    HTML_REPORT="$OUTPUT_DIR/performance_report_$(date +%Y%m%d_%H%M%S).html"

    # Run pytest with HTML plugin if available
    if python -c "import pytest_html" 2>/dev/null; then
        pytest performance/ \
            --benchmark-only \
            --html="$HTML_REPORT" \
            --self-contained-html
        echo -e "${GREEN}✓ HTML report generated: $HTML_REPORT${NC}"
    else
        echo -e "${YELLOW}Warning: pytest-html not installed. Skipping HTML report.${NC}"
        echo "Install with: pip install pytest-html"
    fi
fi

# Compare with baseline if requested
if [ "$COMPARE_BASELINE" = true ]; then
    echo ""
    echo -e "${BLUE}Comparing with baseline...${NC}"

    BASELINE_FILE="performance/benchmarks/baseline.json"

    if [ -f "$BASELINE_FILE" ]; then
        pytest performance/ \
            --benchmark-only \
            --benchmark-compare="$BASELINE_FILE" \
            --benchmark-compare-fail=mean:20%

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Performance within acceptable range${NC}"
        else
            echo -e "${RED}✗ Performance regression detected (>20% slower)${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Warning: Baseline file not found at $BASELINE_FILE${NC}"
        echo "Create baseline with: cp $BENCHMARK_FILE $BASELINE_FILE"
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Performance Tests Complete!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Next steps:"
echo "  - Review benchmark results: cat $BENCHMARK_FILE"
echo "  - Create baseline: cp $BENCHMARK_FILE performance/benchmarks/baseline.json"
echo "  - Run load tests: locust -f performance/locustfile.py --host=http://localhost:8000"
echo ""
