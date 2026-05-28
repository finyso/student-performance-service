from django.shortcuts import render, redirect  # Добавлен redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from apps.accounts.models import Grade, Attendance, StudentProfile, Group, Subject, Assignment, AssignmentSubmission
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import json

@login_required
def analytics_dashboard(request):
    """Дашборд аналитики"""
    if request.user.role not in ['teacher', 'admin'] and not request.user.is_superuser:
        context = get_student_analytics(request)
        return render(request, 'analytics/student_analytics.html', context)
    
    # Аналитика для преподавателя/админа
    context = get_teacher_analytics(request)
    return render(request, 'analytics/teacher_analytics.html', context)


def get_student_analytics(request):
    """Аналитика для студента"""
    if not hasattr(request.user, 'student_profile'):
        return {}
    
    student = request.user.student_profile
    
    # Успеваемость по семестрам
    semester_data = {}
    for semester in range(1, 9):
        grades = Grade.objects.filter(student=student, subject__semester=semester)
        if grades.exists():
            semester_data[semester] = {
                'avg': round(grades.aggregate(Avg('value'))['value__avg'] or 0, 2),
                'count': grades.count(),
                'excellent': grades.filter(value__gte=9).count(),
                'good': grades.filter(value__gte=7, value__lte=8).count(),
                'satisfactory': grades.filter(value__gte=5, value__lte=6).count(),
            }
    
    # График динамики успеваемости
    grades_list = Grade.objects.filter(student=student).order_by('created_at')
    grades_over_time = []
    dates = []
    cumulative_avg = 0
    count = 0
    for grade in grades_list:
        count += 1
        cumulative_avg = (cumulative_avg * (count - 1) + grade.value) / count
        grades_over_time.append(round(cumulative_avg, 1))
        dates.append(grade.created_at.strftime('%d.%m'))
    
    # Генерируем график динамики успеваемости
    grades_trend_chart = generate_grades_trend_chart(dates, grades_over_time)
    
    # Генерируем график распределения оценок
    grade_dist = {
        '5-6': Grade.objects.filter(student=student, value__gte=5, value__lte=6).count(),
        '7-8': Grade.objects.filter(student=student, value__gte=7, value__lte=8).count(),
        '9-10': Grade.objects.filter(student=student, value__gte=9).count(),
    }
    grade_dist_chart = generate_grade_distribution_chart(grade_dist)
    
    # Прогресс по предметам
    subject_progress = []
    if student.group:
        subjects = student.group.subjects.all()
        for subject in subjects[:5]:
            grades = Grade.objects.filter(student=student, subject=subject)
            if grades.exists():
                avg = grades.aggregate(Avg('value'))['value__avg'] or 0
                subject_progress.append({
                    'name': subject.name[:20],
                    'avg': round(avg, 1)
                })
    subject_chart = generate_subject_progress_chart(subject_progress)
    
    context = {
        'student': student,
        'semester_data': semester_data,
        'grades_trend_chart': grades_trend_chart,
        'grade_dist_chart': grade_dist_chart,
        'subject_chart': subject_chart,
        'total_grades': Grade.objects.filter(student=student).count(),
        'avg_grade': round(Grade.objects.filter(student=student).aggregate(Avg('value'))['value__avg'] or 0, 2),
        'total_attendances': Attendance.objects.filter(student=student).count(),
        'attendance_rate': round(Attendance.objects.filter(student=student, status='present').count() / max(Attendance.objects.filter(student=student).count(), 1) * 100, 1),
    }
    return context


def get_teacher_analytics(request):
    """Аналитика для преподавателя"""
    
    if request.user.is_superuser:
        subjects = Subject.objects.all()
        groups = Group.objects.all()
    else:
        subjects = Subject.objects.filter(teacher=request.user)
        groups = Group.objects.filter(subjects__in=subjects).distinct()
    
    # Общая статистика
    total_students = StudentProfile.objects.filter(group__in=groups).count()
    total_grades = Grade.objects.filter(subject__in=subjects).count()
    avg_grade_overall = Grade.objects.filter(subject__in=subjects).aggregate(Avg('value'))['value__avg'] or 0
    
    # Данные для графиков
    group_labels = []
    group_data = []
    for group in groups:
        students = StudentProfile.objects.filter(group=group)
        group_grades = Grade.objects.filter(subject__in=subjects, student__in=students)
        avg = group_grades.aggregate(Avg('value'))['value__avg'] or 0
        group_labels.append(group.name)
        group_data.append(round(avg, 1))
    
    subject_labels = []
    subject_data = []
    for subject in subjects:
        grades = Grade.objects.filter(subject=subject)
        avg = grades.aggregate(Avg('value'))['value__avg'] or 0
        subject_labels.append(subject.name[:15])
        subject_data.append(round(avg, 1))
    
    grade_dist = {
        'excellent': Grade.objects.filter(subject__in=subjects, value__gte=9).count(),
        'good': Grade.objects.filter(subject__in=subjects, value__gte=7, value__lte=8).count(),
        'satisfactory': Grade.objects.filter(subject__in=subjects, value__gte=5, value__lte=6).count(),
        'unsatisfactory': Grade.objects.filter(subject__in=subjects, value__lt=5, value__gt=0).count(),
    }
    
    # Генерируем графики
    group_chart = generate_group_chart(group_labels, group_data)
    subject_chart = generate_subject_chart(subject_labels, subject_data)
    grade_dist_chart = generate_teacher_grade_dist_chart(grade_dist)
    
    # Топ студентов
    top_students = []
    for student in StudentProfile.objects.filter(group__in=groups):
        avg = Grade.objects.filter(subject__in=subjects, student=student).aggregate(Avg('value'))['value__avg'] or 0
        if avg > 0:
            top_students.append({
                'name': student.user.get_full_name(),
                'group': student.group.name if student.group else '-',
                'avg': round(avg, 2)
            })
    top_students = sorted(top_students, key=lambda x: x['avg'], reverse=True)[:10]
    
    context = {
        'total_students': total_students,
        'total_grades': total_grades,
        'avg_grade_overall': round(avg_grade_overall, 2),
        'top_students': top_students,
        'group_chart': group_chart,
        'subject_chart': subject_chart,
        'grade_dist_chart': grade_dist_chart,
    }
    return context


def generate_grades_trend_chart(dates, values):
    """График динамики успеваемости"""
    if not dates or not values:
        return ""
    
    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, marker='o', linewidth=2, markersize=4, color='#667eea')
    plt.fill_between(range(len(values)), values, alpha=0.3, color='#667eea')
    plt.title('Динамика среднего балла', fontsize=14, fontweight='bold')
    plt.xlabel('Дата', fontsize=12)
    plt.ylabel('Средний балл', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')


def generate_grade_distribution_chart(distribution):
    """Круговая диаграмма распределения оценок для студента"""
    labels = ['5-6 (Удовл.)', '7-8 (Хор.)', '9-10 (Отл.)']
    sizes = [distribution['5-6'], distribution['7-8'], distribution['9-10']]
    colors = ['#ffc107', '#2196f3', '#4caf50']
    
    if sum(sizes) == 0:
        return ""
    
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Распределение оценок', fontsize=14, fontweight='bold')
    plt.axis('equal')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')


def generate_subject_progress_chart(subjects):
    """График прогресса по предметам"""
    if not subjects:
        return ""
    
    names = [s['name'] for s in subjects]
    avgs = [s['avg'] for s in subjects]
    
    plt.figure(figsize=(10, 5))
    bars = plt.bar(names, avgs, color='#9c27b0', edgecolor='#6a1b9a', linewidth=1)
    plt.title('Средний балл по предметам', fontsize=14, fontweight='bold')
    plt.xlabel('Предметы', fontsize=12)
    plt.ylabel('Средний балл', fontsize=12)
    plt.ylim(0, 10)
    plt.xticks(rotation=45, ha='right')
    
    # Добавляем значения на столбцы
    for bar, val in zip(bars, avgs):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(val), ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')


def generate_group_chart(labels, data):
    """График успеваемости по группам"""
    if not labels or not data:
        return ""
    
    plt.figure(figsize=(10, 5))
    bars = plt.bar(labels, data, color='#667eea', edgecolor='#4c51bf', linewidth=1)
    plt.title('Средний балл по группам', fontsize=14, fontweight='bold')
    plt.xlabel('Группы', fontsize=12)
    plt.ylabel('Средний балл', fontsize=12)
    plt.ylim(0, 10)
    
    for bar, val in zip(bars, data):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(val), ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')


def generate_subject_chart(labels, data):
    """График успеваемости по предметам"""
    if not labels or not data:
        return ""
    
    plt.figure(figsize=(12, 5))
    bars = plt.bar(labels, data, color='#4caf50', edgecolor='#2e7d32', linewidth=1)
    plt.title('Средний балл по предметам', fontsize=14, fontweight='bold')
    plt.xlabel('Предметы', fontsize=12)
    plt.ylabel('Средний балл', fontsize=12)
    plt.ylim(0, 10)
    plt.xticks(rotation=45, ha='right')
    
    for bar, val in zip(bars, data):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(val), ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')


def generate_teacher_grade_dist_chart(distribution):
    """Круговая диаграмма распределения оценок для преподавателя"""
    labels = ['Отлично (9-10)', 'Хорошо (7-8)', 'Удовл. (5-6)', 'Неуд. (<5)']
    sizes = [distribution['excellent'], distribution['good'], distribution['satisfactory'], distribution['unsatisfactory']]
    colors = ['#4caf50', '#2196f3', '#ffc107', '#f44336']
    
    if sum(sizes) == 0:
        return ""
    
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Распределение оценок', fontsize=14, fontweight='bold')
    plt.axis('equal')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')


@login_required
def export_grades(request):
    """Экспорт оценок в CSV"""
    import csv
    from django.http import HttpResponse
    
    if request.user.role != 'teacher' and not request.user.is_superuser:
        return redirect('home')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="grades_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Студент', 'Группа', 'Предмет', 'Оценка', 'Тип', 'Дата', 'Комментарий'])
    
    if request.user.is_superuser:
        grades = Grade.objects.all().select_related('student__user', 'student__group', 'subject')
    else:
        subjects = Subject.objects.filter(teacher=request.user)
        grades = Grade.objects.filter(subject__in=subjects).select_related('student__user', 'student__group', 'subject')
    
    for grade in grades:
        writer.writerow([
            grade.student.user.get_full_name(),
            grade.student.group.name if grade.student.group else '-',
            grade.subject.name,
            grade.value,
            grade.get_grade_type_display(),
            grade.created_at.strftime('%d.%m.%Y'),
            grade.comment or ''
        ])
    
    return response


@login_required
def export_attendance(request):
    """Экспорт посещаемости в CSV"""
    import csv
    from django.http import HttpResponse
    
    if request.user.role != 'teacher' and not request.user.is_superuser:
        return redirect('home')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Студент', 'Группа', 'Предмет', 'Дата', 'Статус', 'Комментарий'])
    
    if request.user.is_superuser:
        attendances = Attendance.objects.all().select_related('student__user', 'student__group', 'schedule__subject')
    else:
        subjects = Subject.objects.filter(teacher=request.user)
        attendances = Attendance.objects.filter(schedule__subject__in=subjects).select_related('student__user', 'student__group', 'schedule__subject')
    
    for att in attendances:
        writer.writerow([
            att.student.user.get_full_name(),
            att.student.group.name if att.student.group else '-',
            att.schedule.subject.name,
            att.date.strftime('%d.%m.%Y'),
            att.get_status_display(),
            att.comment or ''
        ])
    
    return response