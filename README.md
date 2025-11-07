# Event Management System

[![Django Tests](https://github.com/username/events/workflows/Django%20Tests/badge.svg)](https://github.com/username/events/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.0](https://img.shields.io/badge/django-5.0-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive, production-ready backend API for event management featuring ticketing, food ordering, payments (Stripe), and email notifications (Resend).

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd events

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Visit http://localhost:8000/api/ to see the API.

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

### Getting Started
- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[Quick Start](docs/README.md#quick-start)** - Get running in 5 minutes
- **[Configuration Guide](docs/configuration.md)** - Environment variables and settings

### Core Documentation
- **[Architecture Overview](docs/architecture.md)** - System design and technical architecture
- **[API Reference](docs/api/README.md)** - Complete API endpoint documentation
- **[Development Guide](docs/development.md)** - Development workflows and best practices
- **[Testing Guide](docs/testing.md)** - Testing strategy and running tests

### Deployment
- **[Production Deployment](docs/deployment.md)** - Deploy to production environments
- **[Configuration Reference](docs/configuration.md)** - All environment variables explained

### Planning & Design
- **[RFC-001: Frontend Application](docs/rfc/001-frontend-application.md)** - Comprehensive frontend architecture proposal

## ✨ Features

### 🔐 User Management
- User registration with email verification
- JWT-based authentication with refresh tokens
- Role-based access control (Admin, Organizer, Attendee, Vendor)
- User profiles with pictures and bios
- Follow/unfollow system for users
- Password management and reset

### 🎫 Event Management
- Full CRUD operations for events
- Event categories and tagging
- Event status management (draft, published, cancelled, completed)
- Privacy settings (public, private, invite-only)
- Location-based search (city, country, coordinates)
- Event banners and thumbnails
- View count tracking
- Event favorites/bookmarks
- Comments and Q&A system

### 🎟️ Ticketing System
- Multiple ticket types per event (free, paid, VIP, early bird)
- Ticket quantity management and availability
- Stripe payment integration
- QR code generation and validation
- Ticket check-in system with duplicate prevention
- Order management and history
- Refund request handling

### 🍔 Food & Drink Ordering
- Event menu management
- Menu categories (appetizers, entrees, desserts, beverages)
- Dietary information (vegetarian, vegan, gluten-free, halal, kosher)
- Stock management for menu items
- Pre-ordering and at-event ordering
- Order status tracking (pending, preparing, ready, delivered)
- Stripe payment integration

### ⭐ Reviews & Ratings
- Post-event reviews with 1-5 star ratings
- Review moderation system
- Average rating calculation
- Review editing and deletion

### 📧 Email Notifications (Resend)
- Email verification
- Registration confirmations
- Ticket receipts with QR codes
- Event reminders
- Food order confirmations
- Event updates and cancellations

### 📊 Analytics & Reporting
- Event statistics (views, registrations, attendance)
- Revenue tracking (tickets and food)
- Attendance rate calculation
- Review aggregation
- Organizer-specific analytics

## 🛠️ Technology Stack

- **Framework**: Django 5.0
- **API**: Django REST Framework 3.14
- **Authentication**: JWT (Simple JWT)
- **Payment Processing**: Stripe
- **Email Service**: Resend
- **QR Code Generation**: qrcode + Pillow
- **Database**: PostgreSQL (production) / SQLite (development)
- **API Documentation**: Swagger/OpenAPI (drf-yasg)
- **Testing**: pytest + coverage
- **Code Quality**: flake8, black, isort, bandit, safety

## 📖 API Documentation

Interactive API documentation is available when running the server:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

See the [API Reference](docs/api/README.md) for complete endpoint documentation.

## 🏗️ Architecture

The system follows a modular, app-based architecture:

```
event_management/
├── event_management/      # Core project configuration
│   ├── settings.py       # Django configuration
│   ├── urls.py           # URL routing
│   ├── api_views.py      # Centralized API views
│   ├── permissions.py    # Custom permissions
│   └── utils/            # Service layer
│       ├── stripe_service.py
│       ├── email_service.py
│       └── qr_service.py
├── users/                # User management
├── events/               # Event management
├── tickets/              # Ticketing system
├── menus/                # Food & drink menus
├── reviews/              # Reviews & ratings
├── notifications/        # Email notifications
└── tests/                # Integration tests
```

See [Architecture Overview](docs/architecture.md) for detailed information.

## 🧪 Testing

The project includes comprehensive E2E tests covering:
- Authentication flows
- Event management
- Ticketing system
- Food ordering
- Review system
- Complete user journeys

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# Run specific test suite
python manage.py test users.test_e2e_authentication
```

See [Testing Guide](docs/testing.md) for details.

## 🚀 Deployment

The application can be deployed using various methods:
- Docker (recommended)
- Traditional server deployment
- Platform as a Service (Heroku, AWS Elastic Beanstalk, DigitalOcean)

See [Deployment Guide](docs/deployment.md) for detailed instructions.

## 🎨 Frontend Application

A comprehensive frontend application is planned to complement this backend API. See [RFC-001: Frontend Application](docs/rfc/001-frontend-application.md) for the complete proposal including:

- **Technology Stack**: Next.js 14+ with TypeScript and Tailwind CSS
- **Features**: All backend capabilities exposed through beautiful UI
- **Design System**: Modern, accessible, responsive design
- **Development Roadmap**: 15-week phased implementation plan
- **Performance Goals**: Sub-2-second load times, excellent Core Web Vitals

## 👥 User Roles

The system supports four user roles:

- **Admin**: Full system access, user management, content moderation
- **Organizer**: Create and manage events, view analytics, manage attendees
- **Attendee**: Browse events, purchase tickets, order food, leave reviews
- **Vendor**: Manage menus, handle food orders, view sales

## 🔒 Security

- JWT token-based authentication with refresh tokens
- Role-based access control (RBAC)
- CSRF protection
- CORS configuration
- Password validation and hashing
- Email verification
- Secure payment handling via Stripe
- SQL injection protection (Django ORM)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

See [Development Guide](docs/development.md) for coding standards and best practices.

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Bug Reports**: [Create an issue](https://github.com/username/events/issues)
- **Feature Requests**: [Create an issue](https://github.com/username/events/issues) with the "enhancement" label
- **Email**: support@eventmanagement.com

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- Stripe for payment processing
- Resend for email delivery
- All contributors to this project

## 📊 Project Stats

- **Database Models**: 17 models across 6 apps
- **API Endpoints**: 30+ RESTful endpoints
- **Test Coverage**: 80%+ with E2E tests
- **Python Packages**: 31 dependencies
- **Supported Python**: 3.10, 3.11

## 🗺️ Roadmap

### Current Status
✅ Backend API - Complete and production-ready

### Upcoming
- [ ] Frontend Application (see RFC-001)
- [ ] Mobile Apps (React Native)
- [ ] Real-time features (WebSocket)
- [ ] Advanced analytics
- [ ] Multi-language support

## 📞 Contact

For questions or inquiries:
- **Email**: support@eventmanagement.com
- **GitHub Issues**: https://github.com/username/events/issues
- **Documentation**: https://docs.eventmanagement.com

---

**Made with ❤️ by the Event Management Team**
