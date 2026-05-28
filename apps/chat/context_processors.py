from apps.accounts.models import ChatRoom, ChatMessage

def chat_unread_count(request):
    """Количество непрочитанных сообщений для пользователя"""
    if request.user.is_authenticated:
        # Получаем все комнаты пользователя
        rooms = ChatRoom.objects.filter(participants=request.user)
        unread_count = 0
        for room in rooms:
            unread_count += room.messages.filter(is_read=False).exclude(sender=request.user).count()
        return {'chat_unread_count': unread_count}
    return {'chat_unread_count': 0}