# Performance Testing & Benchmarking

This directory contains comprehensive performance tests and benchmarks for the Event Management Backend.

## Overview

The performance testing framework includes:

- **Database Query Benchmarks**: ORM efficiency, N+1 detection, query optimization
- **API Endpoint Tests**: Response times, throughput, latency percentiles
- **Concurrency Tests**: Race conditions, thread-safety, atomic operations
- **Load Tests**: Realistic user behavior simulation with Locust
- **Scalability Tests**: Performance across different data volumes

## Quick Start

### Prerequisites

```bash
# Install performance testing dependencies
pip install pytest-benchmark pytest-html locust factory-boy faker

# Or install from requirements
pip install -r requirements-perf.txt  # if available
```

### Running Tests

```bash
# Quick performance tests (excludes slow tests)
./performance/run_performance_tests.sh --quick

# Full performance test suite
./performance/run_performance_tests.sh --full

# Benchmark tests only
./performance/run_performance_tests.sh --benchmark

# Concurrency tests only
./performance/run_performance_tests.sh --concurrency

# Generate HTML report
./performance/run_performance_tests.sh --full --report

# Compare with baseline
./performance/run_performance_tests.sh --full --compare
```

### Using pytest directly

```bash
# Run all performance tests
pytest performance/ -v

# Run specific test file
pytest performance/test_database_queries.py -v

# Run tests with specific marker
pytest performance/ -m "benchmark and not slow" -v

# Run with benchmark output
pytest performance/ --benchmark-only -v

# Generate benchmark JSON
pytest performance/ --benchmark-only --benchmark-json=reports/benchmark.json
```

## Test Organization

```
performance/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── test_database_queries.py    # Database query benchmarks
├── test_api_endpoints.py       # API endpoint performance tests
├── test_concurrency.py         # Concurrency and race condition tests
├── locustfile.py              # Load testing scenarios
├── fixtures/
│   ├── factories.py           # Model factories for test data
│   └── data_loaders.py        # Bulk data generation utilities
├── reports/                   # Test results and reports
├── benchmarks/                # Historical benchmark data
├── run_performance_tests.sh   # Test runner script
└── README.md                  # This file
```

## Test Categories

### 1. Database Query Benchmarks

Tests query performance and efficiency:

```bash
# Run database query tests
pytest performance/test_database_queries.py -v

# Check for N+1 queries
pytest performance/test_database_queries.py::TestEventListingQueries::test_no_n_plus_one_in_event_listing -v
```

**Key metrics:**
- Query execution time
- Number of queries per endpoint
- N+1 query detection
- Index utilization

**Targets:**
- Event listing (10K events): < 500ms
- Event detail: < 200ms
- Analytics (100K records): < 1s

### 2. API Endpoint Performance

Tests API response times and throughput:

```bash
# Run API endpoint tests
pytest performance/test_api_endpoints.py -v

# Test specific endpoint
pytest performance/test_api_endpoints.py::TestEventAPIPerformance::test_event_list_api_10000_events -v
```

**Key metrics:**
- Response time (mean, median, p95, p99)
- Requests per second
- Error rate
- Payload size

**Targets (p95):**
- GET /api/events/: < 500ms
- GET /api/events/{slug}/: < 200ms
- POST /api/tickets/order/: < 2s
- POST /api/tickets/check-in/: < 100ms

### 3. Concurrency Tests

Tests thread-safety and race conditions:

```bash
# Run concurrency tests
pytest performance/test_concurrency.py -v

# Test specific race condition
pytest performance/test_concurrency.py::TestTicketPurchaseConcurrency::test_no_overselling_with_concurrent_purchases -v
```

**Key scenarios:**
- Concurrent view count updates
- Simultaneous ticket purchases (no overselling)
- Parallel check-ins (no duplicates)
- Database deadlock prevention

**Targets:**
- 1000 concurrent users on event listing
- 100 concurrent ticket purchases (no overselling)
- 100 check-ins/minute

### 4. Load Testing (Locust)

Simulates realistic user behavior:

```bash
# Start Locust web UI
locust -f performance/locustfile.py --host=http://localhost:8000

# Run headless with specific parameters
locust -f performance/locustfile.py --host=http://localhost:8000 \
    --users=100 --spawn-rate=10 --run-time=5m --headless \
    --html=reports/load_test_report.html

# Distributed load testing (master)
locust -f performance/locustfile.py --host=http://localhost:8000 --master

# Distributed load testing (worker)
locust -f performance/locustfile.py --host=http://localhost:8000 \
    --worker --master-host=<master-ip>
```

**User types:**
- **AttendeeUser** (70%): Browse events, search, view details
- **OrganizerUser** (20%): Manage events, view analytics
- **CheckInStaff** (10%): Check in attendees

**Load patterns:**
- **StepLoadShape**: Gradual increase (10 → 500 users)
- **SpikeLoadShape**: Traffic spikes simulation

## Creating Test Data

Use factories and data loaders to generate test data:

```python
from performance.fixtures.factories import EventFactory, UserFactory
from performance.fixtures.data_loaders import DataLoader

# Create individual events
event = EventFactory(status='published', privacy='public')

# Create batch
events = EventFactory.create_batch(100, status='published')

# Create large datasets efficiently
events = DataLoader.create_events(count=10000, with_tickets=True)

# Create registrations for an event
DataLoader.create_registrations(event, count=1000)

# Create nested comment tree
DataLoader.create_nested_comments(event, depth=5, children_per_level=3)

# Clean up
DataLoader.clear_all()
```

## Performance Targets (SLOs)

### API Response Times (p95)

| Priority | Endpoint | Target | Current |
|----------|----------|--------|---------|
| P0 | GET /api/events/ | <500ms | TBD |
| P0 | GET /api/events/{slug}/ | <200ms | TBD |
| P0 | POST /api/tickets/check-in/ | <100ms | TBD |
| P1 | POST /api/tickets/order/ | <2s | TBD |
| P1 | GET /api/analytics/event/{id}/ | <1s | TBD |

### Database Query Efficiency

- ✓ Maximum 3 queries for list endpoints
- ✓ Maximum 5 queries for detail endpoints
- ✓ No N+1 queries in any endpoint
- ✓ All list queries use `select_related()` or `prefetch_related()`

### Concurrency

- ✓ Support 1000 concurrent users on event listing
- ✓ Support 100 concurrent ticket purchases (no overselling)
- ✓ Support 500 concurrent check-ins (no duplicates)

## Analyzing Results

### Benchmark Output

After running tests, view benchmark results:

```bash
# View JSON results
cat performance/reports/benchmark_*.json | python -m json.tool

# Compare with baseline
pytest performance/ --benchmark-compare=performance/benchmarks/baseline.json

# Set threshold for regression (fail if >20% slower)
pytest performance/ --benchmark-compare=baseline.json --benchmark-compare-fail=mean:20%
```

### Understanding Metrics

- **mean**: Average execution time
- **median**: Middle value (less affected by outliers)
- **stddev**: Standard deviation (consistency measure)
- **min/max**: Fastest/slowest execution
- **iqr**: Interquartile range
- **ops**: Operations per second

### Creating Baselines

After running tests, save results as baseline:

```bash
# Run tests and save results
pytest performance/ --benchmark-only --benchmark-json=reports/current.json

# If satisfied with performance, set as baseline
cp reports/current.json performance/benchmarks/baseline.json

# Future runs will compare against this baseline
pytest performance/ --benchmark-compare=performance/benchmarks/baseline.json
```

## CI/CD Integration

The performance tests are integrated into the CI/CD pipeline:

```yaml
# .github/workflows/performance-tests.yml
# Runs nightly and on performance-critical PRs
```

**Regression Detection:**
- Fails CI if p95 exceeds target by >20%
- Fails CI if query count increases by >2 queries
- Fails CI if new N+1 queries are introduced
- Fails CI if memory usage increases by >30%

## Best Practices

### Writing Performance Tests

1. **Use appropriate fixtures**:
   ```python
   @pytest.mark.django_db
   def test_my_perf(small_event_dataset):  # Use pre-made datasets
       pass
   ```

2. **Mark tests appropriately**:
   ```python
   @pytest.mark.benchmark      # For micro-benchmarks
   @pytest.mark.performance    # For API tests
   @pytest.mark.concurrency    # For race condition tests
   @pytest.mark.slow           # For tests >10s
   ```

3. **Set realistic targets**:
   ```python
   assert benchmark.stats['mean'] < 0.5  # 500ms target
   ```

4. **Test with realistic data volumes**:
   ```python
   # Small: 100 records
   # Medium: 1,000 records
   # Large: 10,000 records
   # XLarge: 100,000 records
   ```

### Optimizing Performance

When tests fail, investigate:

1. **Query count**: Use `django-debug-toolbar` or query logging
2. **Query time**: Use `EXPLAIN ANALYZE` in PostgreSQL
3. **N+1 queries**: Add `select_related()` / `prefetch_related()`
4. **Missing indexes**: Check query plans
5. **Inefficient filters**: Optimize WHERE clauses

## Troubleshooting

### Common Issues

**Tests are flaky:**
- Increase `min_rounds` in benchmark config
- Use `@pytest.mark.django_db(transaction=True)` for concurrency tests
- Ensure database is in clean state before tests

**Tests are too slow:**
- Use `--quick` flag to exclude slow tests
- Run specific test files instead of full suite
- Optimize fixture creation

**Benchmark comparison fails:**
- Check baseline file exists: `ls performance/benchmarks/`
- Verify baseline format: `cat baseline.json | python -m json.tool`
- Adjust threshold: `--benchmark-compare-fail=mean:30%`

**Database errors:**
- Ensure PostgreSQL is running for concurrency tests
- Use `--reuse-db` to speed up test runs
- Reset database if state is corrupted: `pytest --create-db`

## Additional Resources

- [RFC-001: Performance Testing & Benchmarks](../docs/RFC-001-Performance-Testing-Benchmarks.md)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [Django Performance Tips](https://docs.djangoproject.com/en/5.0/topics/performance/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

## Contributing

When adding new features:

1. Add performance tests for critical paths
2. Set appropriate performance targets
3. Run baseline comparison before merging
4. Update this README if adding new test categories

## Support

For questions or issues:
- Review the RFC document
- Check existing test examples
- Run with `-v` flag for verbose output
- Check CI/CD logs for failures
