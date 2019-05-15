from rest_framework.permissions import BasePermission


class IsSender(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        submission_id = view.kwargs['submission_id']

        return user.submissions.filter(pk=submission_id).exists()


class IsHimself(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        user_id = view.kwargs['user_id']

        return user.id == user_id


class RestrictedByTypeAndFieldPermission(BasePermission):

    def has_permission(self, request, view):
        if not hasattr(self, 'ALLOWED_TYPES_AND_FIELDS'):
            raise Exception("ALLOWED_TYPES_AND_FIELDS static dictionary must be specified on a permissions class")

        if request.method not in self.ALLOWED_TYPES_AND_FIELDS:
            raise Exception(f"Method {request.method} was not provided in ALLOWED_TYPES_AND_FIELDS attribute")

        allowed_fields = self.ALLOWED_TYPES_AND_FIELDS[request.method]

        # Every request field must be presented in ALLOWED_TYPES_AND_FIELDS according to specific request method
        if all(field in allowed_fields for field in request.data.keys()):
            return True

        return False


class UpdateSubmissionReviewer(RestrictedByTypeAndFieldPermission):

    ALLOWED_TYPES_AND_FIELDS = {
        'PATCH': ['reviewer']
    }
