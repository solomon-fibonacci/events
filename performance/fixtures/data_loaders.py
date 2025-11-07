"""
Utilities for generating large datasets for performance testing.

Provides efficient bulk creation methods for generating thousands of test records.
"""
from django.db import transaction
from .factories import (
    EventFactory, EventCategoryFactory, UserFactory, OrganizerFactory,
    TicketTypeFactory, OrderFactory, RegistrationFactory,
    EventCommentFactory, ReviewFactory, MenuFactory, MenuItemFactory
)


class DataLoader:
    """Utility class for bulk loading test data"""

    @staticmethod
    @transaction.atomic
    def create_events(count=1000, with_tickets=False, with_reviews=False):
        """
        Create a batch of events efficiently.

        Args:
            count: Number of events to create
            with_tickets: If True, create ticket types for each event
            with_reviews: If True, create reviews for each event

        Returns:
            List of created Event instances
        """
        print(f"Creating {count} events...")

        # Create categories first (reuse them)
        categories = [
            EventCategoryFactory(name=name, slug=name.lower().replace(' ', '-'))
            for name in ['Music', 'Sports', 'Technology', 'Food', 'Art', 'Business']
        ]

        # Create organizers (reuse them)
        organizers = OrganizerFactory.create_batch(min(50, count // 10))

        # Create events in batches
        events = []
        batch_size = 500
        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)
            batch_events = EventFactory.create_batch(
                batch_count,
                category=factory.Iterator(categories),
                organizer=factory.Iterator(organizers)
            )
            events.extend(batch_events)

            if i % 1000 == 0 and i > 0:
                print(f"  Created {i} events...")

        # Add related data if requested
        if with_tickets:
            print(f"Creating ticket types for {len(events)} events...")
            for event in events:
                TicketTypeFactory.create_batch(
                    3,  # 3 ticket types per event
                    event=event
                )

        if with_reviews:
            print(f"Creating reviews for {len(events)} events...")
            users = UserFactory.create_batch(min(100, count // 5))
            for event in events[:min(1000, count)]:  # Limit reviews to first 1000 events
                ReviewFactory.create_batch(
                    5,  # 5 reviews per event
                    event=event,
                    user=factory.Iterator(users)
                )

        print(f"Successfully created {len(events)} events")
        return events

    @staticmethod
    @transaction.atomic
    def create_registrations(event, count=100):
        """
        Create a batch of registrations for an event.

        Args:
            event: Event instance
            count: Number of registrations to create

        Returns:
            List of created Registration instances
        """
        print(f"Creating {count} registrations for event {event.slug}...")

        # Create ticket types if they don't exist
        ticket_types = list(event.ticket_types.all())
        if not ticket_types:
            ticket_types = TicketTypeFactory.create_batch(3, event=event)

        # Create users
        users = UserFactory.create_batch(min(count, 50))  # Reuse users

        # Create orders and registrations
        registrations = []
        batch_size = 100
        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)

            for _ in range(batch_count):
                order = OrderFactory(event=event, user=factory.Iterator(users))
                registration = RegistrationFactory(
                    order=order,
                    event=event,
                    user=order.user,
                    ticket_type=factory.Iterator(ticket_types)
                )
                registrations.append(registration)

            if i % 500 == 0 and i > 0:
                print(f"  Created {i} registrations...")

        print(f"Successfully created {len(registrations)} registrations")
        return registrations

    @staticmethod
    @transaction.atomic
    def create_nested_comments(event, depth=5, children_per_level=3):
        """
        Create a tree of nested comments for an event.

        Args:
            event: Event instance
            depth: Maximum depth of comment tree
            children_per_level: Number of replies per comment

        Returns:
            List of all created comments
        """
        print(f"Creating nested comments (depth={depth}, children={children_per_level})...")

        users = UserFactory.create_batch(10)
        comments = []

        def create_comment_tree(parent=None, current_depth=0):
            if current_depth >= depth:
                return

            for _ in range(children_per_level):
                comment = EventCommentFactory(
                    event=event,
                    user=factory.Iterator(users),
                    parent=parent
                )
                comments.append(comment)

                # Recursively create children
                create_comment_tree(parent=comment, current_depth=current_depth + 1)

        # Create root comments
        for _ in range(5):
            root_comment = EventCommentFactory(
                event=event,
                user=factory.Iterator(users),
                parent=None
            )
            comments.append(root_comment)
            create_comment_tree(parent=root_comment, current_depth=1)

        print(f"Successfully created {len(comments)} nested comments")
        return comments

    @staticmethod
    @transaction.atomic
    def create_large_menu(event, items_count=100):
        """
        Create a menu with many items for an event.

        Args:
            event: Event instance
            items_count: Number of menu items to create

        Returns:
            Menu instance with items
        """
        print(f"Creating menu with {items_count} items...")

        menu = MenuFactory(event=event)
        MenuItemFactory.create_batch(items_count, menu=menu)

        print(f"Successfully created menu with {items_count} items")
        return menu

    @staticmethod
    def clear_all():
        """
        Clear all test data from the database.
        WARNING: This deletes all data!
        """
        from events.models import Event, EventCategory
        from users.models import User
        from tickets.models import Order, Registration, TicketType
        from menus.models import Menu, MenuItem, FoodOrder
        from reviews.models import Review

        print("Clearing all test data...")
        Order.objects.all().delete()
        Registration.objects.all().delete()
        TicketType.objects.all().delete()
        FoodOrder.objects.all().delete()
        MenuItem.objects.all().delete()
        Menu.objects.all().delete()
        Review.objects.all().delete()
        Event.objects.all().delete()
        EventCategory.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        print("All test data cleared")


# Import factory after defining DataLoader to avoid circular imports
import factory
