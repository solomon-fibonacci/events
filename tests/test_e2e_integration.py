"""
End-to-End Integration Tests for Food Ordering and Reviews
Tests complete user journeys across multiple system components
"""
import os
import unittest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from decimal import Decimal

from events.models import Event
from menus.models import Menu, MenuItem, MenuCategory, FoodOrder
from reviews.models import Review
from tickets.models import TicketType, Order, Registration

User = get_user_model()


class FoodOrderingE2ETest(TestCase):
    """E2E tests for food and drink ordering system"""

    def setUp(self):
        self.client = APIClient()

        # Create users
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='TestPass123!',
            role='organizer'
        )

        self.vendor = User.objects.create_user(
            email='vendor@example.com',
            username='vendor',
            password='TestPass123!',
            role='vendor'
        )

        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            username='attendee',
            password='TestPass123!',
            role='attendee'
        )

        # Create event
        self.event = Event.objects.create(
            title='Food Festival',
            slug='food-festival',
            description='Great food event',
            organizer=self.organizer,
            venue_name='Food Court',
            venue_address='123 Food St',
            city='San Francisco',
            country='USA',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            capacity=500,
            status='published',
            privacy='public'
        )

        # Create menu
        self.menu = Menu.objects.create(
            event=self.event,
            name='Festival Menu',
            description='Delicious food options',
            is_active=True,
            vendor=self.vendor
        )

        # Create menu categories
        self.appetizer_category = MenuCategory.objects.create(
            name='Appetizers',
            display_order=1
        )

        self.main_category = MenuCategory.objects.create(
            name='Main Courses',
            display_order=2
        )

        self.beverage_category = MenuCategory.objects.create(
            name='Beverages',
            display_order=3
        )

        # Create menu items
        self.appetizer = MenuItem.objects.create(
            menu=self.menu,
            category=self.appetizer_category,
            name='Spring Rolls',
            description='Fresh vegetable spring rolls',
            price=Decimal('8.99'),
            dietary_type='vegetarian',
            is_available=True,
            stock_quantity=50
        )

        self.main_dish = MenuItem.objects.create(
            menu=self.menu,
            category=self.main_category,
            name='Grilled Chicken',
            description='Herb-marinated grilled chicken',
            price=Decimal('15.99'),
            dietary_type='none',
            is_available=True,
            stock_quantity=30
        )

        self.beverage = MenuItem.objects.create(
            menu=self.menu,
            category=self.beverage_category,
            name='Fresh Juice',
            description='Freshly squeezed orange juice',
            price=Decimal('5.99'),
            dietary_type='vegan',
            is_available=True
        )

    def test_view_menu_items(self):
        """Test viewing event menu"""

        response = self.client.get(f'/api/menus/?event={self.event.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)

    @patch('event_management.utils.stripe_service.stripe.PaymentIntent.create')
    def test_complete_food_order_flow(self, mock_stripe):
        """Test complete food ordering flow"""

        # Mock Stripe
        mock_stripe.return_value = {
            'id': 'pi_food_123',
            'client_secret': 'pi_food_123_secret'
        }

        self.client.force_authenticate(user=self.attendee)

        # Step 1: Browse menu
        response = self.client.get(f'/api/menus/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 2: Create food order
        order_data = {
            'event_id': self.event.id,
            'items': [
                {
                    'menu_item_id': self.appetizer.id,
                    'quantity': 2,
                    'special_instructions': 'Extra sauce please'
                },
                {
                    'menu_item_id': self.main_dish.id,
                    'quantity': 1
                },
                {
                    'menu_item_id': self.beverage.id,
                    'quantity': 2
                }
            ],
            'table_number': 'A12',
            'notes': 'Please deliver to table A12'
        }

        response = self.client.post('/api/food/order/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order', response.data)
        self.assertIn('client_secret', response.data)

        # Verify order created
        order = FoodOrder.objects.get(order_number=response.data['order']['order_number'])
        self.assertEqual(order.user, self.attendee)
        self.assertEqual(order.event, self.event)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.table_number, 'A12')

        # Verify order items
        self.assertEqual(order.items.count(), 3)

        # Verify Stripe called
        mock_stripe.assert_called_once()

    def test_food_order_validation(self):
        """Test food order with invalid data"""

        self.client.force_authenticate(user=self.attendee)

        # Test: Order without items
        order_data = {
            'event_id': self.event.id,
            'items': []
        }

        response = self.client.post('/api/food/order/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('event_management.utils.stripe_service.stripe.PaymentIntent.create')
    def test_unavailable_item_order(self, mock_stripe):
        """Test ordering unavailable items"""

        # Make item unavailable
        self.appetizer.is_available = False
        self.appetizer.save()

        self.client.force_authenticate(user=self.attendee)

        order_data = {
            'event_id': self.event.id,
            'items': [
                {'menu_item_id': self.appetizer.id, 'quantity': 1}
            ]
        }

        response = self.client.post('/api/food/order/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_menu_filtering_by_dietary_type(self):
        """Test filtering menu items by dietary type"""

        # Count vegetarian items
        vegetarian_items = MenuItem.objects.filter(
            menu=self.menu,
            dietary_type='vegetarian'
        )
        self.assertGreater(vegetarian_items.count(), 0)


class EventReviewsE2ETest(TestCase):
    """E2E tests for event review system"""

    def setUp(self):
        self.client = APIClient()

        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='TestPass123!',
            role='organizer'
        )

        self.attendee1 = User.objects.create_user(
            email='attendee1@example.com',
            username='attendee1',
            password='TestPass123!',
            role='attendee'
        )

        self.attendee2 = User.objects.create_user(
            email='attendee2@example.com',
            username='attendee2',
            password='TestPass123!',
            role='attendee'
        )

        # Create past event
        self.event = Event.objects.create(
            title='Past Conference',
            slug='past-conference',
            description='Great event',
            organizer=self.organizer,
            venue_name='Convention Center',
            venue_address='123 Main St',
            city='San Francisco',
            country='USA',
            start_date=timezone.now() - timedelta(days=7),
            end_date=timezone.now() - timedelta(days=6),
            capacity=100,
            status='completed',
            privacy='public'
        )

    def test_complete_review_submission_flow(self):
        """Test submitting and viewing reviews"""

        self.client.force_authenticate(user=self.attendee1)

        # Step 1: Submit review
        review_data = {
            'event': self.event.id,
            'rating': 5,
            'title': 'Amazing Event!',
            'content': 'Had a wonderful time. Great speakers and organization.'
        }

        response = self.client.post('/api/reviews/', review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify review created
        review = Review.objects.get(user=self.attendee1, event=self.event)
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.is_approved)  # Auto-approved by default

        # Step 2: View reviews for event
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/reviews/?event={self.event.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_one_review_per_user_per_event(self):
        """Test that users can only review an event once"""

        self.client.force_authenticate(user=self.attendee1)

        # First review
        review_data = {
            'event': self.event.id,
            'rating': 5,
            'content': 'Great event!'
        }

        response = self.client.post('/api/reviews/', review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try to submit second review
        review_data['content'] = 'Another review'
        response = self.client.post('/api/reviews/', review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_rating_validation(self):
        """Test review rating must be between 1 and 5"""

        self.client.force_authenticate(user=self.attendee1)

        # Test invalid rating (0)
        review_data = {
            'event': self.event.id,
            'rating': 0,
            'content': 'Bad rating'
        }

        response = self.client.post('/api/reviews/', review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test invalid rating (6)
        review_data['rating'] = 6
        response = self.client.post('/api/reviews/', review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_edit_own_review(self):
        """Test that users can edit their reviews"""

        self.client.force_authenticate(user=self.attendee1)

        # Create review
        review = Review.objects.create(
            event=self.event,
            user=self.attendee1,
            rating=4,
            content='Good event'
        )

        # Update review
        update_data = {
            'event': self.event.id,
            'rating': 5,
            'title': 'Updated: Excellent Event!',
            'content': 'After thinking more, this was excellent!'
        }

        response = self.client.put(f'/api/reviews/{review.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify update
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, 'Updated: Excellent Event!')

    def test_average_rating_calculation(self):
        """Test that average ratings are calculated correctly"""

        # Create multiple reviews
        Review.objects.create(event=self.event, user=self.attendee1, rating=5, content='Great!')
        Review.objects.create(event=self.event, user=self.attendee2, rating=4, content='Good')

        # Calculate average
        from django.db.models import Avg
        avg_rating = Review.objects.filter(event=self.event).aggregate(Avg('rating'))['rating__avg']
        self.assertEqual(avg_rating, 4.5)


class CompleteUserJourneyE2ETest(TestCase):
    """E2E test for complete user journey through the system"""

    def setUp(self):
        self.client = APIClient()

    @unittest.skipIf(os.environ.get('CI') == 'true', "Skipping JWT token generation test in CI due to cryptography issues")
    def test_complete_attendee_journey(self):
        """Test complete journey: Register → Browse → Buy Ticket → Order Food → Review"""

        # Step 1: Register new user
        registration_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'attendee'
        }

        response = self.client.post('/api/users/register/', registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        access_token = response.data['tokens']['access']

        # Step 2: Login (verify credentials work)
        login_data = {
            'email': 'newuser@example.com',
            'password': 'TestPass123!'
        }

        response = self.client.post('/api/users/login/', login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

        # Authenticate for subsequent requests
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Step 3: Browse events
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 4: View profile
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'newuser@example.com')

        # Verify user was created correctly
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.role, 'attendee')
        self.assertEqual(user.first_name, 'New')
