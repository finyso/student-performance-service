from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date
from .models import User, StudentProfile, Group, Penalty, Grade, Subject, Schedule, Attendance, Announcement

@login_required
def profile(request):
    """Профиль пользователя"""
    return render(request, 'accounts/profile.html', {'user': request.user})


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def rating_list(request):
    """Список рейтинга студентов"""
    from .models import StudentProfile  # Локальный импорт
    
    group = None
    if hasattr(request.user, 'student_profile'):
        group = request.user.student_profile.group
    
    # Получаем всех студентов
    students = StudentProfile.objects.all().select_related('user', 'group').order_by('-rating')
    
    # Добавляем позицию в рейтинге
    students_with_rank = []
    for idx, student in enumerate(students, 1):
        students_with_rank.append({
            'rank': idx,
            'name': student.user.get_full_name(),
            'group': student.group.name if student.group else '-',
            'rating': student.rating,
            'avg_grade': student.average_grade,
        })
    
    # Топ 10
    top_10 = students_with_rank[:10]
    
    # Рейтинг внутри группы студента
    group_rating = []
    if group:
        group_students = StudentProfile.objects.filter(group=group).order_by('-rating')
        for idx, student in enumerate(group_students, 1):
            group_rating.append({
                'rank': idx,
                'name': student.user.get_full_name(),
                'rating': student.rating,
            })
    
    # Текущий пользователь
    user_rating = None
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        user_rating = next((s for s in students_with_rank if s['name'] == request.user.get_full_name()), None)
    
    context = {
        'top_10': top_10,
        'group_rating': group_rating,
        'user_rating': user_rating,
    }
    return render(request, 'accounts/rating_list.html', context)

# ========== НОВЫЕ ФУНКЦИИ ДЛЯ РАЗНЫХ РОЛЕЙ ==========

@login_required
def group_list(request):
    """Список студентов в группе (для студента)"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут просматривать группу')
        return redirect('home')
    
    student = request.user.student_profile
    group = student.group
    
    if not group:
        messages.warning(request, 'Вы не привязаны к группе')
        return redirect('home')
    
    students = StudentProfile.objects.filter(group=group).select_related('user').order_by('user__last_name')
    
    # Добавляем информацию о старосте
    headman = group.headman
    
    context = {
        'group': group,
        'students': students,
        'headman': headman,
    }
    return render(request, 'accounts/group_list.html', context)


@login_required
def penalties_list(request):
    """Список взысканий студента"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут просматривать взыскания')
        return redirect('home')
    
    student = request.user.student_profile
    penalties = Penalty.objects.filter(student=student, is_active=True).order_by('-issued_at')
    
    context = {
        'penalties': penalties,
    }
    return render(request, 'accounts/penalties_list.html', context)


@login_required
def admin_penalties(request):
    """Управление взысканиями (для админа)"""
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    from .models import StudentProfile, Penalty
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        penalty_type = request.POST.get('penalty_type')
        reason = request.POST.get('reason')
        
        student = get_object_or_404(StudentProfile, id=student_id)
        
        Penalty.objects.create(
            student=student,
            penalty_type=penalty_type,
            reason=reason,
            issued_by=request.user
        )
        
        # Уведомление студенту
        from apps.notifications.utils import create_notification
        create_notification(
            student.user,
            'system',
            f'Вам вынесено {dict(Penalty.PENALTY_TYPES).get(penalty_type)}',
            f'Причина: {reason[:200]}',
            '/penalties/'
        )
        
        messages.success(request, f'Взыскание добавлено студенту {student.user.get_full_name()}')
        return redirect('admin_penalties')
    
    students = StudentProfile.objects.all().select_related('user', 'group')
    penalties = Penalty.objects.all().select_related('student__user', 'issued_by').order_by('-issued_at')[:50]
    
    context = {
        'students': students,
        'penalties': penalties,
        'penalty_types': Penalty.PENALTY_TYPES,
    }
    return render(request, 'accounts/admin_penalties.html', context)

@login_required
def admin_all_grades(request):
    """Просмотр оценок всех студентов (для админа)"""
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    # Импортируем модели, если их нет в глобальном импорте
    from .models import Grade, Group, Subject, StudentProfile
    
    # Фильтры
    group_id = request.GET.get('group')
    subject_id = request.GET.get('subject')
    student_id = request.GET.get('student')
    
    grades = Grade.objects.all().select_related('student__user', 'student__group', 'subject')
    
    if group_id:
        grades = grades.filter(student__group_id=group_id)
    if subject_id:
        grades = grades.filter(subject_id=subject_id)
    if student_id:
        grades = grades.filter(student_id=student_id)
    
    groups = Group.objects.all()
    subjects = Subject.objects.all()
    students = StudentProfile.objects.all()
    
    context = {
        'grades': grades[:100],
        'groups': groups,
        'subjects': subjects,
        'students': students,
        'selected_group': group_id,
        'selected_subject': subject_id,
        'selected_student': student_id,
    }
    return render(request, 'accounts/admin_all_grades.html', context)

@login_required
def admin_all_schedule(request):
    """Просмотр расписания всех групп (для админа)"""
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    from .models import Group, Schedule
    from datetime import date
    
    group_id = request.GET.get('group')
    groups = Group.objects.all()
    
    schedules = []
    selected_group = None
    current_date = date.today()
    
    if group_id:
        selected_group = get_object_or_404(Group, id=group_id)
        schedules = Schedule.objects.filter(group=selected_group, is_active=True).select_related('subject', 'teacher').order_by('weekday', 'lesson_number')
    
    # Получаем даты для текущей недели
    from datetime import timedelta
    week_dates = {}
    start_of_week = current_date - timedelta(days=current_date.weekday())
    for i in range(7):
        week_dates[i + 1] = start_of_week + timedelta(days=i)
    
    context = {
        'groups': groups,
        'selected_group': selected_group,
        'schedules': schedules,
        'weekdays': Schedule.WEEKDAYS,
        'week_dates': week_dates,
        'current_date': current_date,
    }
    return render(request, 'accounts/admin_all_schedule.html', context)

@login_required
def headman_attendance(request):
    """Отметка посещаемости для старосты"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    student = request.user.student_profile
    group = student.group
    
    if not group:
        messages.error(request, 'Вы не привязаны к группе')
        return redirect('home')
    
    if group.headman != student:
        messages.error(request, 'Вы не являетесь старостой этой группы')
        return redirect('home')
    
    from datetime import date, datetime
    current_date = date.today()
    selected_date = request.GET.get('date', current_date.isoformat())
    
    if isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    # Получаем расписание на выбранный день
    weekday = selected_date.isoweekday()
    schedules = Schedule.objects.filter(group=group, weekday=weekday, is_active=True).order_by('lesson_number')
    
    students_list = StudentProfile.objects.filter(group=group).order_by('user__last_name')
    
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        if not schedule_id:
            messages.error(request, 'Не выбран предмет')
            return redirect('headman_attendance')
        
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        for student_item in students_list:
            status = request.POST.get(f'status_{student_item.id}')
            if status:
                comment = request.POST.get(f'comment_{student_item.id}', '')
                Attendance.objects.update_or_create(
                    student=student_item,
                    schedule=schedule,
                    date=selected_date,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'comment': comment
                    }
                )
        messages.success(request, f'Посещаемость за {selected_date.strftime("%d.%m.%Y")} сохранена')
        return redirect('headman_attendance')
    
    # Получаем существующие отметки для отображения
    attendances = {}
    for schedule in schedules:
        for att in Attendance.objects.filter(schedule=schedule, date=selected_date):
            attendances[f"{schedule.id}_{att.student_id}"] = att
    
    context = {
        'group': group,
        'schedules': schedules,
        'students': students_list,
        'selected_date': selected_date,
        'attendances': attendances,
        'status_choices': Attendance.STATUS_CHOICES,
    }
    return render(request, 'accounts/headman_attendance.html', context)

@login_required
def curator_announcements(request):
    """Объявления куратора"""
    if request.user.role != 'curator' and not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    # Получаем группы куратора
    if request.user.is_superuser:
        groups = Group.objects.all()
    else:
        groups = Group.objects.filter(curator=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        group_id = request.POST.get('group_id')
        
        group = get_object_or_404(Group, id=group_id)
        
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            group=group,
            created_by=request.user
        )
        
        # Отправляем уведомления всем студентам группы
        from apps.notifications.utils import create_notification
        students = StudentProfile.objects.filter(group=group)
        for student in students:
            create_notification(
                student.user,
                'message',
                f'Новое объявление: {title}',
                content[:200],
                '/announcements/'
            )
        
        messages.success(request, f'Объявление "{title}" опубликовано для группы {group.name}')
        return redirect('curator_announcements')
    
    announcements = Announcement.objects.filter(group__in=groups).order_by('-created_at')
    
    context = {
        'groups': groups,
        'announcements': announcements,
    }
    return render(request, 'accounts/curator_announcements.html', context)


@login_required
def curator_group_students(request):
    """Просмотр группы куратором"""
    if request.user.role != 'curator' and not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    if request.user.is_superuser:
        groups = Group.objects.all()
        selected_group_id = request.GET.get('group')
        if selected_group_id:
            group = get_object_or_404(Group, id=selected_group_id)
        else:
            group = groups.first()
    else:
        groups = Group.objects.filter(curator=request.user)
        group = groups.first()
    
    students = []
    if group:
        students = StudentProfile.objects.filter(group=group).select_related('user').order_by('user__last_name')
    
    context = {
        'groups': groups,
        'selected_group': group,
        'students': students,
    }
    return render(request, 'accounts/curator_group_students.html', context)


@login_required
def student_announcements(request):
    """Просмотр объявлений для студентов"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут просматривать объявления')
        return redirect('home')
    
    group = request.user.student_profile.group
    announcements = Announcement.objects.filter(group=group, is_active=True).order_by('-created_at')
    
    context = {
        'announcements': announcements,
    }
    return render(request, 'accounts/student_announcements.html', context)

@login_required
def admin_attendance(request):
    """Выставление посещаемости для админа"""
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    from datetime import date, datetime
    
    group_id = request.GET.get('group')
    selected_date = request.GET.get('date', date.today().isoformat())
    
    if isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    groups = Group.objects.all()
    selected_group = None
    schedules = []
    students = []
    attendances = {}
    
    if group_id:
        selected_group = get_object_or_404(Group, id=group_id)
        weekday = selected_date.isoweekday()
        schedules = Schedule.objects.filter(group=selected_group, weekday=weekday, is_active=True).order_by('lesson_number')
        students = StudentProfile.objects.filter(group=selected_group).order_by('user__last_name')
        
        if request.method == 'POST':
            schedule_id = request.POST.get('schedule_id')
            if schedule_id:
                schedule = get_object_or_404(Schedule, id=schedule_id)
                for student in students:
                    status = request.POST.get(f'status_{student.id}')
                    if status:
                        Attendance.objects.update_or_create(
                            student=student,
                            schedule=schedule,
                            date=selected_date,
                            defaults={
                                'status': status,
                                'marked_by': request.user,
                                'comment': request.POST.get(f'comment_{student.id}', '')
                            }
                        )
                messages.success(request, f'Посещаемость за {selected_date.strftime("%d.%m.%Y")} сохранена')
                return redirect(f'/control/attendance/?group={group_id}&date={selected_date.isoformat()}')
        
        # Получаем существующие отметки
        for schedule in schedules:
            for att in Attendance.objects.filter(schedule=schedule, date=selected_date):
                attendances[f"{schedule.id}_{att.student_id}"] = att
    
    context = {
        'groups': groups,
        'selected_group': selected_group,
        'selected_date': selected_date,
        'schedules': schedules,
        'students': students,
        'attendances': attendances,
        'status_choices': Attendance.STATUS_CHOICES,
    }
    return render(request, 'accounts/admin_attendance.html', context)