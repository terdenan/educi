from rest_framework import permissions

from courses.models import Course, Membership


class IsCourseStaff(permissions.BasePermission):

    def has_permission(self, request, view):
        # NOTE: The teacher can perform all CRUD operations while the TA
        # can only perform read operations.
        # TODO: One additional query to the DB. Is there any better way?
        course_id = view.kwargs['pk']
        course_member = Membership.objects.\
            filter(course__id=course_id, user=request.user).\
            first()
        if not course_member:
            return False
        course_role = course_member.role
        if course_role == Membership.TEACHER:
            return True
        elif course_role == Membership.TA and request.method in permissions.SAFE_METHODS:
            return True
        else:
            return False


class RoleBasedPermission(permissions.BasePermission):
    ROLE = None

    def has_permission(self, request, view):
        course_id = view.kwargs['pk']
        course = Course.objects.get(pk=course_id)
        return self.ROLE == course.get_role(request.user)


class IsTeacher(RoleBasedPermission):
    ROLE = Membership.TEACHER


class IsTA(RoleBasedPermission):
    ROLE = Membership.TA


class IsStudent(RoleBasedPermission):
    ROLE = Membership.STUDENT


class IsMember(permissions.BasePermission):

    def has_permission(self, request, view):
        course_id = view.kwargs['pk']
        user_id = request.user.id
        course = Course.objects.get(pk=course_id)

        return course.has_member(user_id)


class IsRequester(permissions.BasePermission):

    def has_permission(self, request, view):
        user_id = view.kwargs['user_id']
        return request.user.id == user_id
