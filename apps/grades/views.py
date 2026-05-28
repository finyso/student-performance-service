from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.utils import timezone
from apps.notifications.utils import notify_about_grade
from apps.accounts.models import StudentProfile, Subject, Grade, SemesterGrade, User, Group

@login_required
def gradebook_view(request):
    """Зачётка студента"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут просматривать зачётку')
        return redirect('home')
    
    student = request.user.student_profile
    
    # Получаем предметы из группы студента
    if student.group:
        subjects = student.group.subjects.all()
    else:
        subjects = []
    
    # Получаем оценки по этим предметам
    grades = Grade.objects.filter(student=student, subject__in=subjects).select_related('subject')
    
    # Группировка по предметам
    subjects_grades = {}
    for grade in grades:
        if grade.subject not in subjects_grades:
            subjects_grades[grade.subject] = []
        subjects_grades[grade.subject].append(grade)
    
    # Добавляем предметы без оценок
    for subject in subjects:
        if subject not in subjects_grades:
            subjects_grades[subject] = []
    
    # Расчёт среднего балла
    all_grades = Grade.objects.filter(student=student)
    avg_grade = all_grades.aggregate(Avg('value'))['value__avg']
    
    context = {
        'student': student,
        'subjects_grades': subjects_grades,
        'avg_grade': round(avg_grade, 2) if avg_grade else 0,
        'grades_count': all_grades.count(),
    }
    return render(request, 'grades/gradebook.html', context)

@login_required
def teacher_gradebook(request, subject_id=None):
    """Журнал оценок для преподавателя"""
    if request.user.role != 'teacher' and not request.user.is_superuser:
        messages.error(request, 'Только преподаватели могут просматривать журнал')
        return redirect('home')
    
    # Получаем предметы преподавателя
    if request.user.is_superuser:
        subjects = Subject.objects.all()
    else:
        subjects = Subject.objects.filter(teacher=request.user)
    
    selected_subject = None
    students = []
    grades_data = {}
    
    if subject_id:
        selected_subject = get_object_or_404(Subject, id=subject_id)
        students = StudentProfile.objects.filter(group__in=selected_subject.groups.all()).distinct()
        
        # Получаем все оценки для этих студентов по выбранному предмету
        grades = Grade.objects.filter(subject=selected_subject, student__in=students)
        
        # Организуем данные для таблицы
        for student in students:
            grades_data[student.id] = {
                'student': student,
                'grades': {g.grade_type: g for g in grades if g.student.id == student.id},
                'avg': grades.filter(student=student).aggregate(Avg('value'))['value__avg'] or 0
            }
    
    context = {
        'subjects': subjects,
        'selected_subject': selected_subject,
        'grades_data': grades_data,
        'grade_types': Grade.GRADE_TYPES,
    }
    return render(request, 'grades/teacher_gradebook.html', context)


@login_required
def add_grade(request, student_id, subject_id):
    """Добавление оценки преподавателем"""
    if request.user.role != 'teacher' and not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    student = get_object_or_404(StudentProfile, id=student_id)
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Проверка, что преподаватель ведёт этот предмет
    if not request.user.is_superuser and subject.teacher != request.user:
        messages.error(request, 'Вы не ведёте этот предмет')
        return redirect('teacher_gradebook')
    
    # Предзаполнение типа работы из GET параметра
    preselected_type = request.GET.get('type', '')
    
    if request.method == 'POST':
        grade_value = request.POST.get('value')
        grade_type = request.POST.get('grade_type')
        comment = request.POST.get('comment', '')
        
        if not grade_value or not grade_type:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('add_grade', student_id=student.id, subject_id=subject.id)
        
        # Проверяем, существует ли уже такая оценка
        grade, created = Grade.objects.get_or_create(
            student=student,
            subject=subject,
            grade_type=grade_type,
            defaults={
                'value': grade_value,
                'comment': comment,
                'created_by': request.user
            }
        )
        
        if not created:
            # Обновляем существующую оценку
            grade.value = grade_value
            grade.comment = comment
            grade.created_by = request.user
            grade.save()
            messages.success(request, f'Оценка для {student.user.get_full_name()} обновлена')
        else:
            messages.success(request, f'Оценка для {student.user.get_full_name()} добавлена')
        
        notify_about_grade(grade)
        student.calculate_rating()

        return redirect('teacher_gradebook', subject_id=subject.id)
    
    context = {
        'student': student,
        'subject': subject,
        'grade_types': Grade.GRADE_TYPES,
        'grade_values': [(i, str(i)) for i in range(1, 11)],
        'preselected_type': preselected_type,
    }
    return render(request, 'grades/add_grade.html', context)

@login_required
def student_statistics(request):
    """Статистика успеваемости студента"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут просматривать статистику')
        return redirect('home')
    
    student = request.user.student_profile
    
    # Статистика по семестрам
    semester_stats = {}
    for semester in range(1, 9):
        grades = Grade.objects.filter(
            student=student,
            subject__semester=semester
        )
        if grades.exists():
            semester_stats[semester] = {
                'avg': grades.aggregate(Avg('value'))['value__avg'] or 0,
                'count': grades.count(),
                'excellent': grades.filter(value__gte=9).count(),
                'good': grades.filter(value__gte=7, value__lte=8).count(),
                'satisfactory': grades.filter(value__gte=5, value__lte=6).count(),
                'unsatisfactory': grades.filter(value__lt=5).count(),
            }
    
    # Статистика по типам работ
    type_stats = Grade.objects.filter(student=student).values('grade_type').annotate(
        avg=Avg('value'),
        count=Count('id')
    )
    
    context = {
        'student': student,
        'semester_stats': semester_stats,
        'type_stats': type_stats,
        'total_avg': Grade.objects.filter(student=student).aggregate(Avg('value'))['value__avg'] or 0,
        'total_count': Grade.objects.filter(student=student).count(),
    }
    return render(request, 'grades/student_statistics.html', context)