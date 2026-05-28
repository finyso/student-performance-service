from django.urls import path
from . import views

urlpatterns = [
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('export/grades/', views.export_grades, name='export_grades'),
    path('export/attendance/', views.export_attendance, name='export_attendance'),
]