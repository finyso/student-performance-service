from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:user_id>/', views.chat_room, name='chat_room'),
    path('chat/users/available/', views.get_available_users, name='available_users'),
    path('chat/api/messages/<int:room_id>/', views.api_get_messages, name='api_get_messages'),
    path('chat/api/send/', views.api_send_message, name='api_send_message'),
]