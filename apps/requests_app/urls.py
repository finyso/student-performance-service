from django.urls import path
from . import views

urlpatterns = [
    path('my-requests/', views.requests_list, name='requests_list'),
    path('my-requests/create/', views.request_create, name='request_create'),
    path('my-requests/<int:request_id>/', views.request_detail, name='request_detail'),
    path('control/requests/', views.admin_requests, name='admin_requests'),  # Изменено
    path('control/requests/<int:request_id>/process/', views.process_request, name='process_request'),  # Изменено
]