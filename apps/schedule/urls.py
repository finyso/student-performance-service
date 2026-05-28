from django.urls import path
from . import views

urlpatterns = [
    path('schedule/', views.schedule_view, name='schedule_view'),
    path('teacher/attendance/', views.teacher_attendance, name='teacher_attendance'),
    path('teacher/attendance/<int:schedule_id>/<str:date_str>/', views.teacher_attendance, name='teacher_attendance_date'),
    path('teacher/attendance/date/<str:date_str>/', views.teacher_attendance_by_date, name='teacher_attendance_by_date'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
]