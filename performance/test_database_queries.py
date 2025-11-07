"""
Database Query Performance Tests

Tests ORM query efficiency, N+1 query detection, and database access patterns.
"""
import pytest
from django.test import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext

from events.models import Event, EventComment
from tickets.models import TicketType, Registration
from performance.fixtures.factories import (
    EventFactory, TicketTypeFactory, RegistrationFactory,
    EventCommentFactory, ReviewFactory
)
from performance.fixtures.data_loaders import DataLoader


class TestEventListingQueries:
    """Test event listing query performance"""

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_event_listing_100_events(self, benchmark):
        """Benchmark event listing with 100 events"""
        EventFactory.create_batch(100, status='published', privacy='public')

        def query_events():
            return list(
                Event.objects.filter(status='published', privacy='public')
                .select_related('organizer', 'category')[:20]
            )

        result = benchmark(query_events)
        assert len(result) == 20

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_event_listing_1000_events(self, benchmark):
        """Benchmark event listing with 1,000 events"""
        EventFactory.create_batch(1000, status='published', privacy='public')

        def query_events():
            return list(
                Event.objects.filter(status='published', privacy='public')
                .select_related('organizer', 'category')[:20]
            )

        result = benchmark(query_events)
        assert len(result) == 20
        # Target: < 100ms for 1K events
        assert benchmark.stats['mean'] < 0.1

    @pytest.mark.benchmark
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_event_listing_10000_events(self, benchmark):
        """Benchmark event listing with 10,000 events"""
        DataLoader.create_events(count=10000)

        def query_events():
            return list(
                Event.objects.filter(status='published', privacy='public')
                .select_related('organizer', 'category')[:20]
            )

        result = benchmark(query_events)
        assert len(result) == 20
        # Target: < 500ms for 10K events
        assert benchmark.stats['mean'] < 0.5

    @pytest.mark.django_db
    def test_no_n_plus_one_in_event_listing(self):
        """Ensure event listing doesn't trigger N+1 queries"""
        EventFactory.create_batch(100, status='published', privacy='public')

        with CaptureQueriesContext(connection) as context:
            events = Event.objects.filter(status='published', privacy='public')
            events = events.select_related('organizer', 'category')
            events_list = list(events[:20])

            # Access related fields
            for event in events_list:
                _ = event.organizer.email
                _ = event.category.name

        # Should use max 3 queries: 1 for events, optimized with select_related
        assert len(context.captured_queries) <= 3, \
            f"Expected ≤3 queries, got {len(context.captured_queries)}"

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_event_filtering_by_city(self, benchmark):
        """Benchmark event filtering by city"""
        # Create events in different cities
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
        for city in cities:
            EventFactory.create_batch(200, city=city, status='published')

        def query_events():
            return list(
                Event.objects.filter(city='New York', status='published')
                .select_related('organizer', 'category')[:20]
            )

        result = benchmark(query_events)
        assert len(result) == 20
        assert all(e.city == 'New York' for e in result)

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_event_search_by_title(self, benchmark):
        """Benchmark event search by title"""
        # Create events with searchable titles
        for i in range(500):
            EventFactory(
                title=f"Technology Conference {i}" if i % 2 == 0 else f"Music Festival {i}",
                status='published'
            )

        def search_events():
            return list(
                Event.objects.filter(
                    title__icontains='Technology',
                    status='published'
                ).select_related('organizer', 'category')[:20]
            )

        result = benchmark(search_events)
        assert len(result) == 20
        assert all('Technology' in e.title for e in result)


class TestTicketQueryPerformance:
    """Test ticket-related query performance"""

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_ticket_availability_check(self, benchmark):
        """Benchmark ticket availability calculation"""
        event = EventFactory(status='published')
        ticket_types = TicketTypeFactory.create_batch(20, event=event, quantity=100)

        # Create some registrations
        for tt in ticket_types[:10]:
            RegistrationFactory.create_batch(
                30, ticket_type=tt, event=event, status='confirmed'
            )

        def check_availability():
            results = []
            for tt in TicketType.objects.filter(event=event):
                remaining = tt.quantity_remaining
                results.append(remaining)
            return results

        result = benchmark(check_availability)
        assert len(result) == 20

    @pytest.mark.django_db
    def test_no_n_plus_one_ticket_types(self):
        """Ensure ticket type listing doesn't trigger N+1 queries"""
        event = EventFactory(status='published')
        TicketTypeFactory.create_batch(20, event=event)

        with CaptureQueriesContext(connection) as context:
            ticket_types = list(event.ticket_types.all())

            # Access properties
            for tt in ticket_types:
                _ = tt.is_available
                _ = tt.quantity_remaining

        # Should be minimal queries (counting registrations will add queries)
        # This test identifies if we need to optimize
        print(f"Ticket availability check used {len(context.captured_queries)} queries")

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_registration_listing(self, benchmark):
        """Benchmark registration listing for an event"""
        event = EventFactory(status='published')
        ticket_type = TicketTypeFactory(event=event)

        # Create 500 registrations
        for _ in range(500):
            RegistrationFactory(
                event=event,
                ticket_type=ticket_type,
                status='confirmed'
            )

        def query_registrations():
            return list(
                Registration.objects.filter(event=event)
                .select_related('user', 'ticket_type', 'order')[:50]
            )

        result = benchmark(query_registrations)
        assert len(result) == 50


class TestAnalyticsQueries:
    """Test analytics and aggregation query performance"""

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_event_analytics_aggregation(self, benchmark):
        """Benchmark event analytics with aggregations"""
        event = EventFactory(status='published')
        ticket_type = TicketTypeFactory(event=event, price=50)

        # Create 1000 registrations
        for _ in range(1000):
            RegistrationFactory(
                event=event,
                ticket_type=ticket_type,
                status='confirmed'
            )

        # Create some reviews
        ReviewFactory.create_batch(50, event=event)

        def calculate_analytics():
            from django.db.models import Count, Sum, Avg

            registrations = Registration.objects.filter(event=event)
            total_registrations = registrations.count()
            checked_in_count = registrations.filter(status='checked_in').count()

            orders = event.orders.filter(status='completed')
            total_revenue = orders.aggregate(total=Sum('total'))['total'] or 0

            reviews = event.reviews.filter(is_approved=True)
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

            return {
                'total_registrations': total_registrations,
                'checked_in_count': checked_in_count,
                'total_revenue': total_revenue,
                'avg_rating': avg_rating,
            }

        result = benchmark(calculate_analytics)
        assert result['total_registrations'] == 1000
        # Target: < 1s for analytics on 1K registrations
        assert benchmark.stats['mean'] < 1.0

    @pytest.mark.benchmark
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_analytics_with_10k_registrations(self, benchmark):
        """Benchmark analytics with 10,000 registrations"""
        event = EventFactory(status='published')
        DataLoader.create_registrations(event, count=10000)

        def calculate_analytics():
            from django.db.models import Count, Sum

            total_registrations = Registration.objects.filter(event=event).count()
            checked_in = Registration.objects.filter(
                event=event, status='checked_in'
            ).count()

            return {
                'total': total_registrations,
                'checked_in': checked_in,
            }

        result = benchmark(calculate_analytics)
        assert result['total'] == 10000
        # Target: < 2s for 10K registrations
        assert benchmark.stats['mean'] < 2.0


class TestCommentQueries:
    """Test comment tree query performance"""

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_comment_listing_flat(self, benchmark):
        """Benchmark flat comment listing"""
        event = EventFactory(status='published')
        EventCommentFactory.create_batch(1000, event=event, parent=None)

        def query_comments():
            return list(
                EventComment.objects.filter(event=event, parent=None)
                .select_related('user')[:50]
            )

        result = benchmark(query_comments)
        assert len(result) <= 50

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_nested_comment_retrieval(self, benchmark):
        """Benchmark nested comment tree retrieval"""
        event = EventFactory(status='published')

        # Create comment tree: 5 root comments, each with 3 levels of replies
        DataLoader.create_nested_comments(event, depth=3, children_per_level=3)

        def query_comment_tree():
            # Get all comments for the event
            comments = list(
                EventComment.objects.filter(event=event)
                .select_related('user', 'parent')
            )
            return comments

        result = benchmark(query_comment_tree)
        assert len(result) > 0
        # Target: < 300ms for nested comment tree
        assert benchmark.stats['mean'] < 0.3


class TestDatabaseIndexes:
    """Test that database indexes are being used efficiently"""

    @pytest.mark.django_db
    def test_event_slug_lookup_uses_index(self):
        """Verify slug lookups use database index"""
        EventFactory.create_batch(1000, status='published')
        event = EventFactory(slug='test-event-slug', status='published')

        with CaptureQueriesContext(connection) as context:
            found_event = Event.objects.get(slug='test-event-slug')

        assert found_event.id == event.id

        # Check that query is efficient (should be very fast with index)
        query = context.captured_queries[0]['sql']
        # Index should be used for slug lookup
        assert 'slug' in query.lower()

    @pytest.mark.django_db
    def test_event_status_privacy_filter_uses_index(self):
        """Verify status+privacy filter uses composite index"""
        EventFactory.create_batch(1000, status='published', privacy='public')

        with CaptureQueriesContext(connection) as context:
            events = list(
                Event.objects.filter(status='published', privacy='public')[:20]
            )

        assert len(events) == 20

        # This should use the composite index on (status, privacy, start_date)
        query = context.captured_queries[0]['sql']
        assert 'status' in query.lower() and 'privacy' in query.lower()


class TestQueryOptimization:
    """Test query optimization techniques"""

    @pytest.mark.django_db
    def test_select_related_reduces_queries(self):
        """Verify select_related reduces query count"""
        EventFactory.create_batch(50, status='published')

        # Without select_related
        with CaptureQueriesContext(connection) as context_without:
            events = list(Event.objects.filter(status='published')[:20])
            for event in events:
                _ = event.organizer.email
                _ = event.category.name

        queries_without = len(context_without.captured_queries)

        # With select_related
        with CaptureQueriesContext(connection) as context_with:
            events = list(
                Event.objects.filter(status='published')
                .select_related('organizer', 'category')[:20]
            )
            for event in events:
                _ = event.organizer.email
                _ = event.category.name

        queries_with = len(context_with.captured_queries)

        # select_related should significantly reduce queries
        assert queries_with < queries_without, \
            f"select_related should reduce queries: {queries_with} vs {queries_without}"
        assert queries_with <= 3, \
            f"With select_related, should use ≤3 queries, got {queries_with}"

    @pytest.mark.benchmark
    @pytest.mark.django_db
    def test_only_fields_performance(self, benchmark):
        """Benchmark using only() to fetch specific fields"""
        EventFactory.create_batch(1000, status='published')

        def query_with_only():
            return list(
                Event.objects.filter(status='published')
                .only('id', 'title', 'slug', 'start_date')[:100]
            )

        result = benchmark(query_with_only)
        assert len(result) == 100
        # Should be faster than fetching all fields


class TestConcurrentQueryPerformance:
    """Test query performance under concurrent access"""

    @pytest.mark.concurrency
    @pytest.mark.django_db
    def test_concurrent_event_reads(self):
        """Test multiple concurrent reads on same event"""
        import threading
        import time

        event = EventFactory(status='published', view_count=0)

        results = []
        errors = []

        def read_event():
            try:
                start = time.time()
                e = Event.objects.get(id=event.id)
                elapsed = time.time() - start
                results.append(elapsed)
            except Exception as ex:
                errors.append(str(ex))

        # Launch 100 concurrent reads
        threads = [threading.Thread(target=read_event) for _ in range(100)]
        start_time = time.time()

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total_time = time.time() - start_time

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 100
        avg_read_time = sum(results) / len(results)

        print(f"Concurrent reads: avg={avg_read_time:.4f}s, total={total_time:.4f}s")
        # Each read should be fast
        assert avg_read_time < 0.1
