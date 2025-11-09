"""
Concurrency and Race Condition Tests

Tests thread-safety, atomic operations, and concurrent access patterns.
"""
import pytest
import threading
import time
from django.db import transaction
from django.db.models import F

from events.models import Event
from tickets.models import TicketType, Order, Registration
from performance.fixtures.factories import (
    EventFactory, TicketTypeFactory, UserFactory,
    OrderFactory, RegistrationFactory
)


class TestConcurrentViewCount:
    """Test concurrent view count increments"""

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_concurrent_view_count_updates(self):
        """Test that view count updates don't lose increments"""
        event = EventFactory(status='published', view_count=0)
        initial_count = event.view_count

        results = []
        errors = []

        def increment_view_count():
            try:
                # Simulate what happens when viewing an event
                Event.objects.filter(id=event.id).update(view_count=F('view_count') + 1)
                results.append('success')
            except Exception as e:
                errors.append(str(e))

        # Launch 100 concurrent view count increments
        threads = [threading.Thread(target=increment_view_count) for _ in range(100)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Refresh from database
        event.refresh_from_db()

        # All increments should be counted
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert event.view_count == initial_count + 100, \
            f"Expected {initial_count + 100} views, got {event.view_count}"
        print(f"✓ All 100 concurrent increments counted: {event.view_count}")

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_view_count_performance_under_load(self):
        """Test view count increment performance under high concurrency"""
        event = EventFactory(status='published', view_count=0)

        results = []

        def increment_with_timing():
            start = time.time()
            Event.objects.filter(id=event.id).update(view_count=F('view_count') + 1)
            elapsed = time.time() - start
            results.append(elapsed)

        # Launch 500 concurrent increments
        threads = [threading.Thread(target=increment_with_timing) for _ in range(500)]

        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_time = time.time() - start_time

        # Verify all increments
        event.refresh_from_db()
        assert event.view_count == 500

        avg_time = sum(results) / len(results)
        print(f"500 concurrent increments: avg={avg_time:.4f}s, total={total_time:.4f}s")

        # Each increment should be fast
        assert avg_time < 0.1, f"Average increment time too slow: {avg_time}s"


class TestTicketPurchaseConcurrency:
    """Test concurrent ticket purchases and overselling prevention"""

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_no_overselling_with_concurrent_purchases(self):
        """Ensure tickets are not oversold under concurrent purchases"""
        event = EventFactory(status='published')
        ticket_type = TicketTypeFactory(
            event=event,
            quantity=100,
            quantity_sold=0,
            price=50
        )

        successful_purchases = []
        failed_purchases = []
        errors = []

        def purchase_ticket():
            try:
                with transaction.atomic():
                    # Lock the ticket type row
                    tt = TicketType.objects.select_for_update().get(id=ticket_type.id)

                    # Check availability
                    if tt.quantity_remaining > 0:
                        # Increment sold count
                        tt.quantity_sold = F('quantity_sold') + 1
                        tt.save()

                        # Create order and registration
                        user = UserFactory()
                        order = OrderFactory(event=event, user=user, total=tt.price)
                        registration = RegistrationFactory(
                            event=event,
                            ticket_type=tt,
                            user=user,
                            order=order,
                            status='confirmed'
                        )

                        successful_purchases.append(registration.id)
                    else:
                        failed_purchases.append('sold_out')

            except Exception as e:
                errors.append(str(e))

        # Launch 200 concurrent purchase attempts for 100 tickets
        threads = [threading.Thread(target=purchase_ticket) for _ in range(200)]

        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.time() - start_time

        # Verify results
        ticket_type.refresh_from_db()

        print(f"Concurrent purchases: {len(successful_purchases)} succeeded, "
              f"{len(failed_purchases)} sold out, {len(errors)} errors")
        print(f"Final quantity_sold: {ticket_type.quantity_sold}")
        print(f"Total time: {elapsed:.2f}s")

        # Verify no overselling
        assert ticket_type.quantity_sold == 100, \
            f"Expected exactly 100 sold, got {ticket_type.quantity_sold}"
        assert len(successful_purchases) == 100, \
            f"Expected 100 successful purchases, got {len(successful_purchases)}"
        assert len(failed_purchases) == 100, \
            f"Expected 100 failed purchases, got {len(failed_purchases)}"
        assert len(errors) == 0, f"No errors should occur: {errors[:5]}"

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_ticket_purchase_atomicity(self):
        """Test that ticket purchases are atomic (all or nothing)"""
        event = EventFactory(status='published')
        ticket_type = TicketTypeFactory(
            event=event,
            quantity=50,
            quantity_sold=0
        )

        successful_orders = []
        failed_orders = []

        def purchase_multiple_tickets(quantity):
            try:
                with transaction.atomic():
                    tt = TicketType.objects.select_for_update().get(id=ticket_type.id)

                    if tt.quantity_remaining >= quantity:
                        user = UserFactory()
                        order = OrderFactory(event=event, user=user)

                        # Create multiple registrations
                        for _ in range(quantity):
                            RegistrationFactory(
                                event=event,
                                ticket_type=tt,
                                user=user,
                                order=order
                            )

                        # Update sold count
                        tt.quantity_sold = F('quantity_sold') + quantity
                        tt.save()

                        successful_orders.append(order.id)
                    else:
                        failed_orders.append('insufficient')

            except Exception as e:
                failed_orders.append(str(e))

        # Try to purchase in batches: 10 threads trying to buy 5 tickets each
        threads = [threading.Thread(target=purchase_multiple_tickets, args=(5,))
                   for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        ticket_type.refresh_from_db()

        # Exactly 10 batches of 5 should succeed
        assert ticket_type.quantity_sold == 50
        assert len(successful_orders) == 10
        print(f"✓ All {len(successful_orders)} multi-ticket purchases were atomic")


class TestCheckInConcurrency:
    """Test concurrent ticket check-ins"""

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_no_duplicate_checkins(self):
        """Ensure a ticket can only be checked in once"""
        event = EventFactory(status='published')
        ticket_type = TicketTypeFactory(event=event)
        user = UserFactory()
        order = OrderFactory(event=event, user=user)

        registration = RegistrationFactory(
            event=event,
            ticket_type=ticket_type,
            user=user,
            order=order,
            status='confirmed'
        )

        successful_checkins = []
        failed_checkins = []

        def checkin_ticket():
            try:
                with transaction.atomic():
                    reg = Registration.objects.select_for_update().get(id=registration.id)

                    if reg.status == 'confirmed':
                        reg.status = 'checked_in'
                        reg.checked_in_at = time.time()
                        reg.save()
                        successful_checkins.append('success')
                    else:
                        failed_checkins.append('already_checked_in')

            except Exception as e:
                failed_checkins.append(str(e))

        # Try to check in the same ticket 100 times concurrently
        threads = [threading.Thread(target=checkin_ticket) for _ in range(100)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        registration.refresh_from_db()

        # Only one check-in should succeed
        assert len(successful_checkins) == 1, \
            f"Expected 1 successful check-in, got {len(successful_checkins)}"
        assert len(failed_checkins) == 99, \
            f"Expected 99 failed check-ins, got {len(failed_checkins)}"
        assert registration.status == 'checked_in'
        print(f"✓ Prevented duplicate check-ins: 1 success, 99 blocked")

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_mass_checkin_performance(self):
        """Test check-in performance with many simultaneous check-ins"""
        event = EventFactory(status='published')
        ticket_type = TicketTypeFactory(event=event)

        # Create 100 registrations
        registrations = []
        for _ in range(100):
            user = UserFactory()
            order = OrderFactory(event=event, user=user)
            reg = RegistrationFactory(
                event=event,
                ticket_type=ticket_type,
                user=user,
                order=order,
                status='confirmed'
            )
            registrations.append(reg)

        results = []

        def checkin_ticket(reg_id):
            start = time.time()
            try:
                with transaction.atomic():
                    reg = Registration.objects.select_for_update().get(id=reg_id)
                    if reg.status == 'confirmed':
                        reg.status = 'checked_in'
                        reg.save()
                elapsed = time.time() - start
                results.append(elapsed)
            except Exception as e:
                print(f"Error: {e}")

        # Check in all 100 tickets concurrently
        threads = [threading.Thread(target=checkin_ticket, args=(reg.id,))
                   for reg in registrations]

        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_time = time.time() - start_time

        # Verify all checked in
        checked_in_count = Registration.objects.filter(
            event=event, status='checked_in'
        ).count()

        assert checked_in_count == 100

        avg_time = sum(results) / len(results) if results else 0
        throughput = 100 / total_time if total_time > 0 else 0

        print(f"Mass check-in: {checked_in_count} tickets in {total_time:.2f}s")
        print(f"Throughput: {throughput:.1f} check-ins/second")
        print(f"Avg time per check-in: {avg_time:.4f}s")

        # Should handle at least 100 check-ins per minute
        assert throughput > 1.67, f"Throughput too low: {throughput:.2f}/s"


class TestConcurrentEventCreation:
    """Test concurrent event creation"""

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_concurrent_event_creation(self):
        """Test creating multiple events concurrently"""
        from events.models import EventCategory

        category = EventCategory.objects.create(name='Test', slug='test')
        organizers = [OrganizerFactory() for _ in range(10)]

        created_events = []
        errors = []

        def create_event(organizer, index):
            try:
                event = EventFactory(
                    title=f'Concurrent Event {index}',
                    slug=f'concurrent-event-{index}-{time.time()}',
                    organizer=organizer,
                    category=category,
                    status='published'
                )
                created_events.append(event.id)
            except Exception as e:
                errors.append(str(e))

        # Create 50 events concurrently
        threads = [
            threading.Thread(target=create_event, args=(organizers[i % 10], i))
            for i in range(50)
        ]

        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.time() - start_time

        print(f"Created {len(created_events)} events in {elapsed:.2f}s")
        print(f"Errors: {len(errors)}")

        assert len(created_events) == 50
        assert len(errors) == 0


class TestDatabaseDeadlocks:
    """Test for potential database deadlock scenarios"""

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_no_deadlock_on_order_creation(self):
        """Test that concurrent order creation doesn't cause deadlocks"""
        event = EventFactory(status='published')
        ticket_types = TicketTypeFactory.create_batch(5, event=event, quantity=100)
        users = UserFactory.create_batch(10)

        successful_orders = []
        errors = []

        def create_order(user, tt_index):
            try:
                with transaction.atomic():
                    # Lock ticket type
                    tt = TicketType.objects.select_for_update().get(
                        id=ticket_types[tt_index].id
                    )

                    if tt.quantity_remaining > 0:
                        order = OrderFactory(event=event, user=user)
                        RegistrationFactory(
                            event=event,
                            ticket_type=tt,
                            user=user,
                            order=order
                        )

                        tt.quantity_sold = F('quantity_sold') + 1
                        tt.save()

                        successful_orders.append(order.id)

            except Exception as e:
                error_msg = str(e)
                if 'deadlock' in error_msg.lower():
                    errors.append(f"DEADLOCK: {error_msg}")
                else:
                    errors.append(error_msg)

        # Create 100 concurrent orders across different ticket types
        threads = [
            threading.Thread(
                target=create_order,
                args=(users[i % 10], i % 5)
            )
            for i in range(100)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print(f"Successful orders: {len(successful_orders)}")
        print(f"Errors: {len(errors)}")

        # Check for deadlocks
        deadlocks = [e for e in errors if 'DEADLOCK' in e]
        assert len(deadlocks) == 0, f"Deadlocks detected: {deadlocks}"


class TestRaceConditionMitigation:
    """Test race condition mitigation strategies"""

    @pytest.mark.concurrency
    @pytest.mark.django_db(transaction=True)
    def test_select_for_update_prevents_race(self):
        """Test that select_for_update prevents race conditions"""
        event = EventFactory(status='published', view_count=0)

        race_detected = []

        def check_and_update_without_lock():
            """Simulates a race condition WITHOUT proper locking"""
            try:
                # Read current value
                e = Event.objects.get(id=event.id)
                current_count = e.view_count

                # Simulate some processing
                time.sleep(0.001)

                # Update based on read value (RACE CONDITION)
                e.view_count = current_count + 1
                e.save()

            except Exception as e:
                race_detected.append(str(e))

        def check_and_update_with_lock():
            """Proper implementation WITH locking"""
            try:
                with transaction.atomic():
                    # Lock the row
                    e = Event.objects.select_for_update().get(id=event.id)
                    current_count = e.view_count

                    # Simulate some processing
                    time.sleep(0.001)

                    # Update (SAFE - row is locked)
                    e.view_count = current_count + 1
                    e.save()

            except Exception as ex:
                race_detected.append(str(ex))

        # Test WITH locking (should work correctly)
        threads = [threading.Thread(target=check_and_update_with_lock)
                   for _ in range(50)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        event.refresh_from_db()

        # With proper locking, all 50 increments should be counted
        assert event.view_count == 50, \
            f"Expected 50, got {event.view_count} (race condition detected!)"
        print(f"✓ select_for_update prevented race condition: {event.view_count}/50")


# Import OrganizerFactory at the end to avoid circular imports
from performance.fixtures.factories import OrganizerFactory
