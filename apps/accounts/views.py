from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date
from datetime import timedelta
from .models import User, StudentProfile, Group, Penalty, Grade, Subject, Schedule, Attendance, Announcement, News
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string

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
    
    from .models import Grade, Group, Subject, StudentProfile
    
    # Фильтры
    group_id = request.GET.get('group')
    subject_id = request.GET.get('subject')
    student_card = request.GET.get('student_card')
    
    grades = Grade.objects.all().select_related('student__user', 'student__group', 'subject')
    
    if group_id:
        grades = grades.filter(student__group_id=group_id)
    if subject_id:
        grades = grades.filter(subject_id=subject_id)
    if student_card:
        grades = grades.filter(student__student_card_number__icontains=student_card)
    
    groups = Group.objects.all()
    subjects = Subject.objects.all()
    
    context = {
        'grades': grades[:200],
        'groups': groups,
        'subjects': subjects,
        'selected_group': group_id,
        'selected_subject': subject_id,
        'search_card': student_card,
    }
    return render(request, 'accounts/admin_all_grades.html', context)

@login_required
def admin_announcements(request):
    """Управление объявлениями для админа"""
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    from apps.notifications.utils import create_notification
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        group_id = request.POST.get('group_id')
        
        group = get_object_or_404(Group, id=group_id)
        
        Announcement.objects.create(
            title=title,
            content=content,
            group=group,
            created_by=request.user
        )
        
        # Уведомление всем студентам группы
        for student in StudentProfile.objects.filter(group=group):
            create_notification(
                student.user,
                'message',
                f'Новое объявление: {title}',
                content[:200],
                '/announcements/'
            )
        
        messages.success(request, f'Объявление "{title}" опубликовано для группы {group.name}')
        return redirect('admin_announcements')
    
    groups = Group.objects.all()
    announcements = Announcement.objects.all().order_by('-created_at')
    
    context = {
        'groups': groups,
        'announcements': announcements,
    }
    return render(request, 'accounts/admin_announcements.html', context)

@login_required
def admin_all_schedule(request):
    """Просмотр расписания всех групп (для админа) с переключением недель"""
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    from .models import Group, Schedule
    from datetime import date, timedelta
    
    group_id = request.GET.get('group')
    week_offset = int(request.GET.get('week', 0))
    groups = Group.objects.all()
    
    # Вычисляем текущую дату с учётом недели
    today = date.today()
    current_date = today + timedelta(days=week_offset * 7)
    
    # Получаем даты для текущей недели
    start_of_week = current_date - timedelta(days=current_date.weekday())
    week_dates = {}
    for i in range(7):
        week_dates[i + 1] = start_of_week + timedelta(days=i)
    
    schedules = []
    selected_group = None
    
    if group_id:
        selected_group = get_object_or_404(Group, id=group_id)
        schedules = Schedule.objects.filter(group=selected_group, is_active=True).select_related('subject', 'teacher').order_by('weekday', 'lesson_number')
    
    # Группируем расписание по дням недели
    schedule_by_day = {i: [] for i in range(1, 7)}
    for schedule in schedules:
        schedule_by_day[schedule.weekday].append(schedule)
    
    context = {
        'groups': groups,
        'selected_group': selected_group,
        'schedule_by_day': schedule_by_day,
        'weekdays': Schedule.WEEKDAYS,
        'week_dates': week_dates,
        'current_date': current_date,
        'week_offset': week_offset,
        'prev_week': week_offset - 1,
        'next_week': week_offset + 1,
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
        if schedule_id:
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
            return redirect(f'/headman/attendance/?date={selected_date.isoformat()}')
    
    # Получаем существующие отметки - ПРАВИЛЬНАЯ СТРУКТУРА
    attendances = {}
    for schedule in schedules:
        attendances[schedule.id] = {}
        for att in Attendance.objects.filter(schedule=schedule, date=selected_date):
            attendances[schedule.id][att.student_id] = att
    
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
    attendances = {}  # {schedule_id: {student_id: attendance}}
    
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
        
        # Загружаем существующие отметки
        for schedule in schedules:
            attendances[schedule.id] = {}
            for att in Attendance.objects.filter(schedule=schedule, date=selected_date):
                attendances[schedule.id][att.student_id] = att
    
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

@login_required
def admin_news(request):
    """Управление новостями для админа"""
    if not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        summary = request.POST.get('summary')
        content = request.POST.get('content')
        is_published = request.POST.get('is_published') == 'on'
        
        News.objects.create(
            title=title,
            summary=summary,
            content=content,
            is_published=is_published
        )
        messages.success(request, f'Новость "{title}" создана')
        return redirect('admin_news')
    
    news_list = News.objects.all().order_by('-created_at')
    
    context = {
        'news_list': news_list,
    }
    return render(request, 'accounts/admin_news.html', context)

@login_required
def profile_edit(request):
    """Редактирование профиля пользователя"""
    user = request.user
    
    if request.method == 'POST':
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.address = request.POST.get('address', user.address)
        
        date_of_birth_str = request.POST.get('date_of_birth')
        if date_of_birth_str:
            from datetime import datetime
            user.date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
        
        if request.FILES.get('avatar'):
            user.avatar = request.FILES.get('avatar')
        
        user.save()
        messages.success(request, 'Профиль успешно обновлён')
        return redirect('profile')
    
    context = {
        'user': user,
    }
    return render(request, 'accounts/profile_edit.html', context)

@login_required
def change_password(request):
    """Изменение пароля пользователя"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Сохраняем сессию
            messages.success(request, 'Пароль успешно изменён!')
            return redirect('profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})