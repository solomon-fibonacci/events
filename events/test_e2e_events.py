"""
End-to-End Tests for Event Management Flow
Tests the complete event lifecycle from creation to completion
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from events.models import Event, EventCategory, EventFavorite, EventComment

User = get_user_model()


class EventManagementE2ETest(TestCase):
    """E2E tests for event management"""

    def setUp(self):
        self.client = APIClient()

        # Create users
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='TestPass123!',
            role='organizer',
            first_name='Event',
            last_name='Organizer'
        )

        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            username='attendee',
            password='TestPass123!',
            role='attendee'
        )

        # Create category
        self.category = EventCategory.objects.create(
            name='Conference',
            slug='conference',
            description='Professional conferences'
        )

    def test_complete_event_creation_and_publication_flow(self):
        """Test creating an event from draft to published"""

        self.client.force_authenticate(user=self.organizer)

        # Step 1: Create event in draft status
        event_data = {
            'title': 'Tech Conference 2024',
            'slug': 'tech-conference-2024',
            'description': 'A conference about technology',
            'category': self.category.id,
            'venue_name': 'Convention Center',
            'venue_address': '123 Main St',
            'city': 'San Francisco',
            'state': 'CA',
            'country': 'USA',
            'start_date': (timezone.now() + timedelta(days=30)).isoformat(),
            'end_date': (timezone.now() + timedelta(days=32)).isoformat(),
            'capacity': 500,
            'status': 'draft',
            'privacy': 'public',
            'tags': 'tech, conference, networking'
        }

        response = self.client.post('/api/events/', event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        event_slug = response.data['slug']

        # Verify event is created
        event = Event.objects.get(slug=event_slug)
        self.assertEqual(event.organizer, self.organizer)
        self.assertEqual(event.status, 'draft')

        # Step 2: Update event to published
        update_data = {
            'title': 'Tech Conference 2024',
            'slug': 'tech-conference-2024',
            'description': 'A conference about technology - Updated',
            'category': self.category.id,
            'venue_name': 'Convention Center',
            'venue_address': '123 Main St',
            'city': 'San Francisco',
            'state': 'CA',
            'country': 'USA',
            'start_date': event_data['start_date'],
            'end_date': event_data['end_date'],
            'capacity': 500,
            'status': 'published',
            'privacy': 'public',
            'tags': 'tech, conference, networking'
        }

        response = self.client.put(f'/api/events/{event_slug}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify status changed
        event.refresh_from_db()
        self.assertEqual(event.status, 'published')

        # Step 3: Verify public can view published event
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/events/{event_slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Tech Conference 2024')

    def test_event_listing_and_filtering(self):
        """Test listing and filtering events"""

        self.client.force_authenticate(user=self.organizer)

        # Create multiple events
        for i in range(5):
            Event.objects.create(
                title=f'Event {i}',
                slug=f'event-{i}',
                description='Test event',
                organizer=self.organizer,
                category=self.category,
                venue_name='Test Venue',
                venue_address='123 Test St',
                city='San Francisco' if i < 3 else 'New York',
                country='USA',
                start_date=timezone.now() + timedelta(days=i),
                end_date=timezone.now() + timedelta(days=i+1),
                capacity=100,
                status='published',
                privacy='public'
            )

        # Step 1: List all events
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)

        # Step 2: Filter by city
        response = self.client.get('/api/events/?city=San Francisco')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        # Step 3: Filter by category
        response = self.client.get(f'/api/events/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)

        # Step 4: Search by title
        response = self.client.get('/api/events/?search=Event 2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_event_view_count_tracking(self):
        """Test that event views are tracked"""

        # Create event
        event = Event.objects.create(
            title='Test Event',
            slug='test-event',
            description='Test',
            organizer=self.organizer,
            venue_name='Test Venue',
            venue_address='123 Test St',
            city='Test City',
            country='USA',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            capacity=100,
            status='published',
            privacy='public'
        )

        initial_view_count = event.view_count

        # View event multiple times
        for i in range(3):
            response = self.client.get(f'/api/events/{event.slug}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify view count increased
        event.refresh_from_db()
        self.assertEqual(event.view_count, initial_view_count + 3)

    def test_organizer_can_only_edit_own_events(self):
        """Test that organizers can only edit their own events"""

        # Create another organizer
        other_organizer = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='TestPass123!',
            role='organizer'
        )

        # First organizer creates event
        event = Event.objects.create(
            title='First Organizer Event',
            slug='first-organizer-event',
            description='Test',
            organizer=self.organizer,
            venue_name='Test Venue',
            venue_address='123 Test St',
            city='Test City',
            country='USA',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            capacity=100,
            status='published',
            privacy='public'
        )

        # Other organizer tries to edit
        self.client.force_authenticate(user=other_organizer)
        update_data = {
            'title': 'Hacked Event',
            'slug': 'first-organizer-event',
            'description': 'Test',
            'venue_name': 'Test Venue',
            'venue_address': '123 Test St',
            'city': 'Test City',
            'country': 'USA',
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat(),
            'capacity': 100,
            'status': 'published',
            'privacy': 'public'
        }

        response = self.client.put(f'/api/events/{event.slug}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify event not changed
        event.refresh_from_db()
        self.assertEqual(event.title, 'First Organizer Event')

    def test_attendee_cannot_create_events(self):
        """Test that attendees cannot create events"""

        self.client.force_authenticate(user=self.attendee)

        event_data = {
            'title': 'Unauthorized Event',
            'slug': 'unauthorized-event',
            'description': 'Test',
            'venue_name': 'Test Venue',
            'venue_address': '123 Test St',
            'city': 'Test City',
            'country': 'USA',
            'start_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'end_date': (timezone.now() + timedelta(days=2)).isoformat(),
            'capacity': 100,
            'status': 'draft',
            'privacy': 'public'
        }

        response = self.client.post('/api/events/', event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EventFavoritesE2ETest(TestCase):
    """E2E tests for event favorites/bookmarks"""

    def setUp(self):
        self.client = APIClient()

        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='TestPass123!',
            role='organizer'
        )

        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            username='attendee',
            password='TestPass123!',
            role='attendee'
        )

        self.event = Event.objects.create(
            title='Test Event',
            slug='test-event',
            description='Test',
            organizer=self.organizer,
            venue_name='Test Venue',
            venue_address='123 Test St',
            city='Test City',
            country='USA',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            capacity=100,
            status='published',
            privacy='public'
        )

    def test_favorite_and_unfavorite_event_flow(self):
        """Test favoriting and unfavoriting an event"""

        self.client.force_authenticate(user=self.attendee)

        # Step 1: Favorite event
        response = self.client.post(f'/api/events/{self.event.slug}/favorite/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify favorite exists
        favorite_exists = EventFavorite.objects.filter(
            user=self.attendee,
            event=self.event
        ).exists()
        self.assertTrue(favorite_exists)

        # Step 2: Unfavorite event (same endpoint)
        response = self.client.post(f'/api/events/{self.event.slug}/favorite/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify favorite removed
        favorite_exists = EventFavorite.objects.filter(
            user=self.attendee,
            event=self.event
        ).exists()
        self.assertFalse(favorite_exists)


class EventCommentsE2ETest(TestCase):
    """E2E tests for event comments and Q&A"""

    def setUp(self):
        self.client = APIClient()

        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='TestPass123!',
            role='organizer'
        )

        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            username='attendee',
            password='TestPass123!',
            role='attendee'
        )

        self.event = Event.objects.create(
            title='Test Event',
            slug='test-event',
            description='Test',
            organizer=self.organizer,
            venue_name='Test Venue',
            venue_address='123 Test St',
            city='Test City',
            country='USA',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            capacity=100,
            status='published',
            privacy='public'
        )

    def test_comment_creation_and_reply_flow(self):
        """Test creating comments and replies"""

        self.client.force_authenticate(user=self.attendee)

        # Step 1: Create a comment
        comment_data = {
            'event': self.event.id,
            'content': 'What time does registration start?'
        }

        response = self.client.post('/api/comments/', comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        parent_comment_id = response.data['id']

        # Step 2: Organizer replies to comment
        self.client.force_authenticate(user=self.organizer)

        reply_data = {
            'event': self.event.id,
            'content': 'Registration starts at 9 AM',
            'parent': parent_comment_id
        }

        response = self.client.post('/api/comments/', reply_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 3: Verify comments are retrievable
        response = self.client.get(f'/api/comments/?event={self.event.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 2)

    def test_user_can_edit_own_comment(self):
        """Test that users can edit their own comments"""

        self.client.force_authenticate(user=self.attendee)

        # Create comment
        comment = EventComment.objects.create(
            event=self.event,
            user=self.attendee,
            content='Original comment'
        )

        # Update comment
        update_data = {
            'event': self.event.id,
            'content': 'Updated comment'
        }

        response = self.client.put(f'/api/comments/{comment.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify update
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Updated comment')

    def test_user_cannot_edit_others_comment(self):
        """Test that users cannot edit others' comments"""

        # Create comment as attendee
        comment = EventComment.objects.create(
            event=self.event,
            user=self.attendee,
            content='Attendee comment'
        )

        # Try to edit as organizer
        self.client.force_authenticate(user=self.organizer)

        update_data = {
            'event': self.event.id,
            'content': 'Hacked comment'
        }

        response = self.client.put(f'/api/comments/{comment.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify comment unchanged
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Attendee comment')
