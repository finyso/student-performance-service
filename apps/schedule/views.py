from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, datetime, timedelta
from django.db.models import Q
from apps.notifications.utils import notify_about_attendance
from apps.accounts.models import Schedule, Attendance, StudentProfile, Group, Subject

@login_required
def schedule_view(request):
    from datetime import date, timedelta
    
    today = date.today()
    week_offset = int(request.GET.get('week', 0))
    current_date = today + timedelta(days=week_offset * 7)
    start_of_week = current_date - timedelta(days=current_date.weekday())
    week_dates = {i + 1: start_of_week + timedelta(days=i) for i in range(7)}
    
    schedules = []
    
    if request.user.role in ['student', 'headman']:
        if hasattr(request.user, 'student_profile') and request.user.student_profile.group:
            group = request.user.student_profile.group
            schedules = Schedule.objects.filter(group=group, is_active=True).select_related('subject', 'teacher')
    elif request.user.role == 'teacher':
        schedules = Schedule.objects.filter(teacher=request.user, is_active=True).select_related('group', 'subject')
    elif request.user.role == 'curator':
        # Куратор видит расписание своих групп
        groups = Group.objects.filter(curator=request.user)
        schedules = Schedule.objects.filter(group__in=groups, is_active=True).select_related('group', 'subject', 'teacher')
    elif request.user.is_superuser:
        group_id = request.GET.get('group')
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                schedules = Schedule.objects.filter(group=group, is_active=True).select_related('subject', 'teacher')
            except Group.DoesNotExist:
                pass
    
    schedule_by_day = {i: [] for i in range(1, 7)}
    for schedule in schedules:
        schedule_by_day[schedule.weekday].append(schedule)
    
    groups = Group.objects.all() if request.user.is_superuser else []
    
    context = {
        'schedule_by_day': schedule_by_day,
        'weekdays': Schedule.WEEKDAYS,
        'current_date': current_date,
        'today': today,
        'week_offset': week_offset,
        'week_dates': week_dates,
        'groups': groups,
        'selected_group_id': request.GET.get('group'),
    }
    return render(request, 'schedule/schedule.html', context)

@login_required
def teacher_attendance(request, schedule_id=None, date_str=None):
    """Страница отметки посещаемости для преподавателя с выбором даты и группы"""
    if request.user.role != 'teacher' and not request.user.is_superuser:
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    from datetime import date, datetime
    
    # Получаем параметры из GET запроса
    selected_group_id = request.GET.get('group')
    selected_date_str = request.GET.get('date')
    
    # Определяем текущую дату
    if selected_date_str:
        current_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    elif date_str:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        current_date = date.today()
    
    # Получаем группы преподавателя
    if request.user.is_superuser:
        groups = Group.objects.all()
    else:
        groups = Group.objects.filter(subjects__teacher=request.user).distinct()
    
    selected_group = None
    schedules = []
    students = []
    attendances = {}
    
    # Если выбрана группа
    if selected_group_id:
        selected_group = get_object_or_404(Group, id=selected_group_id)
        weekday = current_date.isoweekday()
        
        # Получаем расписание на выбранный день
        schedules = Schedule.objects.filter(
            group=selected_group,
            teacher=request.user,
            weekday=weekday,
            is_active=True
        ).order_by('lesson_number')
        
        # Если есть расписание, получаем студентов
        if schedules:
            students = StudentProfile.objects.filter(group=selected_group).order_by('user__last_name')
            
            # Получаем существующие отметки для всех занятий
            attendances = {}
            for schedule in schedules:
                attendances[schedule.id] = {}
                for att in Attendance.objects.filter(schedule=schedule, date=current_date):
                    attendances[schedule.id][att.student_id] = att
    
    # Если передан конкретный schedule_id
    if schedule_id and not schedules:
        schedule = get_object_or_404(Schedule, id=schedule_id, teacher=request.user)
        selected_group = schedule.group
        schedules = [schedule]
        students = StudentProfile.objects.filter(group=selected_group).order_by('user__last_name')
        
        attendances = {}
        for att in Attendance.objects.filter(schedule=schedule, date=current_date):
            if schedule.id not in attendances:
                attendances[schedule.id] = {}
            attendances[schedule.id][att.student_id] = att
    
    # Обработка POST запроса (сохранение посещаемости)
    if request.method == 'POST':
        schedule_id_post = request.POST.get('schedule_id')
        if schedule_id_post:
            schedule = get_object_or_404(Schedule, id=schedule_id_post)
            
            for student in students:
                status = request.POST.get(f'status_{student.id}')
                if status:
                    comment = request.POST.get(f'comment_{student.id}', '')
                    Attendance.objects.update_or_create(
                        student=student,
                        schedule=schedule,
                        date=current_date,
                        defaults={
                            'status': status,
                            'comment': comment,
                            'marked_by': request.user
                        }
                    )
            
            messages.success(request, f'Посещаемость за {current_date.strftime("%d.%m.%Y")} сохранена')
            
            # Перенаправление с сохранением параметров
            if selected_group:
                return redirect(f'/teacher/attendance/?group={selected_group.id}&date={current_date.isoformat()}')
            else:
                return redirect('teacher_attendance')
    
    context = {
        'groups': groups,
        'selected_group': selected_group,
        'schedules': schedules,
        'students': students,
        'attendances': attendances,
        'current_date': current_date,
        'status_choices': Attendance.STATUS_CHOICES,
        'has_schedule': len(schedules) > 0,
    }
    return render(request, 'schedule/teacher_attendance.html', context)

@login_required
def teacher_attendance_by_date(request, date_str):
    """Отметка посещаемости по дате"""
    return teacher_attendance(request, schedule_id=None, date_str=date_str)

@login_required
def student_attendance(request):
    """Просмотр посещаемости студентом"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут просматривать посещаемость')
        return redirect('home')
    
    student = request.user.student_profile
    
    # Получаем все отметки посещаемости, сортируем по дате и паре
    attendances = Attendance.objects.filter(student=student).select_related(
        'schedule__subject', 'schedule__teacher'
    ).order_by('-date', 'schedule__lesson_number')
    
    # Статистика
    total = attendances.count()
    present = attendances.filter(status='present').count()
    absent = attendances.filter(status='absent').count()
    late = attendances.filter(status='late').count()
    excused = attendances.filter(status='excused').count()
    
    attendance_percentage = (present / total * 100) if total > 0 else 0
    
    context = {
        'attendances': attendances,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'attendance_percentage': round(attendance_percentage, 1),
    }
    return render(request, 'schedule/student_attendance.html', context)