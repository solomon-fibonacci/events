# Event Management System Documentation

Welcome to the Event Management System documentation. This comprehensive guide will help you understand, deploy, and develop with our event management platform.

## Table of Contents

### Getting Started
- [Installation Guide](installation.md) - Set up the project locally
- [Quick Start](#quick-start) - Get up and running in 5 minutes

### Core Documentation
- [Architecture Overview](architecture.md) - System design and structure
- [API Reference](api/README.md) - Complete API documentation
- [Development Guide](development.md) - Development workflows and best practices
- [Testing Guide](testing.md) - Testing strategy and running tests

### Deployment
- [Production Deployment](deployment.md) - Deploy to production environments
- [Configuration Guide](configuration.md) - Environment variables and settings

### RFCs (Request for Comments)
- [RFC-001: Frontend Application](rfc/001-frontend-application.md) - Proposed frontend architecture

## What is the Event Management System?

A comprehensive, production-ready backend API for event management featuring:

- **User Management** - Authentication, profiles, roles (Admin, Organizer, Attendee, Vendor)
- **Event Management** - Full CRUD, categories, search, favorites, comments
- **Ticketing System** - Multiple ticket types, Stripe payments, QR codes, check-ins
- **Food & Drink Menus** - Menu management, ordering, dietary preferences
- **Reviews & Ratings** - Post-event reviews with 1-5 star ratings
- **Email Notifications** - Automated emails via Resend
- **Analytics** - Event statistics, revenue tracking, attendance rates

## Technology Stack

- **Framework**: Django 5.0 + Django REST Framework 3.14
- **Authentication**: JWT (Simple JWT)
- **Payments**: Stripe
- **Email**: Resend
- **Database**: PostgreSQL (production) / SQLite (development)
- **API Docs**: Swagger/OpenAPI

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd events
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Migrations
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Start Server
```bash
python manage.py runserver
```

Visit:
- **API**: http://localhost:8000/api/
- **Swagger Docs**: http://localhost:8000/api/docs/
- **Admin**: http://localhost:8000/admin/

## Key Features

### For Event Organizers
- Create and manage events with full control
- Multiple ticket types (free, paid, VIP, early bird)
- Real-time analytics and reporting
- QR code-based check-in system
- Manage menus and food orders

### For Attendees
- Browse and search events by location and category
- Purchase tickets with secure payment processing
- Receive tickets via email with QR codes
- Pre-order food and drinks
- Leave reviews and ratings

### For Vendors
- Manage event menus
- Track food orders
- Update order status
- View sales analytics

### For Admins
- Full system access
- User management
- Content moderation
- System-wide analytics

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`

See [API Reference](api/README.md) for detailed endpoint documentation.

## Development

See the [Development Guide](development.md) for:
- Setting up your development environment
- Code style and standards
- Contributing guidelines
- Git workflow

## Testing

The project includes comprehensive E2E tests covering:
- Authentication flows
- Event management
- Ticketing system
- Food ordering
- Review system
- Complete user journeys

See [Testing Guide](testing.md) for details.

## Deployment

For production deployment instructions, see [Deployment Guide](deployment.md).

## Support

- **Documentation Issues**: Create an issue in the repository
- **Bug Reports**: Use GitHub Issues
- **Feature Requests**: Use GitHub Issues with the "enhancement" label

## License

This project is licensed under the MIT License.
