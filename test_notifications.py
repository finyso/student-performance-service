import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User, StudentProfile, TeacherProfile, Group, Subject, Grade, Attendance, Schedule, Assignment, Request, Penalty, Announcement
from apps.notifications.utils import create_notification
from datetime import date, timedelta
from django.utils import timezone

def test_all_notifications():
    print("=" * 50)
    print("Тестирование уведомлений")
    print("=" * 50)
    
    try:
        # Получаем пользователей
        admin = User.objects.get(username='admin')
        teacher = User.objects.get(username='ivanov')
        student_user = User.objects.get(username='headman_pi31')
        student = StudentProfile.objects.get(user=student_user)
        group = Group.objects.get(name='ПИ-31')
        subject = Subject.objects.get(code='WP301')
        
        print("\n1. Тест уведомления об оценке...")
        # Используем update_or_create вместо create
        grade, created = Grade.objects.update_or_create(
            student=student,
            subject=subject,
            grade_type='homework',  # используем другой тип, чтобы не было конфликта
            defaults={
                'value': 9,
                'comment': 'Отличная работа!',
                'created_by': teacher
            }
        )
        if created:
            print("  ✓ Создана новая оценка - уведомление отправлено студенту")
        else:
            print("  ✓ Обновлена существующая оценка - уведомление отправлено студенту")
        
        print("\n2. Тест уведомления о посещаемости...")
        schedule = Schedule.objects.filter(group=group, subject=subject).first()
        if schedule:
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                schedule=schedule,
                date=date.today(),
                defaults={
                    'status': 'absent',
                    'comment': 'Болеет',
                    'marked_by': teacher
                }
            )
            print("  ✓ Отмечено отсутствие - уведомление отправлено студенту")
        else:
            print("  ⚠ Нет расписания для теста посещаемости")
        
        print("\n3. Тест уведомления о заявке...")
        # Используем get_or_create
        request_obj, created = Request.objects.get_or_create(
            student=student,
            request_type='vacation',
            title='Заявка на отпуск',
            defaults={
                'description': 'Прошу предоставить отпуск',
                'created_by': student_user,
                'status': 'pending'
            }
        )
        request_obj.status = 'approved'
        request_obj.admin_comment = 'Одобрено'
        request_obj.save()
        print("  ✓ Изменён статус заявки - уведомление отправлено студенту")
        
        print("\n4. Тест уведомления о задании...")
        assignment, created = Assignment.objects.get_or_create(
            title='Тестовое задание',
            subject=subject,
            defaults={
                'description': 'Выполнить тест',
                'created_by': teacher,
                'deadline': timezone.now() + timedelta(days=2),
                'max_score': 10,
                'is_active': True
            }
        )
        print("  ✓ Задание создано - уведомление отправлено студентам группы")
        
        print("\n5. Тест уведомления об объявлении...")
        announcement, created = Announcement.objects.get_or_create(
            title='Важное объявление',
            group=group,
            defaults={
                'content': 'Завтра нет пар',
                'created_by': admin
            }
        )
        print("  ✓ Объявление создано - уведомление отправлено студентам группы")
        
        print("\n6. Тест уведомления о взыскании...")
        penalty, created = Penalty.objects.get_or_create(
            student=student,
            penalty_type='reprimand',
            reason='Нарушение дисциплины',
            defaults={'issued_by': admin}
        )
        print("  ✓ Взыскание создано - уведомление отправлено студенту")
        
        print("\n" + "=" * 50)
        print("✅ Все тесты уведомлений выполнены!")
        print("\n📋 Проверьте уведомления в интерфейсе:")
        print(f"  - Студент {student_user.username} -> http://127.0.0.1:8000/notifications/")
        print(f"  - Преподаватель {teacher.username} -> http://127.0.0.1:8000/notifications/")
        print(f"  - Админ {admin.username} -> http://127.0.0.1:8000/notifications/")
        
    except User.DoesNotExist as e:
        print(f"\n❌ Ошибка: пользователь не найден - {e}")
        print("\nУбедитесь, что вы создали тестовые данные командой:")
        print("  python create_test_data.py")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == '__main__':
    test_all_notifications()