from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from apps.accounts.models import ChatRoom, ChatMessage, User, StudentProfile, TeacherProfile, Group

@login_required
def chat_list(request):
    """Список чатов пользователя"""
    chat_rooms = ChatRoom.objects.filter(participants=request.user).order_by('-last_message_at')
    
    # Получаем последнее сообщение для каждого чата
    chats_data = []
    for room in chat_rooms:
        last_message = room.messages.last()
        other_user = room.get_other_participant(request.user)
        chats_data.append({
            'room': room,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': room.messages.filter(is_read=False).exclude(sender=request.user).count()
        })
    
    context = {
        'chats': chats_data,
    }
    return render(request, 'chat/chat_list.html', context)

@login_required
def chat_room(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    if not can_chat(request.user, other_user):
        messages.error(request, 'Вы не можете общаться с этим пользователем')
        return redirect('chat_list')
    
    # Находим или создаём комнату
    room = ChatRoom.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(request.user, other_user)
    
    # Отмечаем сообщения как прочитанные
    ChatMessage.objects.filter(room=room, is_read=False).exclude(sender=request.user).update(is_read=True)
    
    messages_list = room.messages.all().select_related('sender')
    
    # Обновляем время последнего сообщения
    if messages_list:
        room.last_message_at = messages_list.last().created_at
        room.save(update_fields=['last_message_at'])
    
    context = {
        'room': room,
        'other_user': other_user,
        'messages': messages_list,
        'room_id': room.id,
    }
    return render(request, 'chat/chat_room.html', context)

@login_required
def get_available_users(request):
    """Получить список пользователей для чата"""
    users = []
    
    # Для преподавателя - его студенты
    if request.user.role == 'teacher' and hasattr(request.user, 'teacher_profile'):
        subjects = request.user.subjects.all()
        groups = Group.objects.filter(subjects__in=subjects).distinct()
        students = StudentProfile.objects.filter(group__in=groups)
        for student in students:
            users.append({
                'id': student.user.id,
                'name': student.user.get_full_name(),
                'role': 'student',
                'group': student.group.name if student.group else ''
            })
    
    # Для студента - его преподаватели
    elif request.user.role in ['student', 'headman'] and hasattr(request.user, 'student_profile'):
        group = request.user.student_profile.group
        if group:
            subjects = group.subjects.all()
            teachers = set()
            for subject in subjects:
                if subject.teacher:
                    teachers.add(subject.teacher)
            for teacher in teachers:
                users.append({
                    'id': teacher.id,
                    'name': teacher.get_full_name(),
                    'role': 'teacher',
                    'subject': ', '.join([s.name for s in subjects.filter(teacher=teacher)])
                })
        
        # Куратор
        if group and group.curator:
            users.append({
                'id': group.curator.id,
                'name': group.curator.get_full_name(),
                'role': 'curator',
                'group': group.name
            })
    
    # Для куратора - его студенты
    elif request.user.role == 'curator':
        groups = Group.objects.filter(curator=request.user)
        for group in groups:
            for student in group.students.all():
                users.append({
                    'id': student.user.id,
                    'name': student.user.get_full_name(),
                    'role': 'student',
                    'group': group.name
                })
    
    # Для админа - все пользователи
    elif request.user.is_superuser:
        all_users = User.objects.exclude(id=request.user.id)
        for u in all_users[:50]:
            users.append({
                'id': u.id,
                'name': u.get_full_name(),
                'role': u.role,
            })
    
    # Убираем дубликаты
    seen = set()
    unique_users = []
    for user in users:
        if user['id'] not in seen:
            seen.add(user['id'])
            unique_users.append(user)
    
    return render(request, 'chat/available_users.html', {'users': unique_users})


def can_chat(user1, user2):
    """Проверка, могут ли пользователи общаться"""
    # Админ может общаться со всеми
    if user1.is_superuser or user2.is_superuser:
        return True
    
    # Студент и его преподаватель
    if hasattr(user1, 'student_profile') and hasattr(user2, 'teacher_profile'):
        group = user1.student_profile.group
        if group and user2 in [s.teacher for s in group.subjects.all()]:
            return True
    
    if hasattr(user2, 'student_profile') and hasattr(user1, 'teacher_profile'):
        group = user2.student_profile.group
        if group and user1 in [s.teacher for s in group.subjects.all()]:
            return True
    
    # Студент и куратор
    if hasattr(user1, 'student_profile') and user2.role == 'curator':
        group = user1.student_profile.group
        if group and group.curator == user2:
            return True
    
    if hasattr(user2, 'student_profile') and user1.role == 'curator':
        group = user2.student_profile.group
        if group and group.curator == user1:
            return True
    
    # Преподаватель и куратор
    if user1.role == 'teacher' and user2.role == 'curator':
        return True
    
    return False