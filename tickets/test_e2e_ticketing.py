"""
End-to-End Tests for Ticketing and Payment Flow
Tests the complete ticket purchase journey from selection to check-in
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from decimal import Decimal

from events.models import Event, EventCategory
from tickets.models import TicketType, Order, Registration, Refund

User = get_user_model()


class TicketPurchaseE2ETest(TestCase):
    """E2E tests for ticket purchase flow"""

    def setUp(self):
        self.client = APIClient()

        # Create users
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

        # Create event
        self.event = Event.objects.create(
            title='Test Conference',
            slug='test-conference',
            description='Test event',
            organizer=self.organizer,
            venue_name='Convention Center',
            venue_address='123 Main St',
            city='San Francisco',
            country='USA',
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=32),
            capacity=500,
            status='published',
            privacy='public'
        )

        # Create ticket types
        self.general_ticket = TicketType.objects.create(
            event=self.event,
            name='General Admission',
            description='Standard entry',
            price=Decimal('50.00'),
            quantity=300,
            is_active=True
        )

        self.vip_ticket = TicketType.objects.create(
            event=self.event,
            name='VIP Pass',
            description='Premium experience',
            price=Decimal('150.00'),
            quantity=50,
            is_active=True
        )

    @patch('event_management.utils.stripe_service.stripe.PaymentIntent.create')
    @patch('event_management.utils.qr_service.QRCodeService.generate_ticket_qr_code')
    def test_complete_ticket_purchase_flow(self, mock_qr, mock_stripe):
        """Test complete flow from ticket selection to purchase confirmation"""

        # Mock Stripe response
        mock_stripe.return_value = {
            'id': 'pi_test_123',
            'client_secret': 'pi_test_123_secret'
        }

        # Mock QR code generation
        mock_qr.return_value = MagicMock()

        self.client.force_authenticate(user=self.attendee)

        # Step 1: View available ticket types
        response = self.client.get(f'/api/events/{self.event.slug}/ticket_types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Step 2: Create order with tickets
        order_data = {
            'event_id': self.event.id,
            'tickets': [
                {'ticket_type_id': self.general_ticket.id, 'quantity': 2},
                {'ticket_type_id': self.vip_ticket.id, 'quantity': 1}
            ]
        }

        response = self.client.post('/api/tickets/order/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order', response.data)
        self.assertIn('client_secret', response.data)

        order = Order.objects.get(order_number=response.data['order']['order_number'])

        # Verify order details
        self.assertEqual(order.user, self.attendee)
        self.assertEqual(order.event, self.event)
        self.assertEqual(order.status, 'pending')

        # Verify registrations created
        registrations = Registration.objects.filter(order=order)
        self.assertEqual(registrations.count(), 3)  # 2 general + 1 VIP

        # Verify ticket quantities updated
        self.general_ticket.refresh_from_db()
        self.vip_ticket.refresh_from_db()
        self.assertEqual(self.general_ticket.quantity_sold, 2)
        self.assertEqual(self.vip_ticket.quantity_sold, 1)

        # Verify Stripe was called
        mock_stripe.assert_called_once()

        # Step 3: Simulate payment success (in real scenario, webhook handles this)
        order.status = 'completed'
        order.paid_at = timezone.now()
        order.save()

        for registration in registrations:
            registration.status = 'confirmed'
            registration.save()

        # Step 4: View my tickets
        response = self.client.get('/api/tickets/my-tickets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_ticket_purchase_validation(self):
        """Test ticket purchase with invalid data"""

        self.client.force_authenticate(user=self.attendee)

        # Test: Order without tickets
        order_data = {
            'event_id': self.event.id,
            'tickets': []
        }

        response = self.client.post('/api/tickets/order/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test: Order with invalid ticket type
        order_data = {
            'event_id': self.event.id,
            'tickets': [
                {'ticket_type_id': 9999, 'quantity': 1}
            ]
        }

        response = self.client.post('/api/tickets/order/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('event_management.utils.stripe_service.stripe.PaymentIntent.create')
    @patch('event_management.utils.qr_service.QRCodeService.generate_ticket_qr_code')
    def test_ticket_sold_out_scenario(self, mock_qr, mock_stripe):
        """Test purchasing when tickets are sold out"""

        # Mock Stripe and QR
        mock_stripe.return_value = {'id': 'pi_test_123', 'client_secret': 'secret'}
        mock_qr.return_value = MagicMock()

        # Set ticket to only 1 remaining
        self.general_ticket.quantity = 1
        self.general_ticket.save()

        self.client.force_authenticate(user=self.attendee)

        # Try to order 2 tickets
        order_data = {
            'event_id': self.event.id,
            'tickets': [
                {'ticket_type_id': self.general_ticket.id, 'quantity': 2}
            ]
        }

        response = self.client.post('/api/tickets/order/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class TicketCheckInE2ETest(TestCase):
    """E2E tests for ticket check-in system"""

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

        self.staff = User.objects.create_user(
            email='staff@example.com',
            username='staff',
            password='TestPass123!',
            role='organizer'  # Staff member checking in attendees
        )

        # Create event with ticket
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

        ticket_type = TicketType.objects.create(
            event=self.event,
            name='General',
            price=Decimal('50.00'),
            quantity=100
        )

        # Create order and registration
        self.order = Order.objects.create(
            user=self.attendee,
            event=self.event,
            subtotal=Decimal('50.00'),
            tax=Decimal('4.00'),
            service_fee=Decimal('2.50'),
            total=Decimal('56.50'),
            status='completed'
        )

        self.registration = Registration.objects.create(
            order=self.order,
            event=self.event,
            user=self.attendee,
            ticket_type=ticket_type,
            status='confirmed'
        )

    def test_successful_check_in_flow(self):
        """Test checking in a valid ticket"""

        self.client.force_authenticate(user=self.staff)

        check_in_data = {
            'ticket_number': self.registration.ticket_number
        }

        response = self.client.post('/api/tickets/check-in/', check_in_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify registration status updated
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, 'checked_in')
        self.assertIsNotNone(self.registration.checked_in_at)
        self.assertEqual(self.registration.checked_in_by, self.staff)

    def test_duplicate_check_in_prevention(self):
        """Test that tickets cannot be checked in twice"""

        # First check-in
        self.registration.status = 'checked_in'
        self.registration.checked_in_at = timezone.now()
        self.registration.save()

        self.client.force_authenticate(user=self.staff)

        check_in_data = {
            'ticket_number': self.registration.ticket_number
        }

        response = self.client.post('/api/tickets/check-in/', check_in_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_ticket_check_in(self):
        """Test checking in with invalid ticket number"""

        self.client.force_authenticate(user=self.staff)

        check_in_data = {
            'ticket_number': 'INVALID-TICKET-123'
        }

        response = self.client.post('/api/tickets/check-in/', check_in_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TicketRefundE2ETest(TestCase):
    """E2E tests for ticket refund system"""

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

        # Create event with ticket
        self.event = Event.objects.create(
            title='Test Event',
            slug='test-event',
            description='Test',
            organizer=self.organizer,
            venue_name='Test Venue',
            venue_address='123 Test St',
            city='Test City',
            country='USA',
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=32),
            capacity=100,
            status='published',
            privacy='public'
        )

        ticket_type = TicketType.objects.create(
            event=self.event,
            name='General',
            price=Decimal('50.00'),
            quantity=100
        )

        # Create completed order
        self.order = Order.objects.create(
            user=self.attendee,
            event=self.event,
            subtotal=Decimal('50.00'),
            tax=Decimal('4.00'),
            service_fee=Decimal('2.50'),
            total=Decimal('56.50'),
            status='completed',
            stripe_charge_id='ch_test_123'
        )

    def test_refund_request_creation(self):
        """Test creating a refund request"""

        self.client.force_authenticate(user=self.attendee)

        # Create refund
        refund = Refund.objects.create(
            order=self.order,
            user=self.attendee,
            amount=self.order.total,
            reason='Cannot attend event',
            status='pending'
        )

        # Verify refund created
        self.assertIsNotNone(refund)
        self.assertEqual(refund.status, 'pending')
        self.assertEqual(refund.amount, self.order.total)


class TicketTypeManagementE2ETest(TestCase):
    """E2E tests for managing ticket types"""

    def setUp(self):
        self.client = APIClient()

        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='TestPass123!',
            role='organizer'
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
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=32),
            capacity=500,
            status='published',
            privacy='public'
        )

    def test_ticket_availability_calculation(self):
        """Test ticket availability and quantity tracking"""

        ticket = TicketType.objects.create(
            event=self.event,
            name='Limited Ticket',
            price=Decimal('75.00'),
            quantity=10,
            quantity_sold=7,
            is_active=True
        )

        # Check availability
        self.assertTrue(ticket.is_available)
        self.assertEqual(ticket.quantity_remaining, 3)

        # Sell remaining tickets
        ticket.quantity_sold = 10
        ticket.save()

        self.assertFalse(ticket.is_available)
        self.assertEqual(ticket.quantity_remaining, 0)

    def test_inactive_tickets_not_shown(self):
        """Test that inactive tickets are not available for purchase"""

        # Create inactive ticket
        TicketType.objects.create(
            event=self.event,
            name='Inactive Ticket',
            price=Decimal('50.00'),
            quantity=100,
            is_active=False
        )

        # Try to get ticket types
        response = self.client.get(f'/api/events/{self.event.slug}/ticket_types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Inactive tickets should not be in response
        self.assertEqual(len(response.data), 0)
