from django.shortcuts import render
from apps.accounts.models import News

def home(request):
    """Главная страница"""
    last_news = News.objects.filter(is_published=True).order_by('-created_at')[:3]
    
    context = {
        'title': 'Сервис учёта успеваемости студентов',
        'last_news': last_news,
        'user': request.user,
    }
    return render(request, 'core/home.html', context)


def news_list(request):
    """Список новостей"""
    news_list = News.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'core/news_list.html', {'news_list': news_list})


def news_detail(request, pk):
    """Детальная страница новости"""
    news = News.objects.get(pk=pk, is_published=True)
    return render(request, 'core/news_detail.html', {'news': news})


def contacts(request):
    """Страница контактов"""
    contacts_list = [
        {'name': 'Приёмная комиссия', 'phone': '+375 (17) 123-45-67', 'email': 'priem@edu.by'},
        {'name': 'Учебный отдел', 'phone': '+375 (17) 123-45-68', 'email': 'study@edu.by'},
        {'name': 'Техническая поддержка', 'phone': '+375 (17) 123-45-69', 'email': 'support@edu.by'},
    ]
    return render(request, 'core/contacts.html', {'contacts': contacts_list})


def about(request):
    """Страница о компании"""
    return render(request, 'core/about.html')


def privacy_policy(request):
    """Политика конфиденциальности"""
    return render(request, 'core/privacy_policy.html')