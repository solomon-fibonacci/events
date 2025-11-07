# System Architecture

This document describes the architecture and design of the Event Management System.

## Overview

The Event Management System is a **backend-only REST API** built with Django and Django REST Framework. It follows a **modular, app-based architecture** with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend App                          │
│                  (To be implemented - See RFC-001)           │
│              React/Vue/Angular/Next.js                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS / REST API
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Django REST API Backend                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐│
│  │            Django REST Framework Layer                 ││
│  │  - JWT Authentication                                  ││
│  │  - Permission Classes                                  ││
│  │  - Serializers                                         ││
│  │  - ViewSets & APIViews                                 ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌────────────────────────────────────────────────────────┐│
│  │                  Django Apps Layer                     ││
│  │  ┌──────────┬──────────┬──────────┬──────────┐        ││
│  │  │  Users   │  Events  │ Tickets  │  Menus   │        ││
│  │  ├──────────┼──────────┼──────────┼──────────┤        ││
│  │  │ Reviews  │Notificns │   Tests  │  Utils   │        ││
│  │  └──────────┴──────────┴──────────┴──────────┘        ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌────────────────────────────────────────────────────────┐│
│  │              External Services Layer                   ││
│  │  - Stripe (Payments)                                   ││
│  │  - Resend (Email)                                      ││
│  │  - QR Code Generator                                   ││
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│                 (SQLite for Development)                     │
└─────────────────────────────────────────────────────────────┘
```

## Architectural Patterns

### 1. Model-View-Serializer (MVS) Pattern

The application follows Django REST Framework's MVS pattern:

- **Models**: Define data structure and business logic
- **Serializers**: Handle data transformation and validation
- **Views**: Handle HTTP requests and responses

### 2. App-Based Modularity

The system is divided into focused Django apps:

```
event_management/          # Core project configuration
├── users/                # User management
├── events/               # Event management
├── tickets/              # Ticketing system
├── menus/                # Food & drink menus
├── reviews/              # Reviews & ratings
└── notifications/        # Email notifications
```

Each app is self-contained with its own:
- Models
- Serializers
- Views
- URLs
- Tests
- Admin configuration

### 3. Service Layer Pattern

External integrations are abstracted into service classes:

```python
event_management/utils/
├── stripe_service.py     # Payment processing
├── email_service.py      # Email sending
└── qr_service.py         # QR code generation
```

This allows for:
- Easy mocking in tests
- Simplified replacement of services
- Centralized configuration

## Core Components

### Authentication & Authorization

```
┌─────────────────────────────────────────────────┐
│           JWT Authentication Flow                │
│                                                  │
│  1. User Login                                   │
│     POST /api/users/login/                       │
│     { "email": "user@example.com",              │
│       "password": "password" }                   │
│                                                  │
│  2. Server Response                              │
│     { "tokens": {                                │
│         "access": "eyJ...",  # 15 min           │
│         "refresh": "eyJ..."  # 7 days           │
│       }}                                         │
│                                                  │
│  3. Authenticated Requests                       │
│     Authorization: Bearer eyJ...                 │
│                                                  │
│  4. Token Refresh                                │
│     POST /api/users/token/refresh/              │
│     { "refresh": "eyJ..." }                     │
└─────────────────────────────────────────────────┘
```

**Role-Based Access Control (RBAC):**
- **Admin**: Full system access
- **Organizer**: Create/manage events, view analytics
- **Attendee**: Browse events, purchase tickets, leave reviews
- **Vendor**: Manage menus, handle food orders

### Data Models

#### User Management
```python
User (AbstractUser)
├── email (unique)
├── username (unique)
├── role (admin/organizer/attendee/vendor)
├── profile_picture
├── bio
└── is_email_verified

Follow
├── follower → User
└── following → User
```

#### Event Management
```python
EventCategory
└── name, slug, description

Event
├── organizer → User
├── category → EventCategory
├── title, slug, description
├── location (city, country, address, coordinates)
├── start_datetime, end_datetime
├── capacity, status, privacy
├── banner_image, thumbnail_image
└── view_count

EventFavorite
├── user → User
└── event → Event

EventComment
├── event → Event
├── user → User
├── parent → EventComment (for replies)
└── content, created_at
```

#### Ticketing System
```python
TicketType
├── event → Event
├── name, description
├── price, quantity_available
├── sale_start_date, sale_end_date
└── is_active

Order
├── user → User
├── event → Event
├── tickets → [{ticket_type, quantity}]
├── total_amount
├── payment_intent_id
└── status (pending/completed/cancelled)

Registration
├── order → Order
├── ticket_type → TicketType
├── attendee → User
├── qr_code_image
├── check_in_status
└── check_in_time

Refund
├── registration → Registration
├── requester → User
├── reason, status
└── processed_at
```

#### Food & Drink System
```python
MenuCategory
└── name, slug

Menu
├── event → Event
├── vendor → User
└── name, description, is_active

MenuItem
├── menu → Menu
├── category → MenuCategory
├── name, description, price
├── dietary_info (vegetarian, vegan, etc.)
└── quantity_available, is_available

FoodOrder
├── event → Event
├── user → User
├── items → [FoodOrderItem]
├── total_amount
├── payment_intent_id
└── status (pending/preparing/ready/delivered)

FoodOrderItem
├── order → FoodOrder
├── item → MenuItem
├── quantity, price
└── special_instructions
```

#### Reviews & Notifications
```python
Review
├── event → Event
├── user → User
├── rating (1-5)
├── comment
└── created_at

EmailNotification
├── recipient_email
├── subject, body
├── notification_type
├── sent_at
└── status (sent/failed)
```

## API Design

### RESTful Conventions

The API follows REST principles:

```
Resource Operations:
GET    /api/events/              # List events
POST   /api/events/              # Create event
GET    /api/events/{slug}/       # Get event detail
PUT    /api/events/{slug}/       # Update event
DELETE /api/events/{slug}/       # Delete event
```

### Response Format

**Success Response:**
```json
{
  "id": 1,
  "title": "Tech Conference 2024",
  "slug": "tech-conference-2024",
  "organizer": {
    "id": 5,
    "username": "organizer1",
    "email": "organizer@example.com"
  },
  "category": {
    "id": 2,
    "name": "Technology"
  },
  "start_datetime": "2024-06-15T10:00:00Z",
  "location_city": "San Francisco",
  "capacity": 500,
  "status": "published"
}
```

**Error Response:**
```json
{
  "detail": "Event not found",
  "code": "not_found"
}
```

**Validation Error:**
```json
{
  "field_name": [
    "This field is required.",
    "Ensure this value has at least 3 characters."
  ]
}
```

### Pagination

Lists are paginated using cursor pagination:

```json
{
  "count": 150,
  "next": "http://api.example.com/events/?page=2",
  "previous": null,
  "results": [
    { /* event object */ },
    { /* event object */ }
  ]
}
```

### Filtering & Search

Events support filtering and search:

```
GET /api/events/?city=San Francisco
GET /api/events/?category=technology
GET /api/events/?search=conference
GET /api/events/?status=published&privacy=public
GET /api/events/?start_date__gte=2024-06-01
```

## External Service Integration

### Stripe Payment Processing

```
┌─────────────────────────────────────────────────┐
│           Payment Flow (Stripe)                  │
│                                                  │
│  1. Create Payment Intent                        │
│     Backend: stripe.PaymentIntent.create()       │
│     Returns: client_secret                       │
│                                                  │
│  2. Frontend Payment                             │
│     Stripe.js confirmCardPayment()               │
│                                                  │
│  3. Webhook Notification                         │
│     POST /api/webhooks/stripe/                   │
│     payment_intent.succeeded                     │
│                                                  │
│  4. Confirm Order & Generate Tickets             │
│     - Update order status                        │
│     - Generate QR codes                          │
│     - Send email with tickets                    │
└─────────────────────────────────────────────────┘
```

### Resend Email Service

```
┌─────────────────────────────────────────────────┐
│              Email Flow (Resend)                 │
│                                                  │
│  1. Trigger Event (e.g., ticket purchase)        │
│                                                  │
│  2. email_service.send_email()                   │
│     - Build HTML email                           │
│     - Attach QR code (if needed)                 │
│     - Call Resend API                            │
│                                                  │
│  3. Create EmailNotification record              │
│     - Track sent emails                          │
│     - Store status                               │
│                                                  │
│  4. Handle failures gracefully                   │
│     - Log errors                                 │
│     - Retry mechanism (future)                   │
└─────────────────────────────────────────────────┘
```

### QR Code Generation

```python
# qr_service.py
def generate_qr_code(data: str) -> str:
    """
    Generates QR code image from data.

    Args:
        data: String to encode in QR code

    Returns:
        Path to generated QR code image
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    # Save and return path
```

## Security Architecture

### Authentication Security
- JWT tokens with short expiration (15 minutes access, 7 days refresh)
- Password hashing with Django's PBKDF2 algorithm
- Email verification required for account activation
- Password strength validation

### API Security
- CORS configuration for frontend domain
- CSRF protection for cookie-based auth
- Rate limiting (to be implemented)
- SQL injection protection via Django ORM
- XSS protection via DRF serializers

### Payment Security
- PCI compliance via Stripe
- No card data stored locally
- Webhook signature verification
- HTTPS enforced in production

### Data Security
- Role-based access control (RBAC)
- Object-level permissions
- Sensitive data encryption at rest (PostgreSQL)
- Secure session management

## Performance Considerations

### Database Optimization
- Indexed fields (slug, email, foreign keys)
- `select_related()` for foreign key queries
- `prefetch_related()` for many-to-many queries
- Database connection pooling

### Caching Strategy (Future)
```python
# Planned caching layers
- Redis for session storage
- Cache event listings (5 min)
- Cache category lists (1 hour)
- Cache user profiles (15 min)
```

### Query Optimization
```python
# Example optimized query
Event.objects.select_related(
    'organizer', 'category'
).prefetch_related(
    'ticket_types', 'favorites'
).filter(status='published')
```

## Scalability

### Current Architecture
- Monolithic Django application
- Single database (PostgreSQL)
- Synchronous request handling

### Future Scaling Options
1. **Horizontal Scaling**: Multiple app servers behind load balancer
2. **Database Replication**: Read replicas for queries
3. **Caching Layer**: Redis for frequently accessed data
4. **CDN**: Static assets and media files
5. **Async Tasks**: Celery for background jobs (emails, reports)
6. **Microservices**: Extract ticketing/payments into separate services

## Deployment Architecture

### Development
```
localhost:8000 (Django Dev Server)
└── SQLite database
```

### Production
```
┌──────────────────────────────────────────────────┐
│              Load Balancer / CDN                  │
└──────────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───────┐       ┌───────┐       ┌───────┐
│ App   │       │ App   │       │ App   │
│Server1│       │Server2│       │Server3│
└───────┘       └───────┘       └───────┘
    │               │               │
    └───────────────┼───────────────┘
                    │
        ┌───────────────────────┐
        │  PostgreSQL Database  │
        │    (with backups)     │
        └───────────────────────┘
```

## Testing Architecture

### Test Pyramid
```
                 ┌─────────┐
                 │   E2E   │  Complete user journeys
                 │  Tests  │  (Integration tests)
                 └─────────┘
              ┌─────────────┐
              │    API      │   Endpoint testing
              │   Tests     │   (View tests)
              └─────────────┘
           ┌──────────────────┐
           │  Unit Tests      │  Model & utility tests
           │  (Models, Utils) │
           └──────────────────┘
```

### Test Strategy
- **E2E Tests**: Test complete user flows
- **API Tests**: Test endpoints and serializers
- **Unit Tests**: Test models and utilities
- **Mocking**: External services (Stripe, Resend)
- **CI/CD**: GitHub Actions runs all tests

## Directory Structure

```
event_management/
├── event_management/      # Core project
│   ├── settings.py       # Django configuration
│   ├── urls.py           # URL routing
│   ├── api_views.py      # Centralized API views
│   ├── permissions.py    # Custom permissions
│   └── utils/            # Service layer
│       ├── stripe_service.py
│       ├── email_service.py
│       └── qr_service.py
├── users/                # User management app
├── events/               # Event management app
├── tickets/              # Ticketing app
├── menus/                # Food ordering app
├── reviews/              # Reviews app
├── notifications/        # Email notifications app
├── tests/                # Integration tests
├── media/                # Uploaded files
├── static/               # Static files
├── docs/                 # Documentation
├── manage.py             # Django CLI
├── requirements.txt      # Python dependencies
└── .env                  # Environment configuration
```

## Technology Decisions

### Why Django?
- Mature, battle-tested framework
- Excellent ORM for complex queries
- Built-in admin panel
- Strong security features
- Large ecosystem of packages

### Why Django REST Framework?
- Best-in-class REST API support
- Powerful serialization
- Built-in authentication
- Browsable API for development
- Excellent documentation

### Why JWT?
- Stateless authentication
- Works well with frontend apps
- Mobile-friendly
- Scalable (no server-side sessions)

### Why Stripe?
- Industry-leading payment processing
- Excellent developer experience
- PCI compliance handled
- Comprehensive documentation
- Webhook support

### Why Resend?
- Modern email API
- Reliable delivery
- Email verification support
- Attachment support
- Good pricing for startups

## Future Architectural Improvements

### Short Term
1. Implement Redis caching
2. Add rate limiting
3. Implement async email sending with Celery
4. Add WebSocket support for real-time updates

### Long Term
1. Extract payment processing into microservice
2. Implement event sourcing for audit trails
3. Add GraphQL API alongside REST
4. Implement full-text search with Elasticsearch
5. Add analytics with data warehouse

## References

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Stripe API](https://stripe.com/docs/api)
- [Resend Documentation](https://resend.com/docs)
