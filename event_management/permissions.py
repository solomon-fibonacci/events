from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.user == request.user if hasattr(obj, 'user') else obj == request.user


class IsOrganizer(permissions.BasePermission):
    """
    Custom permission to only allow organizers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'organizer'


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow organizers to create/edit, others to read only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role == 'organizer'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user if hasattr(obj, 'organizer') else True


class IsEventOrganizer(permissions.BasePermission):
    """
    Custom permission to only allow event organizers to modify their events.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user


class IsVendor(permissions.BasePermission):
    """
    Custom permission to only allow vendors.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'vendor'


class IsVendorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow vendors to manage menus, others to read only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role in ['vendor', 'organizer']

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Check if user is the vendor or the event organizer
        if hasattr(obj, 'vendor'):
            return obj.vendor == request.user or obj.event.organizer == request.user
        if hasattr(obj, 'menu'):
            return obj.menu.vendor == request.user or obj.menu.event.organizer == request.user
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
