from django.urls import path
from . import views

urlpatterns = [
    path('assignments/', views.assignments_list, name='assignments_list'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/assignments/create/', views.assignment_create, name='assignment_create'),
    path('teacher/assignments/<int:assignment_id>/edit/', views.assignment_edit, name='assignment_edit'),
    path('teacher/assignments/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('teacher/submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
]