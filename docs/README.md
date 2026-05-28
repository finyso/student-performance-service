# Сервис учёта успеваемости студентов

## 📖 О проекте

Веб-сервис для автоматизации учебного процесса учреждения образования. Система обеспечивает:
- Учёт успеваемости студентов
- Хранение оценок и рейтингов
- Управление расписанием
- Контроль посещаемости
- Взаимодействие студентов и преподавателей
- Обработку заявок и обращений
- Разграничение ролей пользователей
- Формирование статистики и отчётов

## 🚀 Технологии

- **Backend**: Django 5.x, Django REST Framework
- **Database**: SQLite (разработка), PostgreSQL (продакшн)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Асинхронность**: Celery, Redis, Django Channels
- **Документация**: Swagger/OpenAPI
- **Тестирование**: pytest, coverage
- **Деплой**: Docker, Gunicorn, Nginx

## 📋 Требования

- Python 3.12+
- Docker (опционально)

## 🛠 Установка и запуск

### Локальная установка

```bash
# 1. Клонирование репозитория
git clone <repository-url>
cd student_performance_service

# 2. Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Применение миграций
python manage.py migrate

# 5. Создание суперпользователя
python manage.py createsuperuser

# 6. Запуск сервера
python manage.py runserver