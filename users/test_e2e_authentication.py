"""
End-to-End Tests for User Authentication Flow
Tests the complete user journey from registration to authentication
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from users.models import Follow

User = get_user_model()


class UserAuthenticationE2ETest(TestCase):
    """E2E tests for user authentication flow"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/users/register/'
        self.login_url = '/api/users/login/'
        self.verify_email_url = '/api/users/verify-email/'
        self.profile_url = '/api/users/profile/'
        self.change_password_url = '/api/users/change-password/'

    def test_complete_user_registration_and_login_flow(self):
        """Test complete user registration, email verification, and login flow"""

        # Step 1: Register a new user
        registration_data = {
            'email': 'testuser@example.com',
            'username': 'testuser',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'attendee'
        }

        response = self.client.post(self.register_url, registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')

        # Verify user was created in database
        user = User.objects.get(email='testuser@example.com')
        self.assertIsNotNone(user)
        self.assertFalse(user.is_email_verified)
        self.assertIsNotNone(user.email_verification_token)

        # Step 2: Verify email
        verification_token = user.email_verification_token
        verify_data = {'token': verification_token}

        response = self.client.post(self.verify_email_url, verify_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify user is now verified
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertIsNone(user.email_verification_token)

        # Step 3: Login with credentials
        login_data = {
            'email': 'testuser@example.com',
            'password': 'TestPass123!'
        }

        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

        access_token = response.data['tokens']['access']

        # Step 4: Access protected endpoint with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'testuser@example.com')

    def test_registration_validation_errors(self):
        """Test registration with invalid data"""

        # Test password mismatch
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'TestPass123!',
            'password2': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'attendee'
        }

        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test duplicate email
        User.objects.create_user(
            email='existing@example.com',
            username='existing',
            password='TestPass123!'
        )

        data = {
            'email': 'existing@example.com',
            'username': 'newuser',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'attendee'
        }

        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_invalid_credentials(self):
        """Test login with wrong credentials"""

        # Create a user
        User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='CorrectPass123!'
        )

        # Try to login with wrong password
        login_data = {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }

        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update_flow(self):
        """Test updating user profile"""

        # Create and authenticate user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!',
            first_name='Old',
            last_name='Name'
        )

        self.client.force_authenticate(user=user)

        # Update profile
        update_data = {
            'first_name': 'New',
            'last_name': 'Name',
            'bio': 'This is my bio',
            'phone': '+1234567890'
        }

        response = self.client.put(self.profile_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify changes
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.bio, 'This is my bio')
        self.assertEqual(user.phone, '+1234567890')

    def test_change_password_flow(self):
        """Test password change functionality"""

        # Create and authenticate user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='OldPass123!'
        )

        self.client.force_authenticate(user=user)

        # Change password
        password_data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password2': 'NewPass123!'
        }

        response = self.client.post(self.change_password_url, password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify new password works
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPass123!'))

        # Verify old password doesn't work anymore
        self.assertFalse(user.check_password('OldPass123!'))


class UserFollowSystemE2ETest(TestCase):
    """E2E tests for follow/unfollow functionality"""

    def setUp(self):
        self.client = APIClient()

        # Create users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='TestPass123!',
            first_name='User',
            last_name='One'
        )

        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='TestPass123!',
            first_name='User',
            last_name='Two',
            role='organizer'
        )

    def test_complete_follow_unfollow_flow(self):
        """Test following and unfollowing a user"""

        self.client.force_authenticate(user=self.user1)

        # Step 1: Follow a user
        follow_url = f'/api/users/follow/{self.user2.id}/'
        response = self.client.post(follow_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify follow relationship exists
        follow_exists = Follow.objects.filter(
            follower=self.user1,
            following=self.user2
        ).exists()
        self.assertTrue(follow_exists)

        # Step 2: Check following list
        following_url = '/api/users/following/'
        response = self.client.get(following_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Step 3: Unfollow the user
        response = self.client.delete(follow_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify follow relationship no longer exists
        follow_exists = Follow.objects.filter(
            follower=self.user1,
            following=self.user2
        ).exists()
        self.assertFalse(follow_exists)

    def test_cannot_follow_self(self):
        """Test that user cannot follow themselves"""

        self.client.force_authenticate(user=self.user1)

        follow_url = f'/api/users/follow/{self.user1.id}/'
        response = self.client.post(follow_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_followers_list(self):
        """Test viewing followers list"""

        # User2 and User1 follow organizer (create another user)
        organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='TestPass123!',
            role='organizer'
        )

        Follow.objects.create(follower=self.user1, following=organizer)
        Follow.objects.create(follower=self.user2, following=organizer)

        self.client.force_authenticate(user=organizer)

        followers_url = '/api/users/followers/'
        response = self.client.get(followers_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class UserRoleBasedAccessE2ETest(TestCase):
    """E2E tests for role-based access control"""

    def setUp(self):
        self.client = APIClient()

        self.attendee = User.objects.create_user(
            email='attendee@example.com',
            username='attendee',
            password='TestPass123!',
            role='attendee'
        )

        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='TestPass123!',
            role='organizer'
        )

        self.vendor = User.objects.create_user(
            email='vendor@example.com',
            username='vendor',
            password='TestPass123!',
            role='vendor'
        )

    def test_users_have_correct_roles(self):
        """Test that users are created with correct roles"""

        self.assertEqual(self.attendee.role, 'attendee')
        self.assertEqual(self.organizer.role, 'organizer')
        self.assertEqual(self.vendor.role, 'vendor')

    def test_user_can_access_own_profile(self):
        """Test that any authenticated user can access their profile"""

        for user in [self.attendee, self.organizer, self.vendor]:
            self.client.force_authenticate(user=user)
            response = self.client.get('/api/users/profile/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['role'], user.role)
