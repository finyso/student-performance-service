FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание необходимых директорий
RUN mkdir -p staticfiles media logs

# Сбор статики
RUN python manage.py collectstatic --noinput

# Запуск
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]