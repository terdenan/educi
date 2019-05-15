from django.urls import path

from .views import RegistrationAPI, UserDetailView

app_name = 'users'
urlpatterns = [
    path('detail/', UserDetailView.as_view(), name='detail'),
    path('register/', RegistrationAPI.as_view(), name='register'),
]

