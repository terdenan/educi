from django.urls import path

from . import views


app_name = 'submissions'
urlpatterns = [
    path('submissions/', views.SubmissionListManageView.as_view(), name='list'),
    path('submissions/<int:submission_id>/', views.SubmissionDetailManageView.as_view(), name='detail'),
    path('users/<int:user_id>/submissions/', views.UserSubmissionsListManageView.as_view(), name='user-list')
]
