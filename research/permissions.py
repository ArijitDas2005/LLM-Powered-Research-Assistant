from rest_framework.permissions import BasePermission


class CanCreateResearchReport(BasePermission):
    message = 'Monthly report limit reached for the free tier.'

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        user = request.user
        return bool(user and user.is_authenticated and user.can_create_report())
