from apps.accounts.models import Notification

def notifications_processor(request):
    """Контекстный процессор для уведомлений"""
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {'unread_count': unread_count}