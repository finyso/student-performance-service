from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from apps.notifications.utils import notify_about_request_status
from apps.accounts.models import Request, StudentProfile

@login_required
def requests_list(request):
    """Список заявок студента"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут просматривать заявки')
        return redirect('home')
    
    student = request.user.student_profile
    requests_list = Request.objects.filter(student=student).order_by('-created_at')
    
    paginator = Paginator(requests_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'request_types': Request.REQUEST_TYPES,
    }
    return render(request, 'requests/requests_list.html', context)


@login_required
def request_create(request):
    """Создание новой заявки"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Только студенты могут создавать заявки')
        return redirect('home')
    
    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if not request_type or not title or not description:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('request_create')
        
        new_request = Request.objects.create(
            student=request.user.student_profile,
            request_type=request_type,
            title=title,
            description=description,
            created_by=request.user,
            status='pending'
        )
        
        messages.success(request, f'Заявка #{new_request.id} успешно создана')
        return redirect('requests_list')
    
    context = {
        'request_types': Request.REQUEST_TYPES,
    }
    return render(request, 'requests/request_create.html', context)


@login_required
def request_detail(request, request_id):
    """Детали заявки"""
    req = get_object_or_404(Request, id=request_id)
    
    # Проверка доступа
    if hasattr(request.user, 'student_profile'):
        if req.student != request.user.student_profile and not request.user.is_superuser:
            messages.error(request, 'У вас нет доступа к этой заявке')
            return redirect('requests_list')
    elif not request.user.is_superuser and request.user.role != 'teacher':
        messages.error(request, 'У вас нет доступа')
        return redirect('home')
    
    return render(request, 'requests/request_detail.html', {'request': req})


@login_required
def admin_requests(request):
    """Управление заявками для администратора/преподавателя"""
    # Проверяем права доступа
    if not request.user.is_authenticated:
        messages.error(request, 'Пожалуйста, войдите в систему')
        return redirect('login')
    
    # Разрешаем доступ только суперпользователям и преподавателям
    if not (request.user.is_superuser or request.user.role == 'teacher'):
        messages.error(request, 'У вас недостаточно прав для просмотра этой страницы')
        return redirect('home')
    
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    
    requests_list = Request.objects.all().order_by('-created_at')
    
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    if type_filter:
        requests_list = requests_list.filter(request_type=type_filter)
    
    paginator = Paginator(requests_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'status_choices': Request.STATUS_CHOICES,
        'request_types': Request.REQUEST_TYPES,
    }
    return render(request, 'requests/admin_requests.html', context)

@login_required
def process_request(request, request_id):
    """Обработка заявки администратором"""
    if not (request.user.is_superuser or request.user.role == 'teacher'):
        messages.error(request, 'Доступ запрещён')
        return redirect('home')
    
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_comment = request.POST.get('admin_comment', '')
        
        req.status = status
        req.admin_comment = admin_comment
        req.reviewed_by = request.user
        req.save()
        
        messages.success(request, f'Заявка #{req.id} обновлена')
        return redirect('admin_requests')
    
    context = {
        'request': req,
        'status_choices': Request.STATUS_CHOICES,
    }

    notify_about_request_status(req)

    return render(request, 'requests/process_request.html', context)