"""
Model factories for generating test data at scale.

Uses factory_boy for creating realistic test data for performance testing.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from events.models import Event, EventCategory, EventFavorite, EventComment
from tickets.models import TicketType, Order, Registration
from menus.models import Menu, MenuItem, FoodOrder, FoodOrderItem
from reviews.models import Review

fake = Faker()
User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances"""
    class Meta:
        model = User
        django_get_or_create = ('email',)

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    role = 'attendee'
    is_email_verified = True
    is_active = True


class OrganizerFactory(UserFactory):
    """Factory for creating Organizer users"""
    role = 'organizer'


class VendorFactory(UserFactory):
    """Factory for creating Vendor users"""
    role = 'vendor'


class EventCategoryFactory(DjangoModelFactory):
    """Factory for creating EventCategory instances"""
    class Meta:
        model = EventCategory
        django_get_or_create = ('slug',)

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    description = factory.Faker('sentence')


class EventFactory(DjangoModelFactory):
    """Factory for creating Event instances"""
    class Meta:
        model = Event

    title = factory.Faker('sentence', nb_words=5)
    slug = factory.Sequence(lambda n: f'event-{n}-{fake.slug()}')
    description = factory.Faker('paragraph', nb_sentences=10)
    organizer = factory.SubFactory(OrganizerFactory)
    category = factory.SubFactory(EventCategoryFactory)
    venue_name = factory.Faker('company')
    venue_address = factory.Faker('street_address')
    city = factory.Faker('city')
    state = factory.Faker('state')
    country = 'United States'
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')
    start_date = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=fake.random_int(min=1, max=30))
    )
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timedelta(hours=fake.random_int(min=2, max=8))
    )
    capacity = factory.Faker('random_int', min=50, max=1000)
    status = 'published'
    privacy = 'public'
    view_count = factory.Faker('random_int', min=0, max=10000)


class DraftEventFactory(EventFactory):
    """Factory for creating draft Event instances"""
    status = 'draft'


class PrivateEventFactory(EventFactory):
    """Factory for creating private Event instances"""
    privacy = 'private'


class TicketTypeFactory(DjangoModelFactory):
    """Factory for creating TicketType instances"""
    class Meta:
        model = TicketType

    event = factory.SubFactory(EventFactory)
    name = factory.Iterator(['General Admission', 'VIP', 'Early Bird', 'Student', 'Group'])
    description = factory.Faker('sentence')
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True, min_value=10, max_value=500)
    quantity = factory.Faker('random_int', min=50, max=500)
    quantity_sold = 0
    is_active = True
    sale_start_date = factory.LazyAttribute(lambda obj: obj.event.start_date - timedelta(days=30))
    sale_end_date = factory.LazyAttribute(lambda obj: obj.event.start_date - timedelta(hours=1))


class OrderFactory(DjangoModelFactory):
    """Factory for creating Order instances"""
    class Meta:
        model = Order

    order_number = factory.Sequence(lambda n: f'ORD-{n:08d}')
    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)
    status = 'completed'
    subtotal = factory.Faker(
        'pydecimal', left_digits=3, right_digits=2,
        positive=True, min_value=50, max_value=1000
    )
    tax = factory.LazyAttribute(lambda obj: obj.subtotal * factory.Faker(
        'pydecimal', left_digits=0, right_digits=2,
        positive=True, min_value=0.05, max_value=0.10
    ).generate({}))
    service_fee = factory.LazyAttribute(lambda obj: obj.subtotal * factory.Faker(
        'pydecimal', left_digits=0, right_digits=2,
        positive=True, min_value=0.02, max_value=0.05
    ).generate({}))
    total = factory.LazyAttribute(lambda obj: obj.subtotal + obj.tax + obj.service_fee)
    stripe_payment_intent_id = factory.Sequence(lambda n: f'pi_test_{n}')
    paid_at = factory.LazyFunction(timezone.now)


class RegistrationFactory(DjangoModelFactory):
    """Factory for creating Registration instances"""
    class Meta:
        model = Registration

    ticket_number = factory.Sequence(lambda n: f'TKT-{n:08d}')
    order = factory.SubFactory(OrderFactory)
    event = factory.LazyAttribute(lambda obj: obj.order.event)
    user = factory.LazyAttribute(lambda obj: obj.order.user)
    ticket_type = factory.SubFactory(TicketTypeFactory)
    status = 'confirmed'
    qr_code_data = factory.LazyAttribute(lambda obj: f'qr-{obj.ticket_number}')


class EventCommentFactory(DjangoModelFactory):
    """Factory for creating EventComment instances"""
    class Meta:
        model = EventComment

    event = factory.SubFactory(EventFactory)
    user = factory.SubFactory(UserFactory)
    content = factory.Faker('paragraph', nb_sentences=3)
    parent = None


class NestedCommentFactory(EventCommentFactory):
    """Factory for creating nested comment replies"""
    parent = factory.SubFactory(EventCommentFactory)


class EventFavoriteFactory(DjangoModelFactory):
    """Factory for creating EventFavorite instances"""
    class Meta:
        model = EventFavorite

    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)


class ReviewFactory(DjangoModelFactory):
    """Factory for creating Review instances"""
    class Meta:
        model = Review

    event = factory.SubFactory(EventFactory)
    user = factory.SubFactory(UserFactory)
    rating = factory.Faker('random_int', min=1, max=5)
    title = factory.Faker('sentence', nb_words=6)
    content = factory.Faker('paragraph', nb_sentences=5)
    is_moderated = True
    is_approved = True


class MenuFactory(DjangoModelFactory):
    """Factory for creating Menu instances"""
    class Meta:
        model = Menu

    event = factory.SubFactory(EventFactory)
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('sentence')
    is_active = True
    vendor = factory.SubFactory(VendorFactory)


class MenuItemFactory(DjangoModelFactory):
    """Factory for creating MenuItem instances"""
    class Meta:
        model = MenuItem

    menu = factory.SubFactory(MenuFactory)
    name = factory.Faker('word')
    description = factory.Faker('sentence')
    price = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True, min_value=5, max_value=50)
    dietary_type = factory.Iterator(['vegetarian', 'vegan', 'gluten_free', 'none'])
    is_available = True
    stock_quantity = factory.Faker('random_int', min=50, max=500)
    display_order = factory.Sequence(lambda n: n)


class FoodOrderFactory(DjangoModelFactory):
    """Factory for creating FoodOrder instances"""
    class Meta:
        model = FoodOrder

    order_number = factory.Sequence(lambda n: f'FOOD-{n:08d}')
    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)
    status = 'confirmed'
    subtotal = factory.Faker(
        'pydecimal', left_digits=2, right_digits=2,
        positive=True, min_value=20, max_value=200
    )
    tax = factory.LazyAttribute(lambda obj: obj.subtotal * factory.Faker(
        'pydecimal', left_digits=0, right_digits=2,
        positive=True, min_value=0.05, max_value=0.10
    ).generate({}))
    service_fee = factory.LazyAttribute(lambda obj: obj.subtotal * factory.Faker(
        'pydecimal', left_digits=0, right_digits=2,
        positive=True, min_value=0.02, max_value=0.05
    ).generate({}))
    total = factory.LazyAttribute(lambda obj: obj.subtotal + obj.tax + obj.service_fee)
    stripe_payment_intent_id = factory.Sequence(lambda n: f'pi_food_test_{n}')
    paid_at = factory.LazyFunction(timezone.now)


class FoodOrderItemFactory(DjangoModelFactory):
    """Factory for creating FoodOrderItem instances"""
    class Meta:
        model = FoodOrderItem

    food_order = factory.SubFactory(FoodOrderFactory)
    menu_item = factory.SubFactory(MenuItemFactory)
    quantity = factory.Faker('random_int', min=1, max=5)
    unit_price = factory.LazyAttribute(lambda obj: obj.menu_item.price)
    total_price = factory.LazyAttribute(lambda obj: obj.unit_price * obj.quantity)
