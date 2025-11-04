from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Follow


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'bio', 'profile_picture', 'is_email_verified',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'is_email_verified', 'created_at', 'updated_at')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 'first_name', 'last_name', 'phone', 'role')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'bio', 'profile_picture')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm New Password')

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class FollowSerializer(serializers.ModelSerializer):
    """Serializer for Follow model"""
    follower_details = UserSerializer(source='follower', read_only=True)
    following_details = UserSerializer(source='following', read_only=True)

    class Meta:
        model = Follow
        fields = ('id', 'follower', 'following', 'follower_details', 'following_details', 'created_at')
        read_only_fields = ('id', 'created_at')
