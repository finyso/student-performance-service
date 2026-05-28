import os
import django
import random
from datetime import datetime, time, timedelta, date
from django.utils import timezone

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from apps.accounts.models import (
    User, StudentProfile, TeacherProfile, Group, Subject, 
    Schedule, Grade, Attendance, Request, Notification,
    Penalty, Announcement, News
)

def create_test_data():
    print("=" * 50)
    print("Создание тестовых данных...")
    print("=" * 50)
    
    # 1. Создание групп
    print("\n1. Создание групп...")
    groups_data = [
        {'name': 'ПИ-31', 'course': 3, 'specialty': 'Программная инженерия'},
        {'name': 'ПИ-32', 'course': 3, 'specialty': 'Программная инженерия'},
        {'name': 'ИС-41', 'course': 4, 'specialty': 'Информационные системы'},
        {'name': 'ВТ-21', 'course': 2, 'specialty': 'Вычислительная техника'},
        {'name': 'Э-11', 'course': 1, 'specialty': 'Экономика'},
    ]
    
    groups = {}
    for g in groups_data:
        group, created = Group.objects.get_or_create(name=g['name'], defaults=g)
        groups[g['name']] = group
        print(f"  ✓ Группа {g['name']} - {'создана' if created else 'существует'}")
    
    # 2. Создание пользователей и студентов/преподавателей
    print("\n2. Создание пользователей и студентов...")
    
    # Администратор
    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'password': make_password('admin123'),
            'email': 'admin@edu.by',
            'first_name': 'Администратор',
            'last_name': 'Системы',
            'role': 'admin',
            'is_superuser': True,
            'is_staff': True
        }
    )
    print("  ✓ Администратор создан (admin/admin123)")
    
    # Преподаватели
    teachers_data = [
        {'username': 'ivanov', 'first_name': 'Иван', 'last_name': 'Иванов', 'email': 'ivanov@edu.by', 
         'department': 'Кафедра ПО', 'position': 'Старший преподаватель', 'degree': 'docent'},
        {'username': 'petrova', 'first_name': 'Мария', 'last_name': 'Петрова', 'email': 'petrova@edu.by',
         'department': 'Кафедра ПО', 'position': 'Профессор', 'degree': 'professor'},
        {'username': 'sidorov', 'first_name': 'Сидор', 'last_name': 'Сидоров', 'email': 'sidorov@edu.by',
         'department': 'Кафедра ИС', 'position': 'Доцент', 'degree': 'docent'},
        {'username': 'kuznetsova', 'first_name': 'Анна', 'last_name': 'Кузнецова', 'email': 'kuznetsova@edu.by',
         'department': 'Кафедра ВТ', 'position': 'Старший преподаватель', 'degree': 'senior_teacher'},
        {'username': 'morozov', 'first_name': 'Алексей', 'last_name': 'Морозов', 'email': 'morozov@edu.by',
         'department': 'Кафедра Экономики', 'position': 'Доцент', 'degree': 'docent'},
        {'username': 'volkova', 'first_name': 'Елена', 'last_name': 'Волкова', 'email': 'volkova@edu.by',
         'department': 'Кафедра ПО', 'position': 'Ассистент', 'degree': 'assistant'},
        {'username': 'smirnov', 'first_name': 'Дмитрий', 'last_name': 'Смирнов', 'email': 'smirnov@edu.by',
         'department': 'Кафедра ИС', 'position': 'Профессор', 'degree': 'professor'},
    ]
    
    teachers = {}
    for t in teachers_data:
        user, created = User.objects.get_or_create(
            username=t['username'],
            defaults={
                'password': make_password('teacher123'),
                'email': t['email'],
                'first_name': t['first_name'],
                'last_name': t['last_name'],
                'role': 'teacher',
                'phone_number': f'+375 (29) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}',
                'date_of_birth': date(random.randint(1970, 1985), random.randint(1,12), random.randint(1,28)),
                'address': f'г. Минск, ул. Преподавательская, д. {random.randint(1,50)}'
            }
        )
        teacher_profile, _ = TeacherProfile.objects.get_or_create(
            user=user,
            defaults={
                'department': t['department'],
                'position': t['position'],
                'degree': t['degree'],
                'hire_date': date(random.randint(2005, 2020), random.randint(1,12), random.randint(1,28)),
                'office': f'{random.randint(1,5)}{random.randint(0,9)}{random.randint(0,9)}'
            }
        )
        teachers[t['username']] = user
        print(f"  ✓ Преподаватель {t['last_name']} {t['first_name']} (teacher123)")
    
    # Студенты (15 штук)
    students_data = [
        # Группа ПИ-31
        {'username': 'petrov_ivan', 'first_name': 'Иван', 'last_name': 'Петров', 'group': 'ПИ-31', 'phone': '+375 (29) 111-11-11', 'email': 'petrov@student.by'},
        {'username': 'sidorova_anna', 'first_name': 'Анна', 'last_name': 'Сидорова', 'group': 'ПИ-31', 'phone': '+375 (29) 222-22-22', 'email': 'sidorova@student.by'},
        {'username': 'kovalev_alex', 'first_name': 'Алексей', 'last_name': 'Ковалёв', 'group': 'ПИ-31', 'phone': '+375 (29) 333-33-33', 'email': 'kovalev@student.by'},
        {'username': 'morozova_olga', 'first_name': 'Ольга', 'last_name': 'Морозова', 'group': 'ПИ-31', 'phone': '+375 (29) 444-44-44', 'email': 'morozova@student.by'},
        # Группа ПИ-32
        {'username': 'kozlova_elena', 'first_name': 'Елена', 'last_name': 'Козлова', 'group': 'ПИ-32', 'phone': '+375 (29) 555-55-55', 'email': 'kozlova@student.by'},
        {'username': 'novikov_dmitry', 'first_name': 'Дмитрий', 'last_name': 'Новиков', 'group': 'ПИ-32', 'phone': '+375 (29) 666-66-66', 'email': 'novikov@student.by'},
        {'username': 'fedorov_sergey', 'first_name': 'Сергей', 'last_name': 'Фёдоров', 'group': 'ПИ-32', 'phone': '+375 (29) 777-77-77', 'email': 'fedorov@student.by'},
        # Группа ИС-41
        {'username': 'mikhailov_andrey', 'first_name': 'Андрей', 'last_name': 'Михайлов', 'group': 'ИС-41', 'phone': '+375 (29) 888-88-88', 'email': 'mikhailov@student.by'},
        {'username': 'vasilyeva_tatyana', 'first_name': 'Татьяна', 'last_name': 'Васильева', 'group': 'ИС-41', 'phone': '+375 (29) 999-99-99', 'email': 'vasilyeva@student.by'},
        # Группа ВТ-21
        {'username': 'nikolaev_pavel', 'first_name': 'Павел', 'last_name': 'Николаев', 'group': 'ВТ-21', 'phone': '+375 (29) 123-45-67', 'email': 'nikolaev@student.by'},
        {'username': 'aleksandrova_irina', 'first_name': 'Ирина', 'last_name': 'Александрова', 'group': 'ВТ-21', 'phone': '+375 (29) 234-56-78', 'email': 'aleksandrova@student.by'},
        # Группа Э-11
        {'username': 'egorov_maxim', 'first_name': 'Максим', 'last_name': 'Егоров', 'group': 'Э-11', 'phone': '+375 (29) 345-67-89', 'email': 'egorov@student.by'},
        {'username': 'romanova_natalia', 'first_name': 'Наталья', 'last_name': 'Романова', 'group': 'Э-11', 'phone': '+375 (29) 456-78-90', 'email': 'romanova@student.by'},
        {'username': 'titova_marina', 'first_name': 'Марина', 'last_name': 'Титова', 'group': 'Э-11', 'phone': '+375 (29) 567-89-01', 'email': 'titova@student.by'},
        # Староста
        {'username': 'headman_pi31', 'first_name': 'Артём', 'last_name': 'Королёв', 'group': 'ПИ-31', 'phone': '+375 (29) 678-90-12', 'email': 'headman@student.by', 'is_headman': True},
    ]
    
    students = {}
    for s in students_data:
        user, created = User.objects.get_or_create(
            username=s['username'],
            defaults={
                'password': make_password('student123'),
                'email': s['email'],
                'first_name': s['first_name'],
                'last_name': s['last_name'],
                'role': 'headman' if s.get('is_headman') else 'student',
                'phone_number': s['phone'],
                'date_of_birth': date(random.randint(1995, 2005), random.randint(1,12), random.randint(1,28)),
                'address': f'г. Минск, ул. {["Советская", "Ленина", "Машерова", "Независимости"][random.randint(0,3)]}, д. {random.randint(1,100)}, кв. {random.randint(1,100)}'
            }
        )
        student_profile, created = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'group': groups[s['group']],
                'student_card_number': f'STU{random.randint(10000,99999)}',
                'enrollment_year': date.today().year - groups[s['group']].course,
                'average_grade': 0,
                'rating': 0
            }
        )
        students[s['username']] = student_profile
        print(f"  ✓ Студент {s['last_name']} {s['first_name']} - группа {s['group']} (student123)")
        
        # Назначаем старосту
        if s.get('is_headman'):
            group = groups[s['group']]
            group.headman = student_profile
            group.save()
            print(f"    → Назначен старостой группы {group.name}")
    
    # 3. Создание предметов
    print("\n3. Создание предметов...")
    subjects_data = [
        {'name': 'Веб-программирование', 'code': 'WP301', 'credits': 4, 'semester': 5, 'teacher': 'ivanov'},
        {'name': 'Базы данных', 'code': 'DB302', 'credits': 3, 'semester': 5, 'teacher': 'petrova'},
        {'name': 'Python программирование', 'code': 'PY303', 'credits': 4, 'semester': 3, 'teacher': 'sidorov'},
        {'name': 'Алгоритмы и структуры данных', 'code': 'ASD201', 'credits': 5, 'semester': 3, 'teacher': 'ivanov'},
        {'name': 'Компьютерные сети', 'code': 'CN304', 'credits': 3, 'semester': 6, 'teacher': 'kuznetsova'},
        {'name': 'Экономика предприятия', 'code': 'EC101', 'credits': 3, 'semester': 1, 'teacher': 'morozov'},
        {'name': 'Математический анализ', 'code': 'MA102', 'credits': 5, 'semester': 1, 'teacher': 'volkova'},
        {'name': 'Физика', 'code': 'PH103', 'credits': 4, 'semester': 2, 'teacher': 'smirnov'},
    ]
    
    subjects = {}
    for s in subjects_data:
        subject, created = Subject.objects.get_or_create(
            code=s['code'],
            defaults={
                'name': s['name'],
                'credits': s['credits'],
                'semester': s['semester'],
                'teacher': teachers[s['teacher']],
                'description': f'Курс по {s["name"]} для студентов {s["semester"]} семестра'
            }
        )
        subjects[s['code']] = subject
        
        # Добавляем группы к предметам
        if s['semester'] == 5:
            subject.groups.add(groups['ПИ-31'], groups['ПИ-32'])
        elif s['semester'] == 3:
            subject.groups.add(groups['ПИ-31'], groups['ПИ-32'], groups['ВТ-21'])
        elif s['semester'] == 6:
            subject.groups.add(groups['ИС-41'])
        elif s['semester'] == 1:
            subject.groups.add(groups['Э-11'])
        elif s['semester'] == 2:
            subject.groups.add(groups['ВТ-21'])
        
        print(f"  ✓ Предмет {s['name']} - {s['code']}")
    
    # 4. Создание расписания
    print("\n4. Создание расписания...")
    schedule_data = [
        # Группа ПИ-31 (3 курс)
        {'group': 'ПИ-31', 'weekday': 1, 'lesson': 1, 'subject': 'WP301', 'start': '09:00', 'end': '10:30', 'room': '201', 'type': 'practice'},
        {'group': 'ПИ-31', 'weekday': 1, 'lesson': 2, 'subject': 'DB302', 'start': '10:45', 'end': '12:15', 'room': '203', 'type': 'lecture'},
        {'group': 'ПИ-31', 'weekday': 2, 'lesson': 1, 'subject': 'PY303', 'start': '09:00', 'end': '10:30', 'room': '305', 'type': 'lab'},
        {'group': 'ПИ-31', 'weekday': 3, 'lesson': 1, 'subject': 'ASD201', 'start': '09:00', 'end': '10:30', 'room': '101', 'type': 'practice'},
        {'group': 'ПИ-31', 'weekday': 4, 'lesson': 2, 'subject': 'WP301', 'start': '10:45', 'end': '12:15', 'room': '201', 'type': 'lab'},
        {'group': 'ПИ-31', 'weekday': 5, 'lesson': 1, 'subject': 'DB302', 'start': '09:00', 'end': '10:30', 'room': '203', 'type': 'practice'},
        
        # Группа Э-11 (1 курс)
        {'group': 'Э-11', 'weekday': 1, 'lesson': 1, 'subject': 'EC101', 'start': '09:00', 'end': '10:30', 'room': '401', 'type': 'lecture'},
        {'group': 'Э-11', 'weekday': 2, 'lesson': 2, 'subject': 'MA102', 'start': '10:45', 'end': '12:15', 'room': '402', 'type': 'practice'},
        {'group': 'Э-11', 'weekday': 3, 'lesson': 1, 'subject': 'EC101', 'start': '09:00', 'end': '10:30', 'room': '401', 'type': 'practice'},
    ]
    
    for s in schedule_data:
        group = groups[s['group']]
        subject = subjects[s['subject']]
        teacher = subject.teacher
        schedule, created = Schedule.objects.get_or_create(
            group=group,
            weekday=s['weekday'],
            lesson_number=s['lesson'],
            defaults={
                'subject': subject,
                'teacher': teacher,
                'start_time': datetime.strptime(s['start'], '%H:%M').time(),
                'end_time': datetime.strptime(s['end'], '%H:%M').time(),
                'classroom': s['room'],
                'lesson_type': s['type'],
                'is_active': True
            }
        )
        print(f"  ✓ {s['group']} - {s['weekday']} пара {s['lesson']}: {subject.name}")
    
    # 5. Выставление оценок (исправлено - проверка на уникальность)
    print("\n5. Выставление оценок...")
    grade_types = ['lab', 'practice', 'control', 'exam', 'homework']
    
    for student in students.values():
        for subject in subjects.values():
            if subject in student.group.subjects.all():
                # Для каждого типа оценки добавляем только одну оценку
                for grade_type in grade_types:
                    if random.random() > 0.3:  # 70% вероятность что оценка есть
                        grade_value = random.randint(5, 10)
                        # Используем update_or_create вместо create для избежания дубликатов
                        grade, created = Grade.objects.update_or_create(
                            student=student,
                            subject=subject,
                            grade_type=grade_type,
                            defaults={
                                'value': grade_value,
                                'comment': f'Оценка: {grade_value}',
                                'created_by': subject.teacher
                            }
                        )
        print(f"  ✓ {student.user.get_full_name()} - выставлены оценки")
    
    # 6. Отметки посещаемости
    print("\n6. Отметка посещаемости...")
    for schedule in Schedule.objects.all():
        for i in range(10):  # 10 занятий
            lesson_date = date.today() - timedelta(days=random.randint(0, 60))
            students_in_group = StudentProfile.objects.filter(group=schedule.group)
            for student in students_in_group:
                status = random.choice(['present', 'present', 'present', 'absent', 'late'])
                Attendance.objects.update_or_create(
                    student=student,
                    schedule=schedule,
                    date=lesson_date,
                    defaults={
                        'status': status,
                        'comment': '' if status == 'present' else ('Болел' if status == 'absent' else 'Опоздал на 5 минут'),
                        'marked_by': schedule.teacher
                    }
                )
    print("  ✓ Посещаемость отмечена")
    
    # 7. Новости
    print("\n7. Создание новостей...")
    news_data = [
        {'title': '📢 Начало учебного семестра', 'content': 'Уважаемые студенты! Поздравляем с началом нового семестра. Желаем успехов в учёбе! Расписание доступно в личном кабинете.'},
        {'title': '💻 Олимпиада по программированию', 'content': 'Приглашаем всех желающих принять участие в ежегодной олимпиаде по программированию. Регистрация до 15 ноября. Призы и грамоты для победителей!'},
        {'title': '🏫 День открытых дверей', 'content': '20 ноября состоится день открытых дверей. Приглашаем абитуриентов и их родителей. Начало в 11:00 в главном корпусе.'},
        {'title': '📚 График консультаций', 'content': 'Опубликован график консультаций перед экзаменационной сессией. Ознакомиться можно в разделе "Расписание".'},
        {'title': '🔬 Студенческая научная конференция', 'content': 'Приглашаем студентов к участию в научной конференции. Приём тезисов до 1 декабря. Лучшие работы будут опубликованы в сборнике.'},
        {'title': '🎓 Вручение дипломов', 'content': 'Торжественное вручение дипломов выпускникам состоится 30 июня в актовом зале. Начало в 14:00.'},
        {'title': '🏆 Спортивные соревнования', 'content': 'Приглашаем студентов принять участие в межфакультетских спортивных соревнованиях по футболу и волейболу. Регистрация в спортивном клубе.'},
    ]
    for news in news_data:
        News.objects.create(
            title=news['title'],
            summary=news['content'][:150],
            content=news['content'],
            is_published=True
        )
    print("  ✓ Новости созданы")
    
    # 8. Заявки
    print("\n8. Создание заявок...")
    request_types = ['certificate', 'reschedule', 'grade_correction', 'excused_absence', 'technical']
    request_titles = {
        'certificate': 'Запрос справки об обучении',
        'reschedule': 'Заявка на перенос занятия',
        'grade_correction': 'Просьба исправить оценку',
        'excused_absence': 'Пропуск по уважительной причине',
        'technical': 'Техническая проблема в системе'
    }
    
    for student in list(students.values())[:10]:
        for i in range(random.randint(1, 2)):
            req_type = random.choice(request_types)
            Request.objects.create(
                student=student,
                request_type=req_type,
                title=request_titles.get(req_type, 'Заявка'),
                description=f'Прошу рассмотреть вопрос. Студент {student.user.get_full_name()}. Детали: тестовое описание заявки.',
                status=random.choice(['pending', 'processing', 'approved', 'completed']),
                created_by=student.user
            )
    print("  ✓ Заявки созданы")
    
    # 9. Уведомления
    print("\n9. Создание уведомлений...")
    for user in User.objects.all():
        for i in range(random.randint(0, 2)):
            Notification.objects.create(
                user=user,
                notification_type='system',
                title=f'Уведомление {i+1}',
                message=f'Системное уведомление для пользователя {user.get_full_name()}. Все системы работают в штатном режиме.',
                is_read=random.choice([True, False])
            )
    print("  ✓ Уведомления созданы")
    
    # 10. Расчёт рейтинга
    print("\n10. Расчёт рейтинга студентов...")
    for student in StudentProfile.objects.all():
        student.calculate_rating()
    print("  ✓ Рейтинг рассчитан")
    
    print("\n" + "=" * 50)
    print("✅ Тестовые данные успешно созданы!")
    print("=" * 50)
    print("\n🔐 Данные для входа:")
    print("  📌 Администратор: admin / admin123")
    print("  📌 Преподаватели: любой из (ivanov, petrova, sidorov, kuznetsova, morozov, volkova, smirnov) / teacher123")
    print("  📌 Студенты: любой из списка / student123")
    print("  📌 Староста: headman_pi31 / student123")
    print("\n📊 Статистика:")
    print(f"  • Пользователей: {User.objects.count()}")
    print(f"  • Студентов: {StudentProfile.objects.count()}")
    print(f"  • Преподавателей: {TeacherProfile.objects.count()}")
    print(f"  • Групп: {Group.objects.count()}")
    print(f"  • Предметов: {Subject.objects.count()}")
    print(f"  • Оценок: {Grade.objects.count()}")
    print(f"  • Посещаемости: {Attendance.objects.count()}")
    print(f"  • Новостей: {News.objects.count()}")
    print(f"  • Заявок: {Request.objects.count()}")
    print(f"  • Уведомлений: {Notification.objects.count()}")

if __name__ == '__main__':
    create_test_data()