# Installation Guide

This guide will help you set up the Event Management System locally for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher**
- **pip** (Python package manager)
- **virtualenv** (recommended for Python environment isolation)
- **Git** (for version control)
- **PostgreSQL** (optional, for production-like setup)

### Check Your Python Version
```bash
python --version
# Should show Python 3.10.x or higher
```

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd events
```

### 2. Create Virtual Environment

Creating a virtual environment isolates your project dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- Django 5.0
- Django REST Framework 3.14
- Stripe SDK
- Resend SDK
- And all other dependencies

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-generate-a-long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional, defaults to SQLite)
# DATABASE_URL=postgresql://user:password@localhost:5432/event_management

# Stripe Settings (get from https://dashboard.stripe.com)
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret

# Resend Settings (get from https://resend.com)
RESEND_API_KEY=re_your_resend_api_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Application URLs
SITE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=True
# CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

#### Generating a Secret Key

```python
# Run in Python shell
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 5. Set Up Stripe (Optional for Development)

1. Create a free account at [stripe.com](https://stripe.com)
2. Get your test API keys from the Dashboard
3. Add them to your `.env` file

For development, you can mock Stripe in tests without real API keys.

### 6. Set Up Resend (Optional for Development)

1. Create a free account at [resend.com](https://resend.com)
2. Get your API key
3. Add it to your `.env` file

For development, email functionality will fail gracefully without real API keys.

### 7. Run Database Migrations

```bash
# Create database tables
python manage.py migrate
```

You should see output like:
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying users.0001_initial... OK
  Applying events.0001_initial... OK
  ...
```

### 8. Create a Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account:
```
Email: admin@example.com
Username: admin
Password: ********
Password (again): ********
```

### 9. Run the Development Server

```bash
python manage.py runserver
```

You should see:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
Django version 5.0, using settings 'event_management.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### 10. Verify Installation

Visit these URLs to verify everything is working:

- **API Root**: http://localhost:8000/api/
- **Swagger Docs**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

## Post-Installation Setup

### Create Sample Data (Optional)

You can create sample data for testing:

```bash
python manage.py shell
```

```python
from users.models import User
from events.models import EventCategory, Event
from datetime import datetime, timedelta

# Create an organizer
organizer = User.objects.create_user(
    email='organizer@example.com',
    username='organizer',
    password='Password123!',
    role='organizer',
    is_email_verified=True
)

# Create categories
tech = EventCategory.objects.create(name='Technology', slug='technology')
music = EventCategory.objects.create(name='Music', slug='music')

# Create a sample event
event = Event.objects.create(
    title='Tech Conference 2024',
    slug='tech-conference-2024',
    description='A great tech conference',
    organizer=organizer,
    category=tech,
    location_city='San Francisco',
    location_country='USA',
    start_datetime=datetime.now() + timedelta(days=30),
    end_datetime=datetime.now() + timedelta(days=31),
    capacity=500,
    status='published',
    privacy='public'
)

print(f"Created event: {event.title}")
```

### Run Tests

Verify everything is working by running the test suite:

```bash
python manage.py test
```

You should see all tests passing:
```
.................................................................
----------------------------------------------------------------------
Ran 65 tests in 45.234s

OK
```

## Troubleshooting

### Issue: ModuleNotFoundError

**Solution**: Make sure your virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: Database Errors

**Solution**: Delete the database and run migrations again:
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Issue: Port Already in Use

**Solution**: Run on a different port:
```bash
python manage.py runserver 8001
```

### Issue: Static Files Not Loading

**Solution**: Collect static files:
```bash
python manage.py collectstatic --noinput
```

### Issue: ImportError for psycopg2

**Solution**: If using PostgreSQL and getting import errors:
```bash
pip install psycopg2-binary
```

## Using PostgreSQL (Production-like Setup)

For a production-like setup, use PostgreSQL:

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create Database

```bash
sudo -u postgres psql

# In psql prompt:
CREATE DATABASE event_management;
CREATE USER event_user WITH PASSWORD 'your_password';
ALTER ROLE event_user SET client_encoding TO 'utf8';
ALTER ROLE event_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE event_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE event_management TO event_user;
\q
```

### 3. Update .env

```env
DATABASE_URL=postgresql://event_user:your_password@localhost:5432/event_management
```

### 4. Run Migrations

```bash
python manage.py migrate
```

## Docker Setup (Alternative)

You can also use Docker for a containerized setup:

```bash
# Coming soon - Docker configuration
```

## Next Steps

Now that you have the system installed:

1. Read the [Development Guide](development.md) to learn about the codebase
2. Check out the [API Documentation](api/README.md) to understand the endpoints
3. Review the [Architecture](architecture.md) to understand the system design
4. Run the tests with `python manage.py test` to ensure everything works

## Getting Help

- Review the [Testing Guide](testing.md) for common issues
- Check the [Development Guide](development.md) for coding standards
- Create an issue on GitHub if you encounter problems
