"""
Locust Load Testing Configuration

Simulates realistic user behavior for load testing the Event Management API.

Usage:
    locust -f performance/locustfile.py --host=http://localhost:8000

    # Run with specific user count and spawn rate
    locust -f performance/locustfile.py --host=http://localhost:8000 \\
           --users=100 --spawn-rate=10

    # Run headless with specific duration
    locust -f performance/locustfile.py --host=http://localhost:8000 \\
           --users=100 --spawn-rate=10 --run-time=5m --headless
"""
from locust import HttpUser, task, between, SequentialTaskSet
import random
import json


class BrowsingBehavior(SequentialTaskSet):
    """
    Sequential task set simulating a user browsing events.
    Represents the most common user journey.
    """

    def on_start(self):
        """Initialize browsing session"""
        self.event_slugs = []

    @task
    def homepage_visit(self):
        """Visit homepage / event listing"""
        with self.client.get("/api/events/", name="Homepage - Event List") as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        # Store some event slugs for later viewing
                        self.event_slugs = [e['slug'] for e in data['results'][:5]]
                except:
                    pass

    @task
    def browse_categories(self):
        """Browse event categories"""
        self.client.get("/api/categories/", name="Browse Categories")

    @task
    def view_event_details(self):
        """View event details"""
        if self.event_slugs:
            slug = random.choice(self.event_slugs)
            with self.client.get(f"/api/events/{slug}/", name="Event Detail") as response:
                if response.status_code == 200:
                    # Check ticket types
                    self.client.get(
                        f"/api/events/{slug}/ticket_types/",
                        name="Event Ticket Types"
                    )

    @task
    def search_events(self):
        """Search for events"""
        search_terms = ['tech', 'music', 'food', 'sports', 'art']
        term = random.choice(search_terms)
        self.client.get(f"/api/events/?search={term}", name="Search Events")

    @task
    def filter_events_by_city(self):
        """Filter events by city"""
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston']
        city = random.choice(cities)
        self.client.get(f"/api/events/?city={city}", name="Filter by City")


class AttendeeUser(HttpUser):
    """
    Simulates an attendee browsing and potentially purchasing tickets.
    Weight: 70% of users (most common user type)
    """
    weight = 70
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Login as attendee"""
        # For load testing, you'd typically have a pool of pre-created users
        # Here we're simulating an already logged-in user
        self.token = None
        self.event_id = None

    @task(5)
    def browse_events(self):
        """Browse event listings (most common action)"""
        page = random.randint(1, 5)
        self.client.get(f"/api/events/?page={page}", name="Browse Events")

    @task(3)
    def view_event(self):
        """View event details"""
        # In a real scenario, you'd pick from known event slugs
        self.client.get("/api/events/", name="Get Event List for Viewing")

    @task(2)
    def search_events(self):
        """Search for events"""
        search_terms = ['conference', 'festival', 'workshop', 'concert']
        term = random.choice(search_terms)
        self.client.get(f"/api/events/?search={term}", name="Search Events")

    @task(1)
    def view_profile(self):
        """View user profile (requires auth)"""
        if self.token:
            headers = {'Authorization': f'Bearer {self.token}'}
            self.client.get("/api/users/profile/", headers=headers, name="View Profile")

    @task(1)
    def view_my_tickets(self):
        """View my tickets (requires auth)"""
        if self.token:
            headers = {'Authorization': f'Bearer {self.token}'}
            self.client.get("/api/tickets/my-tickets/", headers=headers, name="My Tickets")


class OrganizerUser(HttpUser):
    """
    Simulates an event organizer managing events.
    Weight: 20% of users
    """
    weight = 20
    wait_time = between(2, 8)

    def on_start(self):
        """Login as organizer"""
        self.token = None
        self.my_event_id = None

    @task(3)
    def view_my_events(self):
        """View my events"""
        if self.token:
            headers = {'Authorization': f'Bearer {self.token}'}
            self.client.get(
                "/api/events/?organizer=me",
                headers=headers,
                name="My Events"
            )

    @task(2)
    def view_event_analytics(self):
        """View event analytics"""
        if self.token and self.my_event_id:
            headers = {'Authorization': f'Bearer {self.token}'}
            self.client.get(
                f"/api/analytics/event/{self.my_event_id}/",
                headers=headers,
                name="Event Analytics"
            )

    @task(1)
    def browse_all_events(self):
        """Browse all events"""
        self.client.get("/api/events/", name="Browse All Events")


class CheckInStaff(HttpUser):
    """
    Simulates staff checking in attendees at event entrance.
    Weight: 10% of users (least common, but high-frequency when active)
    """
    weight = 10
    wait_time = between(0.5, 2)  # Fast actions - checking people in

    def on_start(self):
        """Login as staff"""
        self.token = None
        self.ticket_numbers = []

    @task(10)
    def check_in_ticket(self):
        """Check in a ticket (most common action for staff)"""
        if self.token and self.ticket_numbers:
            headers = {'Authorization': f'Bearer {self.token}'}
            ticket_number = random.choice(self.ticket_numbers)

            self.client.post(
                "/api/tickets/check-in/",
                json={"ticket_number": ticket_number},
                headers=headers,
                name="Check-in Ticket"
            )

    @task(1)
    def view_event_registrations(self):
        """View event registrations"""
        if self.token:
            headers = {'Authorization': f'Bearer {self.token}'}
            self.client.get(
                "/api/tickets/my-tickets/",
                headers=headers,
                name="View Registrations"
            )


class PeakLoadUser(HttpUser):
    """
    Simulates peak load scenario (e.g., ticket sale launch)
    Use this for stress testing specific scenarios.
    """
    weight = 0  # Set to 0 by default, enable for stress testing

    wait_time = between(0.1, 0.5)  # Very fast actions

    @task(10)
    def rapid_event_browsing(self):
        """Rapid event browsing during peak"""
        self.client.get("/api/events/", name="Peak - Event List")

    @task(5)
    def rapid_ticket_check(self):
        """Rapidly check ticket availability"""
        # Simulate checking ticket types for a popular event
        event_id = random.randint(1, 100)
        self.client.get(f"/api/events/{event_id}/ticket_types/", name="Peak - Ticket Check")


# Custom load shapes for specific scenarios
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    A load shape that increases users in steps.
    Useful for finding breaking points.

    Stages:
    - 0-60s: 10 users
    - 60-120s: 50 users
    - 120-180s: 100 users
    - 180-240s: 200 users
    - 240-300s: 500 users
    """

    step_time = 60
    step_load = 10
    spawn_rate = 10
    time_limit = 300

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = run_time // self.step_time
        user_count_steps = [10, 50, 100, 200, 500]

        if current_step < len(user_count_steps):
            return (user_count_steps[current_step], self.spawn_rate)
        else:
            return None


class SpikeLoadShape(LoadTestShape):
    """
    A load shape that simulates traffic spikes.
    Useful for testing autoscaling and recovery.

    Pattern: baseline → spike → baseline → spike
    """

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 60:
            # Baseline: 20 users
            return (20, 5)
        elif run_time < 120:
            # Spike: 200 users
            return (200, 20)
        elif run_time < 180:
            # Back to baseline: 20 users
            return (20, 10)
        elif run_time < 240:
            # Second spike: 300 users
            return (300, 30)
        elif run_time < 300:
            # Recovery: 20 users
            return (20, 10)
        else:
            return None


# Usage examples in comments:
"""
# Basic load test
locust -f performance/locustfile.py --host=http://localhost:8000

# Specific user count
locust -f performance/locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10

# Headless mode with reports
locust -f performance/locustfile.py --host=http://localhost:8000 \\
    --users=100 --spawn-rate=10 --run-time=5m --headless \\
    --html=reports/load_test_report.html

# Using step load shape
locust -f performance/locustfile.py --host=http://localhost:8000 \\
    --headless --step-load

# Distributed load testing (master)
locust -f performance/locustfile.py --host=http://localhost:8000 --master

# Distributed load testing (worker)
locust -f performance/locustfile.py --host=http://localhost:8000 --worker --master-host=<master-ip>
"""
