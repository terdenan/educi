from django.urls import path

from .views import RuleListCreateAPIView, RuleRetrieveUpdateDestroyAPIView, move


app_name = 'build_rules'
urlpatterns = [
    path(
        route='rules/',
        view=RuleListCreateAPIView.as_view(),
        name='list'
    ),
    path(
        route='rules/<int:rule_id>/',
        view=RuleRetrieveUpdateDestroyAPIView.as_view(),
        name='detail'
    ),
    path(
        route='rules/<int:rule_id>/move/',
        view=move,
        name='move'
    ),
]
