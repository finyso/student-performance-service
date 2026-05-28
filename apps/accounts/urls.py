from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # Basic
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('rating/', views.rating_list, name='rating_list'),
    
    # Student
    path('my-group/', views.group_list, name='group_list'),
    path('penalties/', views.penalties_list, name='penalties_list'),
    path('announcements/', views.student_announcements, name='student_announcements'),
    
    # Headman
    path('headman/attendance/', views.headman_attendance, name='headman_attendance'),
    
    # Curator
    path('curator/announcements/', views.curator_announcements, name='curator_announcements'),
    path('curator/group/', views.curator_group_students, name='curator_group_students'),
    
    # Admin (изменено чтобы не конфликтовать с /admin/)
    path('control/penalties/', views.admin_penalties, name='admin_penalties'),
    path('control/all-grades/', views.admin_all_grades, name='admin_all_grades'),
    path('control/all-schedule/', views.admin_all_schedule, name='admin_all_schedule'),
    path('control/attendance/', views.admin_attendance, name='admin_attendance'),
]