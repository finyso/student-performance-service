from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:user_id>/', views.chat_room, name='chat_room'),
    path('chat/users/available/', views.get_available_users, name='available_users'),
]