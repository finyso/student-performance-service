from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from apps.accounts.models import Assignment, AssignmentSubmission, Subject, StudentProfile
from apps.notifications.utils import create_notification

@login_required
def assignments_list(request):
    """Список заданий для студента"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут просматривать задания')
        return redirect('home')
    
    student = request.user.student_profile
    group = student.group
    
    if group:
        subjects = group.subjects.all()
        assignments = Assignment.objects.filter(
            subject__in=subjects, 
            is_active=True
        ).order_by('deadline')
    else:
        assignments = Assignment.objects.none()
    
    # Получаем статусы сданных заданий
    submissions = {sub.assignment_id: sub for sub in AssignmentSubmission.objects.filter(student=student)}
    
    # Разделяем на активные и просроченные
    now = timezone.now()
    active_assignments = [a for a in assignments if a.deadline > now]
    overdue_assignments = [a for a in assignments if a.deadline <= now and a.id not in submissions]
    
    context = {
        'active_assignments': active_assignments,
        'overdue_assignments': overdue_assignments,
        'submissions': submissions,
    }
    return render(request, 'assignments/student_list.html', context)


@login_required
def assignment_detail(request, assignment_id):
    """Детали задания"""
    assignment = get_object_or_404(Assignment, id=assignment_id, is_active=True)
    
    # Проверка доступа для студента
    if hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
        if assignment.subject not in student.group.subjects.all():
            messages.error(request, 'У вас нет доступа к этому заданию')
            return redirect('assignments_list')
        
        try:
            submission = AssignmentSubmission.objects.get(assignment=assignment, student=student)
        except AssignmentSubmission.DoesNotExist:
            submission = None
    else:
        submission = None
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'is_overdue': assignment.is_overdue(),
    }
    return render(request, 'assignments/assignment_detail.html', context)


@login_required
def submit_assignment(request, assignment_id):
    """Сдача задания студентом"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут сдавать задания')
        return redirect('home')
    
    assignment = get_object_or_404(Assignment, id=assignment_id, is_active=True)
    student = request.user.student_profile
    
    # Проверка доступа
    if assignment.subject not in student.group.subjects.all():
        messages.error(request, 'У вас нет доступа к этому заданию')
        return redirect('assignments_list')
    
    # Проверка, не просрочено ли
    if assignment.is_overdue():
        messages.error(request, 'Дедлайн этого задания уже прошёл')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    # Получаем или создаём сдачу
    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=student,
        defaults={'status': 'draft'}
    )
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        attachment = request.FILES.get('attachment')
        action = request.POST.get('action')
        
        submission.content = content
        if attachment:
            submission.attachment = attachment
        
        if action == 'submit':
            submission.status = 'submitted'
            submission.submitted_at = timezone.now()
            messages.success(request, f'Задание "{assignment.title}" успешно сдано!')
            
            # Уведомление преподавателю
            if assignment.created_by:
                create_notification(
                    assignment.created_by,
                    'deadline',
                    f'Новая сдача задания: {assignment.title}',
                    f'Студент {student.user.get_full_name()} сдал задание "{assignment.title}"',
                    f'/teacher/assignments/{assignment.id}/submissions/'
                )
        else:
            submission.status = 'draft'
            messages.success(request, 'Черновик сохранён')
        
        submission.save()
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    context = {
        'assignment': assignment,
        'submission': submission,
    }
    return render(request, 'assignments/submit_form.html', context)


@login_required
def teacher_assignments(request):
    """Список заданий для преподавателя"""
    if request.user.role != 'teacher' and not request.user.is_superuser:
        messages.error(request, 'Только преподаватели могут просматривать эту страницу')
        return redirect('home')
    
    if request.user.is_superuser:
        assignments = Assignment.objects.all().order_by('-created_at')
    else:
        assignments = Assignment.objects.filter(created_by=request.user).order_by('-created_at')
    
    paginator = Paginator(assignments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'assignments': page_obj,
    }
    return render(request, 'assignments/teacher_list.html', context)


@login_required
def assignment_create(request):
    """Создание нового задания преподавателем"""
    if request.user.role != 'teacher' and not request.user.is_superuser:
        messages.error(request, 'Только преподаватели могут создавать задания')
        return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        deadline = request.POST.get('deadline')
        max_score = request.POST.get('max_score', 10)
        priority = request.POST.get('priority', 'medium')
        attachment = request.FILES.get('attachment')
        
        subject = get_object_or_404(Subject, id=subject_id)
        
        # Проверка, что преподаватель ведёт этот предмет
        if not request.user.is_superuser and subject.teacher != request.user:
            messages.error(request, 'Вы не ведёте этот предмет')
            return redirect('teacher_assignments')
        
        assignment = Assignment.objects.create(
            title=title,
            description=description,
            subject=subject,
            created_by=request.user,
            deadline=deadline,
            max_score=max_score,
            priority=priority,
            attachment=attachment
        )
        
        messages.success(request, f'Задание "{title}" создано')
        return redirect('teacher_assignments')
    
    # Получаем предметы преподавателя
    if request.user.is_superuser:
        subjects = Subject.objects.all()
    else:
        subjects = Subject.objects.filter(teacher=request.user)
    
    context = {
        'subjects': subjects,
        'priorities': Assignment.PRIORITY_CHOICES,
    }
    return render(request, 'assignments/assignment_form.html', context)


@login_required
def assignment_edit(request, assignment_id):
    """Редактирование задания"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if not request.user.is_superuser and assignment.created_by != request.user:
        messages.error(request, 'Вы не можете редактировать это задание')
        return redirect('teacher_assignments')
    
    if request.method == 'POST':
        assignment.title = request.POST.get('title')
        assignment.description = request.POST.get('description')
        assignment.deadline = request.POST.get('deadline')
        assignment.max_score = request.POST.get('max_score', 10)
        assignment.priority = request.POST.get('priority', 'medium')
        
        if request.FILES.get('attachment'):
            assignment.attachment = request.FILES.get('attachment')
        
        assignment.save()
        messages.success(request, f'Задание "{assignment.title}" обновлено')
        return redirect('teacher_assignments')
    
    context = {
        'assignment': assignment,
        'subjects': Subject.objects.filter(teacher=request.user) if not request.user.is_superuser else Subject.objects.all(),
        'priorities': Assignment.PRIORITY_CHOICES,
    }
    return render(request, 'assignments/assignment_form.html', context)


@login_required
def assignment_submissions(request, assignment_id):
    """Просмотр сданных заданий"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if not request.user.is_superuser and assignment.created_by != request.user:
        messages.error(request, 'Вы не можете просматривать это задание')
        return redirect('teacher_assignments')
    
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).select_related('student__user')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
    }
    return render(request, 'assignments/submissions_list.html', context)


@login_required
def grade_submission(request, submission_id):
    """Оценка сданного задания"""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    assignment = submission.assignment
    
    if not request.user.is_superuser and assignment.created_by != request.user:
        messages.error(request, 'Вы не можете оценивать это задание')
        return redirect('teacher_assignments')
    
    if request.method == 'POST':
        score = request.POST.get('score')
        feedback = request.POST.get('feedback', '')
        
        submission.score = score
        submission.feedback = feedback
        submission.status = 'graded'
        submission.graded_at = timezone.now()
        submission.graded_by = request.user
        submission.save()
        
        # Уведомление студенту
        create_notification(
            submission.student.user,
            'grade',
            f'Задание "{assignment.title}" проверено',
            f'Ваша оценка: {score}/{assignment.max_score}\n\nОтзыв: {feedback}',
            f'/assignments/{assignment.id}/'
        )
        
        messages.success(request, f'Оценка выставлена студенту {submission.student.user.get_full_name()}')
        submission.student.calculate_rating()
        return redirect('assignment_submissions', assignment_id=assignment.id)
    
    context = {
        'submission': submission,
        'assignment': assignment,
    }
    return render(request, 'assignments/grade_form.html', context)