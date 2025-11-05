"""
Centralized API Views for Event Management System
This file contains all the main API endpoints for the system
"""
from rest_framework import viewsets, generics, status, views, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from decimal import Decimal

# Import models
from events.models import Event, EventCategory, EventFavorite, EventComment
from tickets.models import TicketType, Order, Registration, Refund
from menus.models import Menu, MenuItem, MenuCategory, FoodOrder, FoodOrderItem
from reviews.models import Review

# Import serializers
from events.serializers import (
    EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer,
    EventCategorySerializer, EventFavoriteSerializer, EventCommentSerializer
)
from tickets.serializers import (
    TicketTypeSerializer, OrderSerializer, OrderCreateSerializer,
    RegistrationSerializer, CheckInSerializer, RefundSerializer, RefundCreateSerializer
)
from menus.serializers import (
    MenuSerializer, MenuItemSerializer, MenuCategorySerializer,
    FoodOrderSerializer, FoodOrderCreateSerializer
)
from reviews.serializers import ReviewSerializer, ReviewCreateUpdateSerializer

# Import utilities
from event_management.utils.stripe_service import StripeService
from event_management.utils.qr_service import QRCodeService
from event_management.utils.email_service import EmailService
from event_management.permissions import IsEventOrganizer, IsOrganizerOrReadOnly, IsOwnerOrReadOnly


class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for Event CRUD operations"""
    queryset = Event.objects.all().select_related('organizer', 'category')
    permission_classes = [IsOrganizerOrReadOnly, IsEventOrganizer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'privacy', 'category', 'city', 'country']
    search_fields = ['title', 'description', 'venue_name', 'city', 'tags']
    ordering_fields = ['start_date', 'created_at', 'view_count']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        return EventDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by status and privacy for non-organizers
        if not self.request.user.is_authenticated or self.request.user.role != 'organizer':
            queryset = queryset.filter(status='published', privacy='public')
        return queryset

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, slug=None):
        """Favorite/Unfavorite an event"""
        event = self.get_object()
        favorite, created = EventFavorite.objects.get_or_create(user=request.user, event=event)
        if not created:
            favorite.delete()
            return Response({'message': 'Event removed from favorites'})
        return Response({'message': 'Event added to favorites'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def ticket_types(self, request, slug=None):
        """Get ticket types for an event"""
        event = self.get_object()
        ticket_types = TicketType.objects.filter(event=event, is_active=True)
        serializer = TicketTypeSerializer(ticket_types, many=True)
        return Response(serializer.data)


class EventCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Event Categories"""
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    permission_classes = [AllowAny]


class EventCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for Event Comments"""
    queryset = EventComment.objects.all()
    serializer_class = EventCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketOrderView(views.APIView):
    """Create ticket orders and process payments"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_id = serializer.validated_data['event_id']
            tickets = serializer.validated_data['tickets']

            event = Event.objects.get(id=event_id)

            # Calculate totals
            subtotal = Decimal('0.00')
            ticket_items = []

            for ticket in tickets:
                ticket_type = TicketType.objects.get(id=ticket['ticket_type_id'])
                quantity = ticket['quantity']

                # Check availability
                if ticket_type.quantity_remaining < quantity:
                    return Response({
                        'error': f'Not enough tickets available for {ticket_type.name}'
                    }, status=status.HTTP_400_BAD_REQUEST)

                subtotal += ticket_type.price * quantity
                ticket_items.append({
                    'ticket_type': ticket_type,
                    'quantity': quantity
                })

            # Calculate fees
            tax = subtotal * Decimal('0.08')  # 8% tax
            service_fee = subtotal * Decimal('0.05')  # 5% service fee
            total = subtotal + tax + service_fee

            # Create Stripe Payment Intent
            payment_intent = StripeService.create_payment_intent(
                amount=float(total),
                metadata={
                    'event_id': event.id,
                    'user_id': request.user.id,
                    'order_type': 'ticket'
                }
            )

            # Create Order
            order = Order.objects.create(
                user=request.user,
                event=event,
                subtotal=subtotal,
                tax=tax,
                service_fee=service_fee,
                total=total,
                stripe_payment_intent_id=payment_intent['id'],
                status='pending'
            )

            # Create Registrations
            for item in ticket_items:
                ticket_type = item['ticket_type']
                for _ in range(item['quantity']):
                    registration = Registration.objects.create(
                        order=order,
                        event=event,
                        user=request.user,
                        ticket_type=ticket_type,
                        status='pending'
                    )

                    # Generate QR code
                    qr_file = QRCodeService.generate_ticket_qr_code(registration)
                    registration.qr_code.save(qr_file.name, qr_file, save=True)

                # Update ticket type quantity sold
                ticket_type.quantity_sold += item['quantity']
                ticket_type.save()

            return Response({
                'order': OrderSerializer(order).data,
                'client_secret': payment_intent['client_secret']
            }, status=status.HTTP_201_CREATED)

        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        except TicketType.DoesNotExist:
            return Response({'error': 'Ticket type not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyTicketsView(generics.ListAPIView):
    """Get user's tickets"""
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user).select_related('event', 'ticket_type')


class CheckInView(views.APIView):
    """Check-in a ticket using QR code"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ticket_number = serializer.validated_data['ticket_number']

        try:
            registration = Registration.objects.get(ticket_number=ticket_number)

            if registration.status == 'checked_in':
                return Response({'error': 'Ticket already checked in'}, status=status.HTTP_400_BAD_REQUEST)

            registration.status = 'checked_in'
            registration.checked_in_at = timezone.now()
            registration.checked_in_by = request.user
            registration.save()

            return Response({
                'message': 'Check-in successful',
                'registration': RegistrationSerializer(registration).data
            })

        except Registration.DoesNotExist:
            return Response({'error': 'Invalid ticket number'}, status=status.HTTP_404_NOT_FOUND)


class MenuViewSet(viewsets.ModelViewSet):
    """ViewSet for Menu management"""
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event', 'is_active']


class FoodOrderView(views.APIView):
    """Create food orders and process payments"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FoodOrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_id = serializer.validated_data['event_id']
            items = serializer.validated_data['items']
            notes = serializer.validated_data.get('notes', '')
            table_number = serializer.validated_data.get('table_number', '')

            event = Event.objects.get(id=event_id)

            # Calculate totals
            subtotal = Decimal('0.00')
            order_items = []

            for item in items:
                menu_item = MenuItem.objects.get(id=item['menu_item_id'])
                quantity = item['quantity']

                # Check availability
                if not menu_item.is_available or not menu_item.in_stock:
                    return Response({
                        'error': f'{menu_item.name} is not available'
                    }, status=status.HTTP_400_BAD_REQUEST)

                subtotal += menu_item.price * quantity
                order_items.append({
                    'menu_item': menu_item,
                    'quantity': quantity,
                    'special_instructions': item.get('special_instructions', '')
                })

            # Calculate fees
            tax = subtotal * Decimal('0.08')
            service_fee = subtotal * Decimal('0.03')
            total = subtotal + tax + service_fee

            # Create Stripe Payment Intent
            payment_intent = StripeService.create_payment_intent(
                amount=float(total),
                metadata={
                    'event_id': event.id,
                    'user_id': request.user.id,
                    'order_type': 'food'
                }
            )

            # Create Food Order
            food_order = FoodOrder.objects.create(
                user=request.user,
                event=event,
                subtotal=subtotal,
                tax=tax,
                service_fee=service_fee,
                total=total,
                stripe_payment_intent_id=payment_intent['id'],
                notes=notes,
                table_number=table_number,
                status='pending'
            )

            # Create Food Order Items
            for item in order_items:
                FoodOrderItem.objects.create(
                    food_order=food_order,
                    menu_item=item['menu_item'],
                    quantity=item['quantity'],
                    unit_price=item['menu_item'].price,
                    special_instructions=item['special_instructions']
                )

            # Send confirmation email
            try:
                EmailService.send_food_order_confirmation(request.user, food_order)
            except:
                pass

            return Response({
                'order': FoodOrderSerializer(food_order).data,
                'client_secret': payment_intent['client_secret']
            }, status=status.HTTP_201_CREATED)

        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        except MenuItem.DoesNotExist:
            return Response({'error': 'Menu item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Reviews"""
    queryset = Review.objects.filter(is_approved=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event', 'rating']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReviewCreateUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EventAnalyticsView(views.APIView):
    """Analytics endpoint for event organizers"""
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)

            # Check if user is the organizer
            if event.organizer != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

            # Calculate analytics
            total_registrations = Registration.objects.filter(event=event).count()
            checked_in = Registration.objects.filter(event=event, status='checked_in').count()
            total_revenue = Order.objects.filter(event=event, status='completed').aggregate(
                total=Sum('total')
            )['total'] or 0

            reviews = Review.objects.filter(event=event, is_approved=True)
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

            return Response({
                'event': EventDetailSerializer(event).data,
                'analytics': {
                    'total_registrations': total_registrations,
                    'checked_in': checked_in,
                    'attendance_rate': (checked_in / total_registrations * 100) if total_registrations > 0 else 0,
                    'total_revenue': float(total_revenue),
                    'average_rating': float(avg_rating),
                    'total_reviews': reviews.count(),
                }
            })

        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
