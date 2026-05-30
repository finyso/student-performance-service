from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from apps.accounts.models import Notification

@login_required
def notifications_list(request):
    """Список уведомлений пользователя"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    return render(request, 'notifications/list.html', context)


@login_required
def notification_detail(request, notification_id):
    """Просмотр уведомления"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Отмечаем как прочитанное
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    return render(request, 'notifications/detail.html', {'notification': notification})


@login_required
def mark_as_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    
    return redirect('notifications_list')


@login_required
def mark_all_read(request):
    """Отметить все уведомления как прочитанные"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Все уведомления отмечены как прочитанные')
    return redirect('notifications_list')


@login_required
def delete_notification(request, notification_id):
    """Удалить уведомление"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    messages.success(request, 'Уведомление удалено')
    return redirect('notifications_list')


@login_required
def get_unread_count(request):
    """API для получения количества непрочитанных уведомлений"""
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

@login_required
def api_get_new_notifications(request):
    """API для получения новых уведомлений (для polling)"""
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0
    
    # Получаем новые уведомления (ID больше last_id)
    new_notifications = Notification.objects.filter(
        user=request.user,
        id__gt=last_id
    ).order_by('-id')[:10]
    
    # Получаем количество непрочитанных
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'link': n.link or '',
                'type': n.notification_type,
                'created_at': n.created_at.strftime('%H:%M'),
                'is_read': n.is_read
            }
            for n in new_notifications
        ],
        'unread_count': unread_count
    }
    return JsonResponse(data)