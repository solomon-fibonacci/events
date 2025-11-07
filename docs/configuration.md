# Configuration Guide

Complete guide to configuring the Event Management System.

## Environment Variables

All configuration is done via environment variables in the `.env` file.

### Creating .env File

```bash
cp .env.example .env
```

## Core Django Settings

### SECRET_KEY

**Required**: Yes
**Description**: Django secret key for cryptographic signing
**Example**: `SECRET_KEY=django-insecure-long-random-string-min-50-characters`

Generate a secure key:
```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Security**: Keep this secret! Never commit to version control.

### DEBUG

**Required**: Yes
**Description**: Enable/disable debug mode
**Values**: `True` or `False`
**Default**: `True`

**Development**:
```env
DEBUG=True
```

**Production**:
```env
DEBUG=False
```

**Warning**: NEVER run production with DEBUG=True!

### ALLOWED_HOSTS

**Required**: Yes (in production)
**Description**: Comma-separated list of allowed hosts
**Example**: `ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com`

**Development**:
```env
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Production**:
```env
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
```

## Database Configuration

### DATABASE_URL

**Required**: No (defaults to SQLite)
**Description**: PostgreSQL database connection URL
**Format**: `postgresql://user:password@host:port/database`

**Development (SQLite - default)**:
```env
# No DATABASE_URL needed - uses SQLite
```

**Development (PostgreSQL)**:
```env
DATABASE_URL=postgresql://event_user:password@localhost:5432/event_management
```

**Production**:
```env
DATABASE_URL=postgresql://event_user:strong_password@db.example.com:5432/event_management_prod
```

## Stripe Configuration

### STRIPE_PUBLIC_KEY

**Required**: Yes (for payments)
**Description**: Stripe publishable key for frontend
**Example**: `STRIPE_PUBLIC_KEY=pk_test_...` or `pk_live_...`

Get from: https://dashboard.stripe.com/apikeys

**Development**:
```env
STRIPE_PUBLIC_KEY=pk_test_51234567890abcdef
```

**Production**:
```env
STRIPE_PUBLIC_KEY=pk_live_51234567890abcdef
```

### STRIPE_SECRET_KEY

**Required**: Yes (for payments)
**Description**: Stripe secret key for backend API calls
**Example**: `STRIPE_SECRET_KEY=sk_test_...` or `sk_live_...`

**Development**:
```env
STRIPE_SECRET_KEY=sk_test_51234567890abcdef
```

**Production**:
```env
STRIPE_SECRET_KEY=sk_live_51234567890abcdef
```

**Security**: Keep this secret! Never expose to frontend.

### STRIPE_WEBHOOK_SECRET

**Required**: Yes (for webhook verification)
**Description**: Stripe webhook signing secret
**Example**: `STRIPE_WEBHOOK_SECRET=whsec_...`

Get from: Stripe Dashboard → Developers → Webhooks

**Development**:
```env
STRIPE_WEBHOOK_SECRET=whsec_test_1234567890
```

**Production**:
```env
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef
```

## Email Configuration (Resend)

### RESEND_API_KEY

**Required**: Yes (for emails)
**Description**: Resend API key
**Example**: `RESEND_API_KEY=re_...`

Get from: https://resend.com/api-keys

```env
RESEND_API_KEY=re_1234567890_abcdefghijklmnop
```

### DEFAULT_FROM_EMAIL

**Required**: Yes (for emails)
**Description**: Default sender email address
**Example**: `DEFAULT_FROM_EMAIL=noreply@yourdomain.com`

**Development**:
```env
DEFAULT_FROM_EMAIL=noreply@localhost
```

**Production**:
```env
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Note**: Domain must be verified in Resend dashboard for production.

## Application URLs

### SITE_URL

**Required**: Yes
**Description**: Backend API base URL
**Format**: Full URL with protocol, no trailing slash

**Development**:
```env
SITE_URL=http://localhost:8000
```

**Production**:
```env
SITE_URL=https://api.yourdomain.com
```

### FRONTEND_URL

**Required**: Yes
**Description**: Frontend application URL for CORS and emails
**Format**: Full URL with protocol, no trailing slash

**Development**:
```env
FRONTEND_URL=http://localhost:3000
```

**Production**:
```env
FRONTEND_URL=https://yourdomain.com
```

## CORS Configuration

### CORS_ALLOW_ALL_ORIGINS

**Required**: No
**Description**: Allow requests from any origin
**Values**: `True` or `False`
**Default**: `False`

**Development**:
```env
CORS_ALLOW_ALL_ORIGINS=True
```

**Production**:
```env
CORS_ALLOW_ALL_ORIGINS=False
```

### CORS_ALLOWED_ORIGINS

**Required**: Yes (if CORS_ALLOW_ALL_ORIGINS=False)
**Description**: Comma-separated list of allowed origins
**Example**: `CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com`

**Production**:
```env
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com
```

## Complete Configuration Examples

### Development Configuration

```env
# Django Core
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite - default)
# DATABASE_URL not needed for SQLite

# Stripe (Test Mode)
STRIPE_PUBLIC_KEY=pk_test_51234567890abcdef
STRIPE_SECRET_KEY=sk_test_51234567890abcdef
STRIPE_WEBHOOK_SECRET=whsec_test_1234567890

# Resend (Test)
RESEND_API_KEY=re_test_1234567890
DEFAULT_FROM_EMAIL=noreply@localhost

# URLs
SITE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ALLOW_ALL_ORIGINS=True
```

### Production Configuration

```env
# Django Core
SECRET_KEY=your-production-secret-key-min-50-characters-random-string
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

# Database (PostgreSQL)
DATABASE_URL=postgresql://event_user:strong_password@db.example.com:5432/event_management_prod

# Stripe (Live Mode)
STRIPE_PUBLIC_KEY=pk_live_51234567890abcdef
STRIPE_SECRET_KEY=sk_live_51234567890abcdef
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef

# Resend (Production)
RESEND_API_KEY=re_1234567890_abcdefghijklmnop
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# URLs
SITE_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Advanced Settings

### Custom Database Settings

For more control over database configuration, you can modify `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'event_management',
        'USER': 'event_user',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'
        }
    }
}
```

Environment variables:
```env
DB_PASSWORD=your_db_password
DB_HOST=db.example.com
DB_PORT=5432
```

### Email Backend Configuration

By default, the system uses Resend. To use a different email backend:

**SMTP Configuration**:
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
```

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Static Files Configuration

**Development** (default):
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

**Production with S3**:
```python
# settings.py
if not DEBUG:
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

### Media Files Configuration

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**With S3**:
```python
if not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### Cache Configuration

**Redis Cache**:
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

```env
REDIS_URL=redis://127.0.0.1:6379/1
```

### Logging Configuration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.getenv('LOG_FILE', '/var/log/event-management/django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

```env
LOG_FILE=/var/log/event-management/django.log
```

## Security Settings

### Production Security Checklist

Enable these settings in production:

```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Session Configuration

```python
# settings.py
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
```

Custom via environment:
```env
SESSION_COOKIE_AGE=1209600
```

## Testing Configuration

For running tests, you can use a separate `.env.test` file:

```env
SECRET_KEY=test-secret-key
DEBUG=True
DATABASE_URL=sqlite:///test_db.sqlite3
STRIPE_SECRET_KEY=sk_test_fake_for_testing
RESEND_API_KEY=re_test_fake_for_testing
SITE_URL=http://testserver
FRONTEND_URL=http://testserver
```

Load in tests:
```python
from decouple import config
config.search_path = '.env.test'
```

## Environment-Specific Configuration

### Using Multiple Environments

You can create different .env files:

```bash
.env.development
.env.staging
.env.production
```

Load specific file:
```bash
# Development
cp .env.development .env
python manage.py runserver

# Staging
cp .env.staging .env
python manage.py runserver

# Production
cp .env.production .env
gunicorn event_management.wsgi
```

## Configuration Validation

### Check Configuration

```bash
# Check for configuration issues
python manage.py check

# Check deployment configuration
python manage.py check --deploy
```

### Required Variables Check

Create `event_management/config_check.py`:

```python
import os
from django.core.exceptions import ImproperlyConfigured

REQUIRED_VARS = [
    'SECRET_KEY',
    'DEBUG',
    'STRIPE_SECRET_KEY',
    'RESEND_API_KEY',
    'DEFAULT_FROM_EMAIL',
]

def check_environment():
    missing = []
    for var in REQUIRED_VARS:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        raise ImproperlyConfigured(
            f"Missing required environment variables: {', '.join(missing)}"
        )

check_environment()
```

## Troubleshooting

### Configuration Not Loading

**Check file exists**:
```bash
ls -la .env
```

**Check file permissions**:
```bash
chmod 600 .env
```

**Check syntax**:
```bash
cat .env
# Look for:
# - Missing quotes around values with spaces
# - Extra spaces around =
# - Comments starting with #
```

### Database Connection Errors

**Test connection**:
```bash
psql $DATABASE_URL
```

**Check URL format**:
```
postgresql://user:password@host:port/database
```

### Stripe Not Working

**Verify keys**:
- Test keys start with `pk_test_` and `sk_test_`
- Live keys start with `pk_live_` and `sk_live_`
- Don't mix test and live keys

**Check webhook secret**:
```bash
stripe listen --print-secret
```

### Email Not Sending

**Check Resend API key**:
- Log in to Resend dashboard
- Verify API key is active
- Check domain is verified (production)

**Test email**:
```python
from event_management.utils.email_service import send_email

send_email(
    to_email='test@example.com',
    subject='Test',
    body='Test email',
    notification_type='test'
)
```

## References

- [Django Settings](https://docs.djangoproject.com/en/5.0/ref/settings/)
- [python-decouple](https://github.com/henriquebastos/python-decouple)
- [Stripe API Keys](https://stripe.com/docs/keys)
- [Resend Documentation](https://resend.com/docs)
