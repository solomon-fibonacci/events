# RFC-001: Performance Testing and Benchmarking Framework

**Status:** Draft
**Author:** Claude
**Created:** 2025-11-07
**Updated:** 2025-11-07

## Abstract

This RFC proposes a comprehensive performance testing and benchmarking framework for the Django Event Management Backend. The framework will measure database query performance, API endpoint response times, concurrency handling, and system scalability under load.

## 1. Motivation

### 1.1 Current State

The application currently has:
- Extensive E2E test coverage (users, events, tickets, menus, reviews)
- CI/CD pipeline with unit and integration tests
- No systematic performance testing or benchmarking

### 1.2 Problem Statement

Without performance tests, we cannot:
1. **Detect Performance Regressions**: Code changes may introduce slow queries or bottlenecks
2. **Validate Scalability**: Unknown behavior under high load (1000+ concurrent users)
3. **Identify N+1 Query Problems**: ORM queries may be inefficient at scale
4. **Optimize Hot Paths**: No data on which endpoints need optimization
5. **Plan Capacity**: No baseline metrics for infrastructure planning

### 1.3 Goals

1. Establish performance baselines for all critical API endpoints
2. Detect N+1 query problems and inefficient database access patterns
3. Test concurrent access and race condition handling
4. Measure system performance under realistic load scenarios
5. Provide actionable metrics for optimization decisions
6. Integrate performance tests into CI/CD pipeline

## 2. Design Overview

### 2.1 Testing Layers

```
┌─────────────────────────────────────────────────┐
│         Performance Testing Framework           │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Database Query Benchmarks                   │
│     - ORM query efficiency                      │
│     - N+1 query detection                       │
│     - Aggregation performance                   │
│                                                  │
│  2. API Endpoint Load Tests                     │
│     - Response time measurement                 │
│     - Throughput testing                        │
│     - Latency percentiles (p50, p95, p99)       │
│                                                  │
│  3. Concurrency Tests                           │
│     - Race condition detection                  │
│     - Atomic operation validation               │
│     - Deadlock detection                        │
│                                                  │
│  4. Scalability Tests                           │
│     - Linear scaling validation                 │
│     - Breaking point identification             │
│     - Resource utilization monitoring           │
│                                                  │
│  5. Integration Performance Tests               │
│     - End-to-end workflow timing                │
│     - External service latency simulation       │
│     - File I/O performance                      │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

- **pytest-benchmark**: Micro-benchmarking with statistical analysis
- **locust**: Load testing and concurrent user simulation
- **django-silk** (optional): Real-time profiling and query analysis
- **pytest-django**: Django test fixtures and database management
- **threading/asyncio**: Concurrency testing
- **psycopg2**: Direct PostgreSQL performance testing

### 2.3 Project Structure

```
/home/user/events/
├── performance/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures and configuration
│   ├── test_database_queries.py       # Query performance benchmarks
│   ├── test_api_endpoints.py          # API response time tests
│   ├── test_concurrency.py            # Race conditions and atomicity
│   ├── test_scalability.py            # Load and stress tests
│   ├── locustfile.py                  # Locust load testing scenarios
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── factories.py               # Model factories with Faker
│   │   └── data_loaders.py            # Large dataset generation
│   ├── reports/                       # Performance test results
│   │   └── .gitkeep
│   └── benchmarks/                    # Historical benchmark data
│       └── .gitkeep
├── pytest.ini                         # Updated with performance markers
└── .github/workflows/
    └── performance-tests.yml          # CI/CD for performance tests
```

## 3. Detailed Design

### 3.1 Database Query Benchmarks

**Objective**: Measure and optimize ORM query performance

#### 3.1.1 Test Scenarios

| Test Case | Dataset Size | Metric | Target |
|-----------|--------------|--------|--------|
| Event listing (no filter) | 1K, 10K, 100K events | Query time, count | <500ms @ 10K |
| Event listing (with filters) | 10K events | Query time | <500ms |
| Event detail with related data | 1 event, 100 registrations | Query count | ≤3 queries |
| Ticket availability check | 1 event, 20 ticket types | Query count | ≤2 queries |
| Analytics aggregation | 100K registrations | Query time | <1s |
| Comment tree retrieval | 1000 nested comments | Query time | <300ms |

#### 3.1.2 Implementation Pattern

```python
@pytest.mark.benchmark
def test_event_listing_performance(benchmark, large_event_dataset):
    """Benchmark event listing with 10K events"""
    def query_events():
        return list(Event.objects.filter(
            status='published',
            privacy='public'
        ).select_related('organizer', 'category')[:20])

    result = benchmark(query_events)
    assert len(result) == 20
    assert benchmark.stats['mean'] < 0.5  # 500ms target
```

#### 3.1.3 N+1 Query Detection

Use `django-debug-toolbar` or custom assertion:

```python
def test_no_n_plus_one_in_event_listing():
    """Ensure event listing doesn't trigger N+1 queries"""
    EventFactory.create_batch(100)

    with assertNumQueries(3):  # Maximum 3 queries allowed
        events = Event.objects.filter(status='published')
        events = events.select_related('organizer', 'category')
        list(events[:20])
```

### 3.2 API Endpoint Load Tests

**Objective**: Measure API response times and throughput under load

#### 3.2.1 Critical Endpoints

| Endpoint | Method | Test Scenario | Target Response Time |
|----------|--------|---------------|---------------------|
| `/api/events/` | GET | List 10K events | p95 < 500ms |
| `/api/events/{slug}/` | GET | Detail view | p95 < 200ms |
| `/api/events/` | POST | Create event | p95 < 300ms |
| `/api/tickets/order/` | POST | Purchase tickets | p95 < 2s |
| `/api/tickets/check-in/` | POST | Check-in ticket | p95 < 100ms |
| `/api/analytics/event/{id}/` | GET | Event analytics | p95 < 1s |
| `/api/users/register/` | POST | User registration | p95 < 500ms |

#### 3.2.2 Implementation Pattern

```python
@pytest.mark.performance
@pytest.mark.parametrize("num_events", [100, 1000, 10000])
def test_event_list_api_performance(api_client, num_events, benchmark):
    """Test event listing API response time at different scales"""
    EventFactory.create_batch(num_events, status='published')

    def call_api():
        response = api_client.get('/api/events/')
        assert response.status_code == 200
        return response

    result = benchmark(call_api)

    # Assert performance targets
    if num_events == 10000:
        assert benchmark.stats['mean'] < 0.5
```

#### 3.2.3 Load Testing with Locust

```python
from locust import HttpUser, task, between

class EventManagementUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before running tasks"""
        response = self.client.post("/api/users/login/", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        self.token = response.json()['access']
        self.client.headers['Authorization'] = f'Bearer {self.token}'

    @task(3)
    def list_events(self):
        """Most common operation (60% of traffic)"""
        self.client.get("/api/events/")

    @task(2)
    def view_event_detail(self):
        """Second most common (40% of traffic)"""
        self.client.get(f"/api/events/{self.event_slug}/")

    @task(1)
    def purchase_ticket(self):
        """Purchase flow (20% of traffic)"""
        self.client.post("/api/tickets/order/", json={
            "event_id": self.event_id,
            "tickets": [{"ticket_type_id": 1, "quantity": 2}]
        })
```

### 3.3 Concurrency Tests

**Objective**: Validate thread-safety and atomic operations

#### 3.3.1 Critical Race Conditions

| Test Case | Risk | Expected Behavior |
|-----------|------|-------------------|
| Concurrent view count updates | Lost updates | All increments counted |
| Simultaneous ticket purchases | Overselling | Never exceed capacity |
| Concurrent check-ins | Duplicate check-ins | One check-in per ticket |
| Parallel order creation | Data corruption | All orders valid |

#### 3.3.2 Implementation Pattern

```python
import threading
from django.db import transaction

@pytest.mark.concurrency
def test_concurrent_ticket_purchase_no_overselling():
    """Ensure tickets are not oversold under concurrent purchases"""
    event = EventFactory()
    ticket_type = TicketTypeFactory(
        event=event,
        quantity=100,
        quantity_sold=0
    )

    results = []
    errors = []

    def purchase_ticket():
        try:
            with transaction.atomic():
                # Simulate ticket purchase
                ticket = TicketType.objects.select_for_update().get(id=ticket_type.id)
                if ticket.quantity_remaining > 0:
                    ticket.quantity_sold += 1
                    ticket.save()
                    results.append('success')
                else:
                    results.append('sold_out')
        except Exception as e:
            errors.append(str(e))

    # Launch 200 concurrent purchase attempts for 100 tickets
    threads = [threading.Thread(target=purchase_ticket) for _ in range(200)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify results
    ticket_type.refresh_from_db()
    assert ticket_type.quantity_sold == 100  # Exactly 100 sold
    assert results.count('success') == 100
    assert results.count('sold_out') == 100
    assert len(errors) == 0
```

### 3.4 Scalability Tests

**Objective**: Identify system breaking points and bottlenecks

#### 3.4.1 Scaling Dimensions

1. **Data Volume**: 100 → 1K → 10K → 100K → 1M records
2. **Concurrent Users**: 10 → 50 → 100 → 500 → 1000 users
3. **Query Complexity**: Simple → Medium → Complex filters
4. **Payload Size**: Small → Medium → Large requests

#### 3.4.2 Implementation Pattern

```python
@pytest.mark.scalability
@pytest.mark.parametrize("dataset_size,expected_max_time", [
    (100, 0.05),      # 50ms for 100 events
    (1000, 0.1),      # 100ms for 1K events
    (10000, 0.5),     # 500ms for 10K events
    (100000, 2.0),    # 2s for 100K events
])
def test_event_listing_scales_linearly(dataset_size, expected_max_time):
    """Verify event listing scales linearly with dataset size"""
    EventFactory.create_batch(dataset_size, status='published')

    start = time.time()
    events = Event.objects.filter(status='published')[:20]
    list(events)
    elapsed = time.time() - start

    assert elapsed < expected_max_time, \
        f"Query took {elapsed}s, expected <{expected_max_time}s"
```

### 3.5 Metrics and Reporting

#### 3.5.1 Key Metrics

- **Response Time**: Mean, Median, p95, p99, Max
- **Throughput**: Requests per second (RPS)
- **Database**: Query count, query time, connection pool usage
- **Resources**: CPU %, Memory MB, Disk I/O
- **Errors**: Error rate, timeout rate

#### 3.5.2 Report Format

```json
{
  "test_suite": "api_endpoint_performance",
  "timestamp": "2025-11-07T10:30:00Z",
  "environment": {
    "python_version": "3.11",
    "django_version": "5.0",
    "database": "PostgreSQL 15",
    "dataset_size": 10000
  },
  "results": [
    {
      "test_name": "test_event_list_api_performance",
      "endpoint": "GET /api/events/",
      "iterations": 100,
      "mean_response_time_ms": 234.5,
      "median_response_time_ms": 220.0,
      "p95_response_time_ms": 450.0,
      "p99_response_time_ms": 520.0,
      "max_response_time_ms": 600.0,
      "min_response_time_ms": 180.0,
      "std_dev_ms": 45.2,
      "queries_per_request": 3,
      "passed": true,
      "target_p95_ms": 500,
      "target_met": true
    }
  ]
}
```

#### 3.5.3 Visualization

Generate HTML reports with:
- Time series graphs (response time over iterations)
- Histogram of response time distribution
- Comparison charts (before/after optimization)
- Query profile breakdown

## 4. Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Set up performance testing directory structure
- [ ] Install and configure pytest-benchmark
- [ ] Create model factories for large dataset generation
- [ ] Write database query benchmarks for top 10 queries

### Phase 2: API Load Tests (Week 2)
- [ ] Implement API endpoint performance tests
- [ ] Set up Locust for load testing
- [ ] Create realistic user behavior scenarios
- [ ] Establish baseline metrics for all endpoints

### Phase 3: Concurrency & Race Conditions (Week 3)
- [ ] Write concurrency tests for ticket purchasing
- [ ] Test view count increment race conditions
- [ ] Validate check-in system thread-safety
- [ ] Add database lock testing

### Phase 4: Scalability & Integration (Week 4)
- [ ] Implement scalability tests (100 → 100K records)
- [ ] Add end-to-end workflow performance tests
- [ ] Create performance regression detection
- [ ] Integrate with CI/CD pipeline

### Phase 5: Reporting & Documentation (Week 5)
- [ ] Build automated report generation
- [ ] Create performance dashboards
- [ ] Document performance targets and SLOs
- [ ] Write optimization recommendations

## 5. Performance Targets (SLOs)

### 5.1 API Response Times (p95)

| Priority | Endpoint | Target | Rationale |
|----------|----------|--------|-----------|
| P0 | GET /api/events/ | <500ms | Most frequent operation |
| P0 | GET /api/events/{slug}/ | <200ms | User engagement critical |
| P0 | POST /api/tickets/check-in/ | <100ms | Real-time operation |
| P1 | POST /api/tickets/order/ | <2s | Payment flow tolerance |
| P1 | GET /api/analytics/event/{id}/ | <1s | Admin dashboard |
| P2 | POST /api/food/order/ | <3s | Non-critical path |

### 5.2 Database Query Efficiency

- Maximum 3 queries for list endpoints (with pagination)
- Maximum 5 queries for detail endpoints (with nested relations)
- No N+1 queries in any endpoint
- All list queries must use `select_related()` or `prefetch_related()`

### 5.3 Concurrency

- Support 1000 concurrent users on event listing
- Support 100 concurrent ticket purchases (no overselling)
- Support 500 concurrent check-ins (no duplicates)

### 5.4 Scalability

- Event listing: <500ms for 10K events
- Analytics: <1s for 100K registrations
- Comment tree: <300ms for 1000 nested comments

## 6. CI/CD Integration

### 6.1 GitHub Actions Workflow

```yaml
name: Performance Tests

on:
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM

jobs:
  performance-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-benchmark locust

      - name: Run performance tests
        run: |
          pytest performance/ -v --benchmark-only \
            --benchmark-json=reports/benchmark.json

      - name: Check performance regression
        run: |
          python performance/check_regression.py \
            --current reports/benchmark.json \
            --baseline benchmarks/baseline.json \
            --threshold 20  # Fail if 20% slower

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: performance/reports/
```

### 6.2 Regression Detection

Fail CI if:
- Any endpoint p95 exceeds target by >20%
- Query count increases by >2 queries
- Memory usage increases by >30%
- New N+1 queries are introduced

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tests too slow for CI | Delays merges | Use parallel execution, optimize fixtures |
| Flaky tests | False positives | Use statistical analysis, multiple runs |
| Non-deterministic results | Unreliable metrics | Control environment, use containers |
| Database state pollution | Test interference | Use transactions, reset between tests |
| External service dependencies | Test failures | Mock Stripe/email, use local stubs |

## 8. Success Metrics

- **Coverage**: 100% of critical endpoints have performance tests
- **Stability**: <5% flaky test rate
- **Actionability**: All test failures include optimization recommendations
- **Adoption**: 0 performance regressions merged to main
- **Improvement**: 30% improvement in p95 response times within 6 months

## 9. Future Enhancements

- Real user monitoring (RUM) integration
- APM tool integration (New Relic, DataDog)
- Automated performance optimization suggestions
- Database query plan analysis
- Cache hit rate tracking
- CDN performance monitoring

## 10. References

- [Django Performance Optimization](https://docs.djangoproject.com/en/5.0/topics/performance/)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

## 11. Appendix

### A. Example Test Output

```
============================= test session starts ==============================
collected 24 items

performance/test_database_queries.py::test_event_listing_10k PASSED     [ 4%]
  Mean: 234.5ms, p95: 450.0ms, p99: 520.0ms ✓ (target: 500ms)

performance/test_api_endpoints.py::test_ticket_purchase PASSED          [ 8%]
  Mean: 1.2s, p95: 1.8s, p99: 1.95s ✓ (target: 2s)

performance/test_concurrency.py::test_no_overselling PASSED            [12%]
  200 concurrent purchases, 100 sold, 0 oversold ✓

========================= 24 passed in 45.23s ==========================
```

### B. Model Factory Example

```python
import factory
from faker import Faker
from events.models import Event, EventCategory

fake = Faker()

class EventCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EventCategory

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())

class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    title = factory.Faker('sentence', nb_words=5)
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    description = factory.Faker('paragraph', nb_sentences=5)
    organizer = factory.SubFactory('users.factories.UserFactory')
    category = factory.SubFactory(EventCategoryFactory)
    venue_name = factory.Faker('company')
    venue_address = factory.Faker('street_address')
    city = factory.Faker('city')
    country = factory.Faker('country')
    start_date = factory.Faker('future_datetime', end_date='+30d')
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timedelta(hours=3)
    )
    capacity = factory.Faker('random_int', min=50, max=1000)
    status = 'published'
    privacy = 'public'
```

---

**Decision**: Pending review and approval
**Next Steps**: Review with team, gather feedback, begin implementation
