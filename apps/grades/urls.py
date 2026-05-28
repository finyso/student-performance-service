from django.urls import path
from . import views

urlpatterns = [
    path('gradebook/', views.gradebook_view, name='gradebook_view'),
    path('teacher/gradebook/', views.teacher_gradebook, name='teacher_gradebook'),
    path('teacher/gradebook/<int:subject_id>/', views.teacher_gradebook, name='teacher_gradebook'),
    path('teacher/grade/add/<int:student_id>/<int:subject_id>/', views.add_grade, name='add_grade'),
    path('statistics/', views.student_statistics, name='student_statistics'),
]