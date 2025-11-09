"""
Shared fixtures for performance tests.

Provides common test data and configuration for all performance tests.
"""
import pytest
from django.test import Client
from rest_framework.test import APIClient
from django.core.management import call_command

from performance.fixtures.factories import (
    UserFactory, OrganizerFactory, EventFactory, EventCategoryFactory,
    TicketTypeFactory, OrderFactory, RegistrationFactory
)
from performance.fixtures.data_loaders import DataLoader


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Set up database for performance tests.
    Runs migrations once per test session.
    """
    with django_db_blocker.unblock():
        call_command('migrate', '--run-syncdb')


@pytest.fixture
def api_client():
    """Provide an unauthenticated API client"""
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    """Provide an authenticated API client"""
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def organizer_client(db):
    """Provide an authenticated API client for an organizer"""
    organizer = OrganizerFactory()
    client = APIClient()
    client.force_authenticate(user=organizer)
    return client


@pytest.fixture
def sample_event(db):
    """Create a single event for testing"""
    return EventFactory(status='published', privacy='public')


@pytest.fixture
def sample_event_with_tickets(db):
    """Create an event with ticket types"""
    event = EventFactory(status='published', privacy='public')
    TicketTypeFactory.create_batch(3, event=event)
    return event


@pytest.fixture
def small_event_dataset(db):
    """Create 100 events for small-scale testing"""
    return EventFactory.create_batch(100, status='published', privacy='public')


@pytest.fixture
def medium_event_dataset(db):
    """Create 1,000 events for medium-scale testing"""
    return DataLoader.create_events(count=1000)


@pytest.fixture
def large_event_dataset(db):
    """Create 10,000 events for large-scale testing"""
    return DataLoader.create_events(count=10000)


@pytest.fixture
def xlarge_event_dataset(db):
    """Create 100,000 events for extra-large-scale testing"""
    return DataLoader.create_events(count=100000)


@pytest.fixture
def event_with_registrations(db):
    """Create an event with 100 registrations"""
    event = EventFactory(status='published', privacy='public')
    TicketTypeFactory.create_batch(3, event=event)
    DataLoader.create_registrations(event, count=100)
    return event


@pytest.fixture
def event_with_many_registrations(db):
    """Create an event with 10,000 registrations"""
    event = EventFactory(status='published', privacy='public')
    TicketTypeFactory.create_batch(3, event=event)
    DataLoader.create_registrations(event, count=10000)
    return event


@pytest.fixture
def categories(db):
    """Create standard event categories"""
    return [
        EventCategoryFactory(name='Music', slug='music'),
        EventCategoryFactory(name='Sports', slug='sports'),
        EventCategoryFactory(name='Technology', slug='technology'),
        EventCategoryFactory(name='Food', slug='food'),
        EventCategoryFactory(name='Art', slug='art'),
        EventCategoryFactory(name='Business', slug='business'),
    ]


@pytest.fixture
def cleanup_db(db):
    """Clean up database after test"""
    yield
    # Cleanup happens after test
    DataLoader.clear_all()


# Benchmark configuration
@pytest.fixture
def benchmark_config():
    """Configure pytest-benchmark settings"""
    return {
        'min_rounds': 5,
        'max_time': 1.0,
        'warmup': True,
        'warmup_iterations': 2,
    }


# Performance test markers
def pytest_configure(config):
    """Register custom markers for performance tests"""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a benchmark test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "concurrency: mark test as a concurrency test"
    )
    config.addinivalue_line(
        "markers", "scalability: mark test as a scalability test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running (> 1 minute)"
    )
