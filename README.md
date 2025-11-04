# Event Management System - Django REST API

A comprehensive, fully-featured backend system for event management with ticketing, food/drink ordering, payments (Stripe), and email notifications (Resend).

## Features

### User Management
- ✅ User registration with email verification
- ✅ JWT-based authentication
- ✅ Role-based access control (Admin, Organizer, Attendee, Vendor)
- ✅ User profiles with profile pictures
- ✅ Follow/Unfollow system for users
- ✅ Password management and reset

### Event Management
- ✅ Create, read, update, delete (CRUD) events
- ✅ Event categories and tagging
- ✅ Event status management (draft, published, cancelled, completed)
- ✅ Privacy settings (public, private, invite-only)
- ✅ Location-based search (city, country, coordinates)
- ✅ Event banners and thumbnails
- ✅ View count tracking
- ✅ Event favorites/bookmarks
- ✅ Comments and Q&A system

### Ticketing System
- ✅ Multiple ticket types per event (free, paid, VIP, early bird)
- ✅ Ticket quantity management and availability
- ✅ Stripe payment integration
- ✅ QR code generation for tickets
- ✅ Ticket check-in system
- ✅ Order management and history
- ✅ Refund handling

### Food & Drink Menu System
- ✅ Create menus for events
- ✅ Menu categories (appetizers, entrees, desserts, beverages)
- ✅ Dietary information (vegetarian, vegan, gluten-free, halal, kosher)
- ✅ Stock management for menu items
- ✅ Pre-ordering and at-event ordering
- ✅ Order status tracking (pending, preparing, ready, delivered)
- ✅ Stripe payment integration for food orders

### Reviews & Ratings
- ✅ Post-event reviews with 1-5 star ratings
- ✅ Review moderation system
- ✅ Average rating calculation

### Email Notifications (Resend)
- ✅ Email verification
- ✅ Registration confirmations
- ✅ Ticket receipts with QR codes
- ✅ Event reminders
- ✅ Food order confirmations
- ✅ Event updates and cancellations

### Analytics & Reporting
- ✅ Event statistics (views, registrations, attendance)
- ✅ Revenue tracking
- ✅ Attendance rate calculation
- ✅ Review aggregation

### API Features
- ✅ RESTful API design
- ✅ Swagger/OpenAPI documentation
- ✅ Pagination and filtering
- ✅ Search functionality
- ✅ Permission-based access control
- ✅ Comprehensive error handling

## Technology Stack

- **Framework**: Django 5.0
- **API**: Django REST Framework 3.14
- **Authentication**: JWT (Simple JWT)
- **Payment Processing**: Stripe
- **Email Service**: Resend
- **QR Code Generation**: qrcode + Pillow
- **Database**: SQLite (development) / PostgreSQL (production)
- **API Documentation**: drf-yasg (Swagger/OpenAPI)
- **CORS**: django-cors-headers

## Installation

### Prerequisites
- Python 3.10+
- pip
- virtualenv (recommended)

### Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd events
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Stripe Settings
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret

# Resend Settings
RESEND_API_KEY=re_your_resend_api_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Application URLs
SITE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run the development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

### Admin Panel
- **URL**: http://localhost:8000/admin/
- Login with your superuser credentials

## API Endpoints

### Authentication
```
POST   /api/users/register/           - User registration
POST   /api/users/login/              - User login
POST   /api/users/token/refresh/      - Refresh JWT token
POST   /api/users/verify-email/       - Verify email address
GET    /api/users/profile/            - Get user profile
PUT    /api/users/profile/            - Update user profile
POST   /api/users/change-password/    - Change password
```

### Events
```
GET    /api/events/                   - List all events
POST   /api/events/                   - Create event (organizers only)
GET    /api/events/{slug}/            - Get event details
PUT    /api/events/{slug}/            - Update event (organizer only)
DELETE /api/events/{slug}/            - Delete event (organizer only)
POST   /api/events/{slug}/favorite/   - Favorite/unfavorite event
GET    /api/events/{slug}/ticket_types/ - Get ticket types for event
```

### Event Categories
```
GET    /api/categories/               - List all categories
GET    /api/categories/{id}/          - Get category details
```

### Comments
```
GET    /api/comments/                 - List all comments
POST   /api/comments/                 - Create comment
GET    /api/comments/{id}/            - Get comment details
PUT    /api/comments/{id}/            - Update comment (author only)
DELETE /api/comments/{id}/            - Delete comment (author only)
```

### Tickets
```
POST   /api/tickets/order/            - Create ticket order
GET    /api/tickets/my-tickets/       - Get user's tickets
POST   /api/tickets/check-in/         - Check-in ticket using QR code
```

### Menus
```
GET    /api/menus/                    - List all menus
POST   /api/menus/                    - Create menu (vendors/organizers)
GET    /api/menus/{id}/               - Get menu details
PUT    /api/menus/{id}/               - Update menu
DELETE /api/menus/{id}/               - Delete menu
```

### Food Orders
```
POST   /api/food/order/               - Create food order
```

### Reviews
```
GET    /api/reviews/                  - List all reviews
POST   /api/reviews/                  - Create review
GET    /api/reviews/{id}/             - Get review details
PUT    /api/reviews/{id}/             - Update review (author only)
DELETE /api/reviews/{id}/             - Delete review (author only)
```

### Analytics
```
GET    /api/analytics/event/{id}/     - Get event analytics (organizer only)
```

### Follow System
```
POST   /api/users/follow/{user_id}/   - Follow user
DELETE /api/users/follow/{user_id}/   - Unfollow user
GET    /api/users/followers/          - Get my followers
GET    /api/users/following/          - Get users I'm following
```

## Database Models

### User Roles
- **Admin**: Full system access
- **Organizer**: Can create and manage events
- **Attendee**: Can register for events and order food
- **Vendor**: Can manage menus and food orders

### Main Models
- **User**: Extended Django user with roles and profiles
- **Event**: Event information with location, timing, and capacity
- **EventCategory**: Categories for organizing events
- **TicketType**: Different ticket types for events
- **Order**: Ticket purchase orders
- **Registration**: Individual tickets with QR codes
- **Menu**: Event menus
- **MenuItem**: Food and drink items
- **FoodOrder**: Food/drink orders
- **Review**: Event reviews and ratings
- **EmailNotification**: Email notification tracking

## Payment Integration (Stripe)

### Ticket Purchases
1. User selects tickets and submits order
2. System creates Stripe Payment Intent
3. Frontend handles payment with Stripe.js
4. On successful payment, tickets are confirmed
5. QR codes are generated and emailed

### Food Orders
1. User selects menu items and submits order
2. System creates Stripe Payment Intent
3. Payment processed via frontend
4. Order is sent to kitchen/vendor

### Webhook Handling
Configure Stripe webhooks to handle:
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `charge.refunded`

## Email Service (Resend)

### Supported Email Types
- Email verification
- Password reset
- Registration confirmation
- Ticket receipts (with QR codes)
- Event reminders
- Event updates/cancellations
- Food order confirmations
- Food order status updates

### Configuration
Set your Resend API key in `.env`:
```env
RESEND_API_KEY=re_your_api_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## QR Code System

### Ticket QR Codes
- Generated automatically upon ticket purchase
- Contains ticket number for verification
- Stored as image file in media directory
- Included in email receipts
- Used for check-in at events

### Scanning Flow
1. Scan QR code at event entrance
2. POST to `/api/tickets/check-in/` with ticket number
3. System verifies ticket and marks as checked-in
4. Records check-in timestamp and staff member

## Security Features

- JWT token-based authentication
- Role-based permissions
- CSRF protection
- CORS configuration
- Password validation
- Email verification
- Secure payment handling via Stripe
- SQL injection protection (Django ORM)

## Production Deployment

### Environment Setup
1. Set `DEBUG=False` in `.env`
2. Configure proper `ALLOWED_HOSTS`
3. Use PostgreSQL instead of SQLite
4. Set up proper SECRET_KEY
5. Configure HTTPS
6. Set up Stripe webhook endpoints
7. Configure email domain in Resend

### Database Migration (PostgreSQL)
```python
# In settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'event_management',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Static Files
```bash
python manage.py collectstatic
```

### Deployment Checklist
- [ ] Environment variables configured
- [ ] Database migrated
- [ ] Static files collected
- [ ] Media files directory configured
- [ ] Stripe webhooks configured
- [ ] Resend domain verified
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Admin superuser created
- [ ] Error logging configured

## Testing

### Run Tests
```bash
python manage.py test
```

### Test Coverage
```bash
coverage run --source='.' manage.py test
coverage report
```

## Project Structure

```
events/
├── event_management/       # Main project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL configuration
│   ├── api_views.py       # Centralized API views
│   ├── permissions.py     # Custom permissions
│   └── utils/             # Utility services
│       ├── stripe_service.py
│       ├── email_service.py
│       └── qr_service.py
├── users/                 # User management app
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── events/                # Events app
│   ├── models.py
│   ├── serializers.py
│   └── admin.py
├── tickets/               # Ticketing app
│   ├── models.py
│   ├── serializers.py
│   └── admin.py
├── menus/                 # Food/drink menus app
│   ├── models.py
│   ├── serializers.py
│   └── admin.py
├── reviews/               # Reviews app
│   ├── models.py
│   ├── serializers.py
│   └── admin.py
├── notifications/         # Email notifications app
│   ├── models.py
│   ├── serializers.py
│   └── admin.py
├── media/                 # Uploaded files
├── manage.py
└── requirements.txt
```

## Testing

This project includes comprehensive End-to-End (E2E) tests to ensure reliability and maintain confidence as changes are made.

### Test Coverage

- ✅ **Authentication Flow**: Registration, login, email verification, profile management
- ✅ **Event Management**: CRUD operations, filtering, search, favorites, comments
- ✅ **Ticketing System**: Purchase flow, QR codes, check-in, refunds
- ✅ **Food Ordering**: Menu browsing, ordering, payment processing
- ✅ **Review System**: Submission, validation, editing
- ✅ **Complete User Journeys**: End-to-end flows across multiple features

### Running Tests Locally

```bash
# Run all tests
python manage.py test

# Run specific test suite
python manage.py test users.test_e2e_authentication
python manage.py test events.test_e2e_events
python manage.py test tickets.test_e2e_ticketing
python manage.py test tests.test_e2e_integration

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report in htmlcov/

# Run with verbosity
python manage.py test --verbosity=2
```

### Continuous Integration (GitHub Actions)

Tests run automatically on every push and pull request:

- **Python 3.10 & 3.11** compatibility
- **PostgreSQL** integration testing
- **Code coverage** reporting
- **Linting** (flake8, black, isort)
- **Security scanning** (safety, bandit)
- **Deployment checks**

View test results in the **Actions** tab on GitHub.

### Test Documentation

For detailed testing information, see [TESTING.md](TESTING.md):
- Test scenarios and coverage
- Adding new tests
- Debugging failed tests
- CI/CD pipeline details

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, email support@eventmanagement.com or open an issue on GitHub.

## Acknowledgments

- Django and Django REST Framework communities
- Stripe for payment processing
- Resend for email delivery
- All contributors to this project
