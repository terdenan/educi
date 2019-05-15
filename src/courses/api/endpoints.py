from django.urls import path, include

from . import views


app_name = 'courses'
urlpatterns = [
    path(
        route='requests/',
        view=views.CourseCreationRequestListManageView.as_view(),
        name='request-list'
    ),

    path(
        route='',
        view=views.CourseListManageView.as_view(),
        name='list'
    ),
    path(
        route='<int:pk>/',
        view=views.CourseDetailManageView.as_view(),
        name='detail'
    ),

    path(
        route='<int:pk>/members/',
        view=views.CourseMembersListManageView.as_view(),
        name='members-list'
    ),
    path(
        route='<int:pk>/members/<int:user_id>/',
        view=views.CourseMembersRetrieveDestroyAPIView.as_view(),
        name='members-detail'
    ),

    path(
        route='<int:pk>/assignments/',
        view=views.CourseAssignmentListManageView.as_view(),
        name='assignments-list'
    ),
    path(
        route='<int:pk>/assignments/<int:assignment_id>/',
        view=views.CourseAssignmentDetailManageView.as_view(),
        name='assignments-detail'
    ),

    path(
        route='<int:pk>/',
        view=include('submissions.api.endpoints')
    ),
    path(
        route='<int:pk>/assignments/<int:assignment_id>/',
        view=include('build_rules.api.endpoints')
    ),

    path(
        route='<int:pk>/environments/',
        view=views.EnvironmentListManageView.as_view(),
        name='environment-list'
    ),
    path(
        route='<int:pk>/environments/<environment_id>/',
        view=views.EnvironmentRetrieveUpdateDestroyAPIView.as_view(),
        name='environment-detail'
    ),
    path(
        route='<int:pk>/attachments/',
        view=views.manage_attachments,
        name='attachments-list',
    ),
]
