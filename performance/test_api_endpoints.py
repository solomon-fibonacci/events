"""
API Endpoint Performance Tests

Tests API response times, throughput, and latency under various load conditions.
"""
import pytest
import time
from unittest import mock
from django.urls import reverse
from rest_framework import status

from performance.fixtures.factories import (
    EventFactory, UserFactory, OrganizerFactory,
    TicketTypeFactory, RegistrationFactory, OrderFactory
)
from performance.fixtures.data_loaders import DataLoader


class TestEventAPIPerformance:
    """Test Event API endpoint performance"""

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_event_list_api_100_events(self, api_client, benchmark):
        """Test event listing API with 100 events"""
        EventFactory.create_batch(100, status='published', privacy='public')

        def call_api():
            response = api_client.get('/api/events/')
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        assert 'results' in data
        # Target: < 200ms for 100 events
        assert benchmark.stats['mean'] < 0.2

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_event_list_api_1000_events(self, api_client, benchmark):
        """Test event listing API with 1,000 events"""
        EventFactory.create_batch(1000, status='published', privacy='public')

        def call_api():
            response = api_client.get('/api/events/')
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        # Target: < 300ms for 1K events
        assert benchmark.stats['mean'] < 0.3

    @pytest.mark.performance
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_event_list_api_10000_events(self, api_client, benchmark):
        """Test event listing API with 10,000 events"""
        DataLoader.create_events(count=10000)

        def call_api():
            response = api_client.get('/api/events/')
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        assert len(data['results']) == 20  # Page size is 20
        # Target: < 500ms for 10K events
        assert benchmark.stats['mean'] < 0.5

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_event_detail_api(self, api_client, benchmark):
        """Test event detail API response time"""
        event = EventFactory(status='published', privacy='public')
        url = f'/api/events/{event.slug}/'

        def call_api():
            response = api_client.get(url)
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        assert data['slug'] == event.slug
        # Target: < 200ms for detail view
        assert benchmark.stats['mean'] < 0.2

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_event_filtering_performance(self, api_client, benchmark):
        """Test event filtering with multiple filters"""
        # Create diverse dataset
        cities = ['New York', 'Los Angeles', 'Chicago']
        for city in cities:
            EventFactory.create_batch(200, city=city, status='published', privacy='public')

        def call_api():
            response = api_client.get('/api/events/', {
                'city': 'New York',
                'status': 'published',
                'privacy': 'public',
            })
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        # Verify filtering works
        for event in data['results']:
            assert event['city'] == 'New York'
        # Target: < 300ms with filters
        assert benchmark.stats['mean'] < 0.3

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_event_search_performance(self, api_client, benchmark):
        """Test event search performance"""
        # Create searchable events
        for i in range(500):
            title = f"Tech Conference {i}" if i % 2 == 0 else f"Music Festival {i}"
            EventFactory(title=title, status='published', privacy='public')

        def call_api():
            response = api_client.get('/api/events/', {'search': 'Tech Conference'})
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        # Verify search works
        for event in data['results']:
            assert 'Tech Conference' in event['title']
        # Target: < 400ms for search
        assert benchmark.stats['mean'] < 0.4

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_event_creation_api(self, organizer_client, benchmark):
        """Test event creation performance"""
        from events.models import EventCategory
        category = EventCategory.objects.create(name='Technology', slug='technology')

        event_data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'category': category.id,
            'venue_name': 'Test Venue',
            'venue_address': '123 Test St',
            'city': 'Test City',
            'country': 'United States',
            'start_date': '2025-12-01T10:00:00Z',
            'end_date': '2025-12-01T18:00:00Z',
            'capacity': 100,
            'status': 'published',
            'privacy': 'public',
        }

        def call_api():
            response = organizer_client.post('/api/events/', event_data, format='json')
            assert response.status_code == 201
            # Clean up
            from events.models import Event
            Event.objects.filter(title='Test Event').delete()
            return response

        result = benchmark(call_api)
        # Target: < 300ms for event creation
        assert benchmark.stats['mean'] < 0.3


class TestTicketAPIPerformance:
    """Test Ticket API endpoint performance"""

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_ticket_types_listing(self, api_client, benchmark):
        """Test ticket types listing performance"""
        event = EventFactory(status='published', privacy='public')
        TicketTypeFactory.create_batch(20, event=event)

        url = f'/api/events/{event.slug}/ticket_types/'

        def call_api():
            response = api_client.get(url)
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        assert len(data) == 20
        # Target: < 200ms for ticket types
        assert benchmark.stats['mean'] < 0.2

    @pytest.mark.performance
    @pytest.mark.django_db
    @mock.patch('event_management.utils.stripe_service.StripeService.create_payment_intent')
    def test_ticket_order_api(self, mock_stripe, authenticated_client, benchmark):
        """Test ticket ordering performance"""
        # Mock Stripe to avoid external API calls
        mock_stripe.return_value = {
            'id': 'pi_test_123',
            'client_secret': 'secret_test_123',
            'status': 'succeeded'
        }

        event = EventFactory(status='published', privacy='public')
        ticket_type = TicketTypeFactory(event=event, price=50, quantity=1000)

        order_data = {
            'event_id': event.id,
            'tickets': [
                {
                    'ticket_type_id': ticket_type.id,
                    'quantity': 2
                }
            ],
            'payment_method_id': 'pm_test_123'
        }

        def call_api():
            response = authenticated_client.post(
                '/api/tickets/order/',
                order_data,
                format='json'
            )
            # Clean up
            if response.status_code == 201:
                from tickets.models import Order
                Order.objects.filter(event=event).delete()
            return response

        result = benchmark(call_api)
        # Target: < 2s for ticket purchase (includes payment processing)
        assert benchmark.stats['mean'] < 2.0

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_my_tickets_api(self, authenticated_client, benchmark):
        """Test my tickets listing performance"""
        user = authenticated_client.handler._force_user

        # Create 50 tickets for the user
        for _ in range(50):
            event = EventFactory(status='published')
            ticket_type = TicketTypeFactory(event=event)
            order = OrderFactory(user=user, event=event)
            RegistrationFactory(
                user=user,
                event=event,
                ticket_type=ticket_type,
                order=order,
                status='confirmed'
            )

        def call_api():
            response = authenticated_client.get('/api/tickets/my-tickets/')
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        assert len(data['results']) > 0
        # Target: < 300ms for ticket listing
        assert benchmark.stats['mean'] < 0.3

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_ticket_checkin_api(self, organizer_client, benchmark):
        """Test ticket check-in performance"""
        organizer = organizer_client.handler._force_user
        event = EventFactory(status='published', organizer=organizer)
        ticket_type = TicketTypeFactory(event=event)
        user = UserFactory()
        order = OrderFactory(user=user, event=event)

        # Create registration
        registration = RegistrationFactory(
            user=user,
            event=event,
            ticket_type=ticket_type,
            order=order,
            status='confirmed'
        )

        checkin_data = {
            'ticket_number': registration.ticket_number
        }

        def call_api():
            response = organizer_client.post(
                '/api/tickets/check-in/',
                checkin_data,
                format='json'
            )
            # Reset status for next iteration
            if response.status_code == 200:
                registration.status = 'confirmed'
                registration.save()
            return response

        result = benchmark(call_api)
        # Target: < 100ms for check-in (real-time operation)
        assert benchmark.stats['mean'] < 0.1


class TestUserAPIPerformance:
    """Test User API endpoint performance"""

    @pytest.mark.performance
    @pytest.mark.django_db
    @mock.patch('event_management.utils.email_service.EmailService.send_verification_email')
    def test_user_registration_api(self, mock_email, api_client, benchmark):
        """Test user registration performance"""
        # Mock email to avoid external API calls
        mock_email.return_value = True

        registration_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'attendee'
        }

        def call_api():
            # Use unique email each time
            import uuid
            data = registration_data.copy()
            data['email'] = f'user{uuid.uuid4()}@example.com'
            data['username'] = f'user{uuid.uuid4().hex[:10]}'

            response = api_client.post('/api/users/register/', data, format='json')
            return response

        result = benchmark(call_api)
        # Target: < 500ms for registration
        assert benchmark.stats['mean'] < 0.5

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_user_login_api(self, api_client, benchmark):
        """Test user login performance"""
        user = UserFactory(email='testuser@example.com')
        user.set_password('testpass123')
        user.save()

        login_data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }

        def call_api():
            response = api_client.post('/api/users/login/', login_data, format='json')
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        assert 'access' in data
        # Target: < 300ms for login
        assert benchmark.stats['mean'] < 0.3

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_user_profile_api(self, authenticated_client, benchmark):
        """Test user profile retrieval performance"""

        def call_api():
            response = authenticated_client.get('/api/users/profile/')
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        # Target: < 200ms for profile
        assert benchmark.stats['mean'] < 0.2


class TestAnalyticsAPIPerformance:
    """Test Analytics API endpoint performance"""

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_event_analytics_api(self, organizer_client, benchmark):
        """Test event analytics API performance"""
        organizer = organizer_client.handler._force_user
        event = EventFactory(status='published', organizer=organizer)

        # Create data for analytics
        ticket_type = TicketTypeFactory(event=event, price=50)
        for _ in range(100):
            user = UserFactory()
            order = OrderFactory(user=user, event=event, total=50)
            RegistrationFactory(
                user=user,
                event=event,
                ticket_type=ticket_type,
                order=order,
                status='confirmed'
            )

        url = f'/api/analytics/event/{event.id}/'

        def call_api():
            response = organizer_client.get(url)
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        data = result.json()
        assert 'total_registrations' in data or 'registrations' in str(data)
        # Target: < 1s for analytics
        assert benchmark.stats['mean'] < 1.0

    @pytest.mark.performance
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_analytics_with_large_dataset(self, organizer_client, benchmark):
        """Test analytics with 1000 registrations"""
        organizer = organizer_client.handler._force_user
        event = EventFactory(status='published', organizer=organizer)

        # Create large dataset
        DataLoader.create_registrations(event, count=1000)

        url = f'/api/analytics/event/{event.id}/'

        def call_api():
            response = organizer_client.get(url)
            return response

        result = benchmark(call_api)
        # Target: < 2s for analytics with 1K registrations
        assert benchmark.stats['mean'] < 2.0


class TestPaginationPerformance:
    """Test pagination performance across different pages"""

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_first_page_performance(self, api_client, benchmark):
        """Test first page load performance"""
        EventFactory.create_batch(500, status='published', privacy='public')

        def call_api():
            response = api_client.get('/api/events/', {'page': 1})
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        # First page should be fast
        assert benchmark.stats['mean'] < 0.3

    @pytest.mark.performance
    @pytest.mark.django_db
    def test_last_page_performance(self, api_client, benchmark):
        """Test last page load performance"""
        EventFactory.create_batch(500, status='published', privacy='public')

        def call_api():
            # Page 25 (500 events / 20 per page)
            response = api_client.get('/api/events/', {'page': 25})
            assert response.status_code == 200
            return response

        result = benchmark(call_api)
        # Last page might be slower, but should still be reasonable
        assert benchmark.stats['mean'] < 0.5
