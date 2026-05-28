import os
import django
from datetime import datetime, timedelta, date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Attendance, Schedule, StudentProfile

def fix_attendance():
    print("=" * 50)
    print("Очистка и пересоздание посещаемости...")
    print("=" * 50)
    
    # 1. Удаляем ВСЕ старые записи
    old_count = Attendance.objects.count()
    Attendance.objects.all().delete()
    print(f"✅ Удалено старых записей: {old_count}")
    
    # 2. Создаём новые записи
    print("\nСоздание новых записей посещаемости...")
    
    # Получаем все расписания
    schedules = Schedule.objects.all()
    new_count = 0
    
    # Для каждого расписания создаём записи за последние 30 дней
    days_back = 30
    today = date.today()
    
    for schedule in schedules:
        # Для каждого дня в расписании (по дням недели)
        for days_ago in range(days_back, -1, -1):
            lesson_date = today - timedelta(days=days_ago)
            
            # Проверяем, совпадает ли день недели
            if lesson_date.isoweekday() != schedule.weekday:
                continue
            
            # Получаем студентов группы
            students = StudentProfile.objects.filter(group=schedule.group)
            
            if not students:
                continue
            
            # Для каждого студента создаём запись
            import random
            for student in students:
                # Случайный статус (80% присутствуют)
                rand = random.random()
                if rand < 0.7:
                    status = 'present'
                    comment = ''
                elif rand < 0.85:
                    status = 'absent'
                    comment = 'Болел'
                else:
                    status = 'late'
                    comment = 'Опоздал на 5 минут'
                
                Attendance.objects.create(
                    student=student,
                    schedule=schedule,
                    date=lesson_date,
                    status=status,
                    comment=comment,
                    marked_by=schedule.teacher
                )
                new_count += 1
            
            print(f"  ✓ {schedule.group.name} - {lesson_date}: {schedule.subject.name} ({schedule.lesson_number} пара)")
    
    print(f"\n✅ Создано новых записей: {new_count}")
    print(f"📊 Итого в БД: {Attendance.objects.count()} записей")
    
    # 3. Статистика по студентам
    print("\n" + "=" * 50)
    print("Статистика по студентам:")
    for student in StudentProfile.objects.all()[:5]:
        count = Attendance.objects.filter(student=student).count()
        print(f"  • {student.user.get_full_name()}: {count} записей")

if __name__ == '__main__':
    fix_attendance()