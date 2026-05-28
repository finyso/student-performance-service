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
    """Просмотр расписания для студента или преподавателя"""
    today = date.today()
    current_weekday = today.isoweekday()
    
    # Получаем параметры фильтрации
    week_offset = int(request.GET.get('week', 0))
    selected_date = request.GET.get('date')
    
    if selected_date:
        current_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        current_weekday = current_date.isoweekday()
    else:
        current_date = today + timedelta(days=week_offset * 7)
    
    # Определяем, чьё расписание показывать
    if request.user.role == 'student' and hasattr(request.user, 'student_profile'):
        group = request.user.student_profile.group
        schedules = Schedule.objects.filter(group=group, is_active=True).select_related('subject', 'teacher')
    elif request.user.role == 'teacher':
        schedules = Schedule.objects.filter(teacher=request.user, is_active=True).select_related('group', 'subject')
    else:
        schedules = Schedule.objects.filter(is_active=True).select_related('group', 'subject', 'teacher')
    
    # Группируем по дням недели
    schedule_by_day = {i: [] for i in range(1, 7)}
    for schedule in schedules:
        schedule_by_day[schedule.weekday].append(schedule)
    
    context = {
        'schedule_by_day': schedule_by_day,
        'weekdays': Schedule.WEEKDAYS,
        'current_date': current_date,
        'today': today,
        'week_offset': week_offset,
    }
    return render(request, 'schedule/schedule.html', context)


@login_required
def teacher_attendance(request, schedule_id=None, date_str=None):
    """Страница отметки посещаемости для преподавателя"""
    if request.user.role != 'teacher' and not request.user.is_superuser:
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    # Если дата не указана, используем сегодня
    if date_str:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        current_date = date.today()
    
    # Получаем расписание преподавателя на выбранный день
    weekday = current_date.isoweekday()
    
    if schedule_id:
        schedule = get_object_or_404(Schedule, id=schedule_id, teacher=request.user)
    else:
        # Ищем расписание на текущий день
        schedule = Schedule.objects.filter(
            teacher=request.user,
            weekday=weekday,
            is_active=True
        ).first()
    
    if not schedule:
        # Показываем список всех занятий на сегодня
        schedules_today = Schedule.objects.filter(
            teacher=request.user,
            weekday=weekday,
            is_active=True
        ).order_by('lesson_number')
        
        context = {
            'schedules_today': schedules_today,
            'current_date': current_date,
            'has_schedule': False,
        }
        return render(request, 'schedule/teacher_attendance_select.html', context)
    
    # Получаем студентов группы
    students = StudentProfile.objects.filter(group=schedule.group).order_by('user__last_name', 'user__first_name')
    
    # Получаем уже существующие отметки
    attendances = {
        att.student_id: att for att in Attendance.objects.filter(
            schedule=schedule,
            date=current_date
        )
    }
    
    # Обработка POST запроса
    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            comment = request.POST.get(f'comment_{student.id}', '')
            
            if status:
                attendance, created = Attendance.objects.update_or_create(
                    student=student,
                    schedule=schedule,
                    date=current_date,
                    defaults={
                        'status': status,
                        'comment': comment,
                        'marked_by': request.user
                    }
                )

            if attendance.status in ['absent', 'late']:
                notify_about_attendance(attendance)
                student.calculate_rating()
        
        messages.success(request, f'Посещаемость за {current_date.strftime("%d.%m.%Y")} сохранена')
        return redirect('teacher_attendance_date', schedule_id=schedule.id, date_str=current_date.isoformat())
    
    context = {
        'schedule': schedule,
        'students': students,
        'attendances': attendances,
        'current_date': current_date,
        'status_choices': Attendance.STATUS_CHOICES,
        'has_schedule': True,
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
    
    # Получаем все отметки посещаемости
    attendances = Attendance.objects.filter(student=student).select_related('schedule__subject', 'schedule__teacher').order_by('-date')
    
    # Статистика
    total = attendances.count()
    present = attendances.filter(status='present').count()
    absent = attendances.filter(status='absent').count()
    late = attendances.filter(status='late').count()
    excused = attendances.filter(status='excused').count()
    
    attendance_percentage = (present / total * 100) if total > 0 else 0
    
    context = {
        'attendances': attendances[:50],  # Последние 50 записей
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'attendance_percentage': round(attendance_percentage, 1),
    }
    return render(request, 'schedule/student_attendance.html', context)