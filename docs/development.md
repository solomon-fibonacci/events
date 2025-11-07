# Development Guide

This guide covers development workflows, coding standards, and best practices for contributing to the Event Management System.

## Development Environment Setup

See the [Installation Guide](installation.md) for initial setup instructions.

### Required Tools
- Python 3.10+
- Git
- Code editor (VS Code, PyCharm, etc.)
- PostgreSQL (optional, for production-like development)
- Stripe CLI (optional, for webhook testing)

### Recommended VS Code Extensions
- Python
- Pylance
- Django
- GitLens
- REST Client
- Python Test Explorer

## Project Structure

```
event_management/
├── event_management/      # Core Django project
│   ├── settings.py       # Configuration
│   ├── urls.py           # Main URL routing
│   ├── api_views.py      # Centralized API views
│   ├── permissions.py    # Custom permissions
│   └── utils/            # Service layer
│       ├── stripe_service.py
│       ├── email_service.py
│       └── qr_service.py
├── users/                # User management app
│   ├── models.py         # User, Follow models
│   ├── serializers.py    # User serializers
│   ├── views.py          # User views
│   ├── urls.py           # User routes
│   ├── admin.py          # Admin configuration
│   └── test_*.py         # Tests
├── events/               # Event management app
│   ├── models.py         # Event, Category, Comment models
│   ├── serializers.py    # Event serializers
│   ├── views.py          # Event views
│   ├── admin.py          # Admin configuration
│   └── test_*.py         # Tests
├── tickets/              # Ticketing system app
├── menus/                # Food ordering app
├── reviews/              # Reviews app
├── notifications/        # Notifications app
├── tests/                # Integration tests
├── media/                # User uploads
├── static/               # Static files
├── docs/                 # Documentation
├── manage.py             # Django management
├── requirements.txt      # Dependencies
├── pytest.ini            # Pytest configuration
└── .env                  # Environment variables
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Test additions/updates

### 2. Make Your Changes

Follow the coding standards below and write tests for your changes.

### 3. Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### 4. Check Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Security checks
bandit -r .
safety check
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add user profile picture upload"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/updates
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `perf:` - Performance improvements
- `chore:` - Build/config changes

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# Good: Clear, descriptive names
def create_event_with_tickets(event_data, ticket_types):
    """
    Creates an event along with its ticket types.

    Args:
        event_data: Dictionary containing event information
        ticket_types: List of ticket type dictionaries

    Returns:
        Event: The created event instance

    Raises:
        ValidationError: If event data is invalid
    """
    event = Event.objects.create(**event_data)
    for ticket_type in ticket_types:
        TicketType.objects.create(event=event, **ticket_type)
    return event

# Bad: Unclear, abbreviated names
def cre_evt(d, t):
    e = Event.objects.create(**d)
    for x in t:
        TicketType.objects.create(event=e, **x)
    return e
```

### Code Formatting

#### Black Configuration
```python
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
```

#### isort Configuration
```python
# .isort.cfg
[settings]
profile = black
line_length = 100
multi_line_output = 3
include_trailing_comma = True
```

### Django Best Practices

#### Models
```python
# Good: Clear model with proper validation
class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError('End time must be after start time')
```

#### Serializers
```python
# Good: Comprehensive serializer with validation
class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    ticket_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'organizer', 'category',
            'start_datetime', 'end_datetime', 'ticket_count'
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_ticket_count(self, obj):
        return obj.ticket_types.count()

    def validate(self, data):
        if data['start_datetime'] >= data['end_datetime']:
            raise serializers.ValidationError(
                'End time must be after start time'
            )
        return data
```

#### Views
```python
# Good: Clear, focused view with proper permissions
class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing events.

    Permissions:
    - List/Retrieve: Anyone
    - Create: Organizers only
    - Update/Delete: Owner only
    """
    queryset = Event.objects.select_related('organizer', 'category')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'slug'

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by status for non-organizers
        if not self.request.user.is_authenticated or \
           self.request.user.role != 'organizer':
            queryset = queryset.filter(status='published')
        return queryset
```

### API Design Best Practices

#### 1. Use Proper HTTP Methods
```python
# GET - Retrieve resources
GET /api/events/

# POST - Create resources
POST /api/events/

# PUT - Full update
PUT /api/events/{slug}/

# PATCH - Partial update
PATCH /api/events/{slug}/

# DELETE - Remove resources
DELETE /api/events/{slug}/
```

#### 2. Return Appropriate Status Codes
```python
# 200 OK - Successful GET, PUT, PATCH
# 201 Created - Successful POST
# 204 No Content - Successful DELETE
# 400 Bad Request - Validation errors
# 401 Unauthorized - Authentication required
# 403 Forbidden - Permission denied
# 404 Not Found - Resource doesn't exist
# 500 Internal Server Error - Server error
```

#### 3. Consistent Error Format
```python
# Validation errors
{
    "field_name": ["Error message 1", "Error message 2"]
}

# General errors
{
    "detail": "Error message",
    "code": "error_code"
}
```

## Testing Guidelines

### Test Structure

```python
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User
from events.models import Event

class EventAPITest(APITestCase):
    """
    End-to-end tests for Event API endpoints.
    """

    def setUp(self):
        """Set up test data before each test."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!',
            role='organizer'
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        """Clean up after each test."""
        pass

    def test_create_event_success(self):
        """Test successful event creation."""
        data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'start_datetime': '2024-12-01T10:00:00Z',
            'end_datetime': '2024-12-01T18:00:00Z',
            'location_city': 'San Francisco',
            'capacity': 100
        }
        response = self.client.post('/api/events/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Event')
        self.assertEqual(Event.objects.count(), 1)

    def test_create_event_validation_error(self):
        """Test event creation with invalid data."""
        data = {
            'title': '',  # Empty title should fail
        }
        response = self.client.post('/api/events/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
```

### Test Coverage Goals
- Overall: 80%+
- Critical paths (auth, payments): 95%+
- Models: 90%+
- API endpoints: 85%+

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

class TicketPurchaseTest(APITestCase):
    @patch('event_management.utils.stripe_service.stripe.PaymentIntent.create')
    @patch('event_management.utils.email_service.send_email')
    def test_ticket_purchase_flow(self, mock_email, mock_stripe):
        """Test complete ticket purchase flow."""
        # Mock Stripe response
        mock_stripe.return_value = MagicMock(
            id='pi_test_123',
            client_secret='secret_test_123',
            status='succeeded'
        )

        # Mock email sending
        mock_email.return_value = True

        # Test ticket purchase
        data = {
            'event_id': self.event.id,
            'ticket_type_id': self.ticket_type.id,
            'quantity': 2
        }
        response = self.client.post('/api/tickets/order/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_stripe.assert_called_once()
        mock_email.assert_called_once()
```

## Database Migrations

### Creating Migrations

```bash
# Create migrations for all apps
python manage.py makemigrations

# Create migration for specific app
python manage.py makemigrations users

# Create empty migration (for data migrations)
python manage.py makemigrations --empty users
```

### Applying Migrations

```bash
# Apply all migrations
python manage.py migrate

# Apply specific migration
python manage.py migrate users 0001

# Rollback migration
python manage.py migrate users 0000
```

### Migration Best Practices

1. **Review migrations before committing**
2. **Never edit applied migrations**
3. **Use data migrations for complex changes**
4. **Test migrations on copy of production data**
5. **Always backup database before major migrations**

## Debugging

### Django Debug Toolbar

```python
# Install
pip install django-debug-toolbar

# Add to settings.py (development only)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### Django Shell

```bash
# Open Django shell
python manage.py shell

# Or use iPython
pip install ipython
python manage.py shell
```

```python
# Example debugging session
from users.models import User
from events.models import Event

# Get all users
users = User.objects.all()

# Debug query
print(Event.objects.filter(status='published').query)

# Test serializer
from events.serializers import EventSerializer
event = Event.objects.first()
serializer = EventSerializer(event)
print(serializer.data)
```

### Logging

```python
# Add to views or services
import logging

logger = logging.getLogger(__name__)

def my_view(request):
    logger.debug('Debug message')
    logger.info('Info message')
    logger.warning('Warning message')
    logger.error('Error message')
    logger.critical('Critical message')
```

## Performance Optimization

### Query Optimization

```python
# Bad: N+1 query problem
events = Event.objects.all()
for event in events:
    print(event.organizer.username)  # Hits DB for each event

# Good: Use select_related
events = Event.objects.select_related('organizer').all()
for event in events:
    print(event.organizer.username)  # Single query

# Good: Use prefetch_related for many-to-many
events = Event.objects.prefetch_related('ticket_types').all()
```

### Pagination

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}
```

## Common Tasks

### Adding a New Model

1. Define model in `models.py`
2. Create serializer in `serializers.py`
3. Create views in `views.py`
4. Add URLs in `urls.py`
5. Register in `admin.py`
6. Write tests
7. Create migrations

### Adding a New Endpoint

1. Create view function or viewset
2. Add URL pattern
3. Add permission classes
4. Write serializer if needed
5. Write tests
6. Update API documentation

### Adding External Service

1. Create service class in `event_management/utils/`
2. Add configuration to settings
3. Add environment variables to `.env.example`
4. Mock in tests
5. Document usage

## Useful Commands

```bash
# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run on different port
python manage.py runserver 8001

# Open Django shell
python manage.py shell

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test

# Run specific test
python manage.py test users.tests.TestClassName.test_method_name

# Check deployment readiness
python manage.py check --deploy

# Show SQL for migrations
python manage.py sqlmigrate users 0001
```

## Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'rest_framework'`
```bash
pip install -r requirements.txt
```

**Issue**: Database errors after model changes
```bash
python manage.py makemigrations
python manage.py migrate
```

**Issue**: Static files not loading
```bash
python manage.py collectstatic --noinput
```

**Issue**: Tests failing locally
```bash
# Clear test database
rm db.sqlite3
python manage.py migrate
python manage.py test
```

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)

## Getting Help

- Check the [Architecture](architecture.md) for system design
- Review [API Documentation](api/README.md) for endpoint details
- See [Testing Guide](testing.md) for test examples
- Create an issue on GitHub for bugs or questions
