from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView, LoginView, VerifyEmailView, UserProfileView,
    ChangePasswordView, FollowUserView, UserFollowersView, UserFollowingView
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),

    # Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Follow/Unfollow
    path('follow/<int:user_id>/', FollowUserView.as_view(), name='follow-user'),
    path('followers/', UserFollowersView.as_view(), name='my-followers'),
    path('followers/<int:user_id>/', UserFollowersView.as_view(), name='user-followers'),
    path('following/', UserFollowingView.as_view(), name='my-following'),
    path('following/<int:user_id>/', UserFollowingView.as_view(), name='user-following'),
]
