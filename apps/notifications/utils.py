from apps.accounts.models import Notification, User
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_realtime_notification(user_id, notification):
    """Отправить уведомление в реальном времени через WebSocket"""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'send_notification',
                'notification_id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'link': notification.link or '',
                'created_at': notification.created_at.strftime('%H:%M')
            }
        )
    except Exception as e:
        print(f"WebSocket error: {e}")

def create_notification(user, notification_type, title, message, link=None, send_email=False):
    """Создать уведомление для пользователя"""
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )
    
    # Отправка через WebSocket
    send_realtime_notification(user.id, notification)
    
    return notification

def notify_students_in_group(group, notification_type, title, message, link=None):
    """Отправить уведомление всем студентам группы"""
    from apps.accounts.models import StudentProfile
    
    students = StudentProfile.objects.filter(group=group)
    for student in students:
        create_notification(student.user, notification_type, title, message, link)


def notify_teacher(subject, notification_type, title, message, link=None):
    """Отправить уведомление преподавателю"""
    if subject.teacher:
        create_notification(subject.teacher, notification_type, title, message, link)


def notify_about_grade(grade):
    """Уведомление о новой оценке"""
    title = f"Новая оценка по {grade.subject.name}"
    message = f"Вы получили оценку {grade.value} за {grade.get_grade_type_display()}"
    link = f"/gradebook/"
    create_notification(grade.student.user, 'grade', title, message, link)


def notify_about_attendance(attendance):
    """Уведомление о посещаемости"""
    if attendance.status == 'absent':
        title = f"Отсутствие на занятии"
        message = f"Вы отсутствовали на {attendance.schedule.subject.name} {attendance.date.strftime('%d.%m.%Y')}"
    elif attendance.status == 'late':
        title = f"Опоздание на занятие"
        message = f"Вы опоздали на {attendance.schedule.subject.name} {attendance.date.strftime('%d.%m.%Y')}"
    else:
        return
    link = f"/student/attendance/"
    create_notification(attendance.student.user, 'attendance', title, message, link)


def notify_about_request_status(request_obj):
    """Уведомление об изменении статуса заявки"""
    title = f"Статус заявки изменён: {request_obj.get_request_type_display()}"
    message = f"Ваша заявка \"{request_obj.title}\" получила статус: {request_obj.get_status_display()}"
    if request_obj.admin_comment:
        message += f"\n\nКомментарий: {request_obj.admin_comment}"
    
    # Определяем кому отправлять уведомление
    if request_obj.student:
        user = request_obj.student.user
        link = f"/my-requests/{request_obj.id}/"
    elif request_obj.teacher:
        user = request_obj.teacher.user
        link = f"/my-requests/{request_obj.id}/"
    else:
        user = request_obj.created_by
        link = f"/my-requests/{request_obj.id}/"
    
    create_notification(user, 'request', title, message, link)