# Testing Documentation

This document describes the comprehensive End-to-End (E2E) testing strategy for the Event Management System.

## Overview

The test suite provides confidence in the core implementation through automated testing of critical user journeys and workflows. Tests run automatically on GitHub Actions for every push and pull request.

## Test Categories

### 1. Authentication Tests (`users/test_e2e_authentication.py`)

**Coverage:**
- Complete user registration flow with email verification
- Login and JWT token generation
- Profile management and updates
- Password change functionality
- Follow/unfollow system
- Role-based access control

**Key Test Scenarios:**
- ✅ User can register, verify email, and login
- ✅ Invalid credentials are rejected
- ✅ Users can update their profiles
- ✅ Password changes work correctly
- ✅ Follow/unfollow relationships function properly
- ✅ Role-based permissions are enforced

### 2. Event Management Tests (`events/test_e2e_events.py`)

**Coverage:**
- Event creation and publication workflow
- Event listing with filtering and search
- Event favorites/bookmarks
- Comment and Q&A system
- View count tracking
- Organizer permissions

**Key Test Scenarios:**
- ✅ Organizers can create and publish events
- ✅ Events can be filtered by city, category, date
- ✅ Search functionality works correctly
- ✅ View counts are tracked accurately
- ✅ Only organizers can edit their own events
- ✅ Attendees cannot create events
- ✅ Comments and replies work correctly

### 3. Ticketing Tests (`tickets/test_e2e_ticketing.py`)

**Coverage:**
- Complete ticket purchase flow (with mocked Stripe)
- Multiple ticket type support
- QR code generation
- Check-in system
- Ticket availability tracking
- Refund requests

**Key Test Scenarios:**
- ✅ Users can purchase tickets successfully
- ✅ Payment integration works (mocked)
- ✅ QR codes are generated for tickets
- ✅ Check-in system validates tickets
- ✅ Duplicate check-ins are prevented
- ✅ Sold-out tickets cannot be purchased
- ✅ Ticket quantities are tracked correctly

### 4. Food Ordering Tests (`tests/test_e2e_integration.py`)

**Coverage:**
- Menu browsing
- Food and drink ordering flow
- Order with multiple items
- Dietary filtering (vegetarian, vegan, etc.)
- Stock management
- Table number assignment

**Key Test Scenarios:**
- ✅ Users can browse available menus
- ✅ Complete food order with multiple items
- ✅ Unavailable items cannot be ordered
- ✅ Special instructions are captured
- ✅ Payment processing works (mocked)
- ✅ Dietary preferences can be filtered

### 5. Review System Tests (`tests/test_e2e_integration.py`)

**Coverage:**
- Review submission
- Rating validation (1-5 stars)
- Review editing
- One review per user per event
- Average rating calculation

**Key Test Scenarios:**
- ✅ Users can submit reviews after events
- ✅ Ratings must be between 1 and 5
- ✅ Users can only review each event once
- ✅ Users can edit their own reviews
- ✅ Average ratings are calculated correctly

### 6. Complete User Journey (`tests/test_e2e_integration.py`)

**Coverage:**
- End-to-end user flow across multiple features
- Register → Browse → Buy Ticket → Order Food → Review

**Key Test Scenario:**
- ✅ Complete attendee journey through the system

## Running Tests

### Run All Tests

```bash
python manage.py test
```

### Run Specific Test Suite

```bash
# Authentication tests only
python manage.py test users.test_e2e_authentication

# Event management tests only
python manage.py test events.test_e2e_events

# Ticketing tests only
python manage.py test tickets.test_e2e_ticketing

# Integration tests only
python manage.py test tests.test_e2e_integration
```

### Run with Verbosity

```bash
python manage.py test --verbosity=2
```

### Run with Coverage

```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Run Specific Test Class

```bash
python manage.py test users.test_e2e_authentication.UserAuthenticationE2ETest
```

### Run Specific Test Method

```bash
python manage.py test users.test_e2e_authentication.UserAuthenticationE2ETest.test_complete_user_registration_and_login_flow
```

## GitHub Actions CI/CD

The test suite runs automatically on GitHub Actions for:
- Every push to `main`, `develop`, or `claude/**` branches
- Every pull request to `main` or `develop`

### Workflow Jobs

**1. Test Job**
- Runs on Python 3.10 and 3.11
- Uses PostgreSQL service for realistic testing
- Runs all E2E tests with coverage
- Uploads coverage reports to Codecov

**2. Lint Job**
- Runs flake8 for code quality
- Checks formatting with black
- Checks import sorting with isort

**3. Security Job**
- Runs safety check for dependency vulnerabilities
- Runs bandit for security issues

**4. Build Check Job**
- Verifies Django configuration
- Runs deployment checks
- Collects static files

### Viewing Test Results

1. Go to your repository on GitHub
2. Click on "Actions" tab
3. Click on the latest workflow run
4. View detailed test results and logs

## Test Patterns and Best Practices

### 1. Mocking External Services

External services (Stripe, Resend) are mocked in tests:

```python
@patch('event_management.utils.stripe_service.stripe.PaymentIntent.create')
def test_payment(self, mock_stripe):
    mock_stripe.return_value = {'id': 'pi_test_123', 'client_secret': 'secret'}
    # Test code here
```

### 2. Authentication in Tests

```python
# Force authenticate as specific user
self.client.force_authenticate(user=self.user)

# Test authenticated endpoint
response = self.client.get('/api/protected-endpoint/')
```

### 3. Test Data Setup

```python
def setUp(self):
    """Set up test data before each test"""
    self.user = User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='TestPass123!'
    )
```

### 4. Assertions

```python
# Status code assertions
self.assertEqual(response.status_code, status.HTTP_200_OK)

# Data assertions
self.assertIn('tokens', response.data)
self.assertEqual(response.data['email'], 'test@example.com')

# Database assertions
user.refresh_from_db()
self.assertTrue(user.is_email_verified)
```

## Test Coverage Goals

Current test coverage targets:
- **Overall**: 80%+ coverage
- **Critical paths**: 95%+ coverage (auth, payments, tickets)
- **Models**: 90%+ coverage
- **API endpoints**: 85%+ coverage

## Adding New Tests

When adding new features, follow this pattern:

1. **Create test file** in the appropriate app directory
   ```
   app_name/test_e2e_feature_name.py
   ```

2. **Structure your test class**
   ```python
   class FeatureE2ETest(TestCase):
       def setUp(self):
           # Set up test data
           pass

       def test_complete_feature_flow(self):
           # Test main user journey
           pass

       def test_validation_errors(self):
           # Test error cases
           pass
   ```

3. **Follow naming conventions**
   - Test files: `test_e2e_*.py`
   - Test classes: `*E2ETest` or `*TestCase`
   - Test methods: `test_*`

4. **Run your new tests**
   ```bash
   python manage.py test app_name.test_e2e_feature_name
   ```

## Continuous Improvement

### Test Maintenance

- Review and update tests when features change
- Remove obsolete tests
- Keep test data minimal but realistic
- Regularly check test execution time

### Monitoring Test Health

- **Failed tests**: Investigate immediately
- **Flaky tests**: Identify and fix root cause
- **Slow tests**: Optimize or mark as slow
- **Coverage drops**: Add tests for new code

## Debugging Failed Tests

### View Detailed Output

```bash
python manage.py test --verbosity=2 --debug-mode
```

### Run Single Failing Test

```bash
python manage.py test app.tests.TestClass.test_method
```

### Use Django Shell for Debugging

```bash
python manage.py shell
```

### Check Test Database

```python
from django.test import TestCase

class DebugTest(TestCase):
    def test_debug(self):
        # Add breakpoint
        import pdb; pdb.set_trace()
        # Test code here
```

## Environment Variables for Testing

Create a `.env.test` file for test-specific configuration:

```env
SECRET_KEY=test-secret-key
DEBUG=True
DATABASE_URL=sqlite:///test_db.sqlite3
STRIPE_SECRET_KEY=sk_test_fake_key
RESEND_API_KEY=re_test_fake_key
```

## Common Issues and Solutions

### Issue: Tests fail with database errors
**Solution**: Run migrations before tests
```bash
python manage.py migrate
python manage.py test
```

### Issue: Stripe tests fail
**Solution**: Ensure Stripe is properly mocked
```python
@patch('event_management.utils.stripe_service.stripe.PaymentIntent.create')
```

### Issue: Tests pass locally but fail in CI
**Solution**: Check environment variables and database configuration

### Issue: Tests are too slow
**Solution**: Use `--parallel` flag or optimize database queries
```bash
python manage.py test --parallel
```

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/5.0/topics/testing/)
- [DRF Testing Documentation](https://www.django-rest-framework.org/api-guide/testing/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Questions or Issues?

If you encounter issues with tests:
1. Check this documentation
2. Review test logs in GitHub Actions
3. Run tests locally with verbosity
4. Create an issue in the repository

---

**Remember**: Tests are living documentation. Keep them updated, clear, and comprehensive!
