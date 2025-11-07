# Production Deployment Guide

This guide covers deploying the Event Management System to production environments.

## Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] Code reviewed and merged to main branch
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] SSL/TLS certificates ready
- [ ] Backup strategy in place
- [ ] Monitoring tools configured
- [ ] Stripe webhooks configured
- [ ] Resend domain verified
- [ ] Static files collected

## Environment Configuration

### Required Environment Variables

```env
# Django Core
SECRET_KEY=your-production-secret-key-min-50-characters-random
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Stripe
STRIPE_PUBLIC_KEY=pk_live_your_live_public_key
STRIPE_SECRET_KEY=sk_live_your_live_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Resend
RESEND_API_KEY=re_your_production_api_key
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

### Generating Production SECRET_KEY

```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## Database Setup (PostgreSQL)

### 1. Create Production Database

```sql
CREATE DATABASE event_management_prod;
CREATE USER event_user WITH PASSWORD 'strong_password_here';
ALTER ROLE event_user SET client_encoding TO 'utf8';
ALTER ROLE event_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE event_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE event_management_prod TO event_user;
```

### 2. Run Migrations

```bash
python manage.py migrate --no-input
```

### 3. Create Superuser

```bash
python manage.py createsuperuser --email admin@yourdomain.com --username admin
```

### 4. Database Backups

Set up automated backups:

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"
pg_dump -U event_user -h localhost event_management_prod > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup_script.sh
```

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "event_management.wsgi:application"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: event_management
      POSTGRES_USER: event_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: always

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 --workers 3 event_management.wsgi:application
    volumes:
      - ./media:/app/media
      - ./static:/app/static
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://event_user:${DB_PASSWORD}@db:5432/event_management
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - RESEND_API_KEY=${RESEND_API_KEY}
    depends_on:
      - db
    restart: always

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/static
      - ./media:/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
```

#### 3. Deploy with Docker

```bash
# Build and start
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Option 2: Traditional Server Deployment

#### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    supervisor
```

#### 2. Setup Application

```bash
# Clone repository
cd /var/www
git clone <repository-url> event-management
cd event-management

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Setup environment variables
cp .env.example .env
nano .env  # Edit with production values
```

#### 3. Configure Gunicorn

Create `/etc/supervisor/conf.d/event-management.conf`:

```ini
[program:event-management]
directory=/var/www/event-management
command=/var/www/event-management/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/event-management/gunicorn.sock \
    event_management.wsgi:application
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/event-management/gunicorn.err.log
stdout_logfile=/var/log/event-management/gunicorn.out.log

[group:event-management]
programs=event-management
```

Start Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start event-management
```

#### 4. Configure Nginx

Create `/etc/nginx/sites-available/event-management`:

```nginx
upstream event_management {
    server unix:/var/www/event-management/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/event-management/static/;
    }

    location /media/ {
        alias /var/www/event-management/media/;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://event_management;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/event-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 3: Platform as a Service (PaaS)

#### Heroku

1. **Install Heroku CLI**:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

2. **Create Procfile**:
```
web: gunicorn event_management.wsgi
release: python manage.py migrate
```

3. **Create runtime.txt**:
```
python-3.11.0
```

4. **Deploy**:
```bash
heroku login
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set STRIPE_SECRET_KEY="sk_live_..."
heroku config:set RESEND_API_KEY="re_..."
git push heroku main
heroku run python manage.py createsuperuser
```

#### AWS Elastic Beanstalk

1. **Install EB CLI**:
```bash
pip install awsebcli
```

2. **Initialize EB**:
```bash
eb init -p python-3.11 event-management
```

3. **Create environment**:
```bash
eb create event-management-prod
```

4. **Configure environment variables**:
```bash
eb setenv SECRET_KEY="..." STRIPE_SECRET_KEY="..." RESEND_API_KEY="..."
```

5. **Deploy**:
```bash
eb deploy
```

#### DigitalOcean App Platform

1. **Create app.yaml**:
```yaml
name: event-management
services:
- name: web
  github:
    repo: your-username/event-management
    branch: main
  build_command: pip install -r requirements.txt
  run_command: gunicorn --worker-tmp-dir /dev/shm event_management.wsgi
  envs:
  - key: SECRET_KEY
    value: ${SECRET_KEY}
  - key: STRIPE_SECRET_KEY
    value: ${STRIPE_SECRET_KEY}
  http_port: 8000
databases:
- name: db
  engine: PG
  version: "15"
```

2. **Deploy via CLI or web interface**

## Static Files

### Collect Static Files

```bash
python manage.py collectstatic --no-input
```

### Serve via CDN (Optional)

Configure AWS S3 + CloudFront:

```python
# settings.py
if not DEBUG:
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

## SSL/TLS Configuration

### Using Let's Encrypt (Free)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

Auto-renewal:
```bash
sudo certbot renew --dry-run
```

### Manual SSL Certificate

1. Place certificate files:
   - `/etc/ssl/certs/yourdomain.crt`
   - `/etc/ssl/private/yourdomain.key`

2. Update nginx configuration with paths

## Stripe Webhook Configuration

### 1. Create Webhook Endpoint

In Stripe Dashboard:
- Go to Developers → Webhooks
- Add endpoint: `https://api.yourdomain.com/api/webhooks/stripe/`
- Select events:
  - `payment_intent.succeeded`
  - `payment_intent.payment_failed`
  - `charge.refunded`

### 2. Update Environment Variable

```env
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret
```

### 3. Test Webhook

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Forward to local
stripe listen --forward-to localhost:8000/api/webhooks/stripe/
```

## Resend Email Configuration

### 1. Verify Domain

In Resend Dashboard:
- Add your domain
- Add DNS records (SPF, DKIM, DMARC)
- Verify domain

### 2. Update Configuration

```env
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
RESEND_API_KEY=re_your_production_key
```

## Monitoring & Logging

### Application Logging

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
            'filename': '/var/log/event-management/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}
```

### Monitoring Tools

**Sentry** (Error Tracking):
```bash
pip install sentry-sdk
```

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    environment="production"
)
```

**New Relic** (APM):
```bash
pip install newrelic
newrelic-admin generate-config YOUR_LICENSE_KEY newrelic.ini
```

```bash
# Start with New Relic
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn ...
```

## Performance Optimization

### 1. Enable Database Connection Pooling

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}
```

### 2. Configure Caching (Redis)

```bash
# Install Redis
sudo apt-get install redis-server
pip install redis django-redis
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. Enable Gzip Compression

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    # ... other middleware
]
```

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Database backed up
- [ ] Environment variables set
- [ ] Static files collected

### Deployment
- [ ] Deploy application code
- [ ] Run database migrations
- [ ] Restart application server
- [ ] Clear cache (if applicable)
- [ ] Verify deployment

### Post-Deployment
- [ ] Test critical flows (login, ticket purchase)
- [ ] Check error logs
- [ ] Verify Stripe webhooks working
- [ ] Test email sending
- [ ] Monitor performance metrics

## Rollback Procedure

If deployment fails:

```bash
# Docker
docker-compose down
git checkout previous-working-commit
docker-compose up -d

# Traditional
sudo supervisorctl stop event-management
cd /var/www/event-management
git checkout previous-working-commit
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
sudo supervisorctl start event-management
```

## Security Hardening

### 1. Django Security Settings

```python
# settings.py (production)
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 2. Database Security

- Use strong passwords
- Enable SSL connections
- Restrict network access
- Regular backups
- Keep PostgreSQL updated

### 3. Server Security

```bash
# Enable firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# Keep system updated
sudo apt-get update && sudo apt-get upgrade
```

## Maintenance

### Regular Tasks

**Daily**:
- Monitor error logs
- Check disk space
- Verify backups

**Weekly**:
- Review performance metrics
- Check security updates
- Test backup restoration

**Monthly**:
- Update dependencies
- Review access logs
- Security audit

### Updating Application

```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Restart application
sudo supervisorctl restart event-management
```

## Troubleshooting

### Application won't start
```bash
# Check logs
sudo tail -f /var/log/event-management/gunicorn.err.log

# Check environment
cat .env

# Test Django
python manage.py check --deploy
```

### Database connection errors
```bash
# Test connection
psql -U event_user -h localhost event_management_prod

# Check Django can connect
python manage.py dbshell
```

### Static files not loading
```bash
# Collect again
python manage.py collectstatic --clear --no-input

# Check nginx config
sudo nginx -t

# Check permissions
sudo chown -R www-data:www-data /var/www/event-management
```

## Support

For deployment issues:
- Check [Installation Guide](installation.md)
- Review [Configuration Guide](configuration.md)
- Create an issue on GitHub
