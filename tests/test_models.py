import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from apps.accounts.models import User, StudentProfile, TeacherProfile, Group, Subject, Grade, Attendance, Schedule, ChatRoom, ChatMessage, Notification, Request, Penalty, Announcement

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    """Тесты модели пользователя"""
    
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com',
            first_name='Тест',
            last_name='Пользователь'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@test.com'
        assert user.check_password('testpass123')
        assert user.role == 'student'
    
    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        assert admin.is_superuser
        assert admin.is_staff
        assert admin.username == 'admin'
    
    def test_user_str_method(self):
        user = User.objects.create_user(
            username='testuser',
            first_name='Иван',
            last_name='Петров'
        )
        assert str(user) == 'Иван Петров (Студент)'
    
    def test_user_age_method(self):
        user = User.objects.create_user(
            username='testuser',
            date_of_birth=date(2000, 1, 1)
        )
        assert user.age() == date.today().year - 2000


@pytest.mark.django_db
class TestGroupModel:
    """Тесты модели группы"""
    
    def test_create_group(self):
        group = Group.objects.create(
            name='ПИ-31',
            course=3,
            specialty='Программная инженерия'
        )
        assert group.name == 'ПИ-31'
        assert str(group) == 'ПИ-31 (3 курс)'
    
    def test_group_student_count(self):
        group = Group.objects.create(name='ТЕСТ-01', course=1, specialty='Тест')
        user = User.objects.create_user(username='student1', password='pass')
        StudentProfile.objects.create(
            user=user,
            group=group,
            enrollment_year=2023
        )
        assert group.get_student_count() == 1


@pytest.mark.django_db
class TestGradeModel:
    """Тесты модели оценок"""
    
    def test_create_grade(self):
        group = Group.objects.create(name='ТЕСТ-01', course=1, specialty='Тест')
        user = User.objects.create_user(username='student1', password='pass')
        student = StudentProfile.objects.create(
            user=user,
            group=group,
            enrollment_year=2023
        )
        teacher = User.objects.create_user(username='teacher1', password='pass', role='teacher')
        subject = Subject.objects.create(
            name='Тестовый предмет',
            code='TEST01',
            credits=3,
            semester=1,
            teacher=teacher
        )
        grade = Grade.objects.create(
            student=student,
            subject=subject,
            value=8,
            grade_type='exam',
            comment='Хорошая работа',
            created_by=teacher
        )
        assert grade.value == 8
        assert grade.get_grade_display_color() == 'primary'
    
    def test_grade_unique_constraint(self):
        group = Group.objects.create(name='ТЕСТ-01', course=1, specialty='Тест')
        user = User.objects.create_user(username='student1', password='pass')
        student = StudentProfile.objects.create(user=user, group=group, enrollment_year=2023)
        teacher = User.objects.create_user(username='teacher1', password='pass', role='teacher')
        subject = Subject.objects.create(
            name='Тестовый предмет',
            code='TEST01',
            credits=3,
            semester=1,
            teacher=teacher
        )
        Grade.objects.create(
            student=student,
            subject=subject,
            value=7,
            grade_type='exam',
            created_by=teacher
        )
        with pytest.raises(Exception):
            Grade.objects.create(
                student=student,
                subject=subject,
                value=9,
                grade_type='exam',
                created_by=teacher
            )


@pytest.mark.django_db
class TestAttendanceModel:
    """Тесты модели посещаемости"""
    
    def test_create_attendance(self):
        group = Group.objects.create(name='ТЕСТ-01', course=1, specialty='Тест')
        user = User.objects.create_user(username='student1', password='pass')
        student = StudentProfile.objects.create(user=user, group=group, enrollment_year=2023)
        teacher = User.objects.create_user(username='teacher1', password='pass', role='teacher')
        subject = Subject.objects.create(
            name='Тестовый предмет',
            code='TEST01',
            credits=3,
            semester=1,
            teacher=teacher
        )
        schedule = Schedule.objects.create(
            group=group,
            subject=subject,
            teacher=teacher,
            weekday=1,
            lesson_number=1,
            start_time='09:00',
            end_time='10:30',
            classroom='101'
        )
        attendance = Attendance.objects.create(
            student=student,
            schedule=schedule,
            date=date.today(),
            status='present',
            marked_by=teacher
        )
        assert attendance.status == 'present'
        assert attendance.get_status_color() == 'success'


@pytest.mark.django_db
class TestChatModel:
    """Тесты модели чата"""
    
    def test_create_chat_room(self):
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        room = ChatRoom.objects.create()
        room.participants.add(user1, user2)
        assert room.participants.count() == 2
        assert room.get_other_participant(user1) == user2
    
    def test_create_chat_message(self):
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        room = ChatRoom.objects.create()
        room.participants.add(user1, user2)
        message = ChatMessage.objects.create(
            room=room,
            sender=user1,
            content='Тестовое сообщение'
        )
        assert message.content == 'Тестовое сообщение'
        assert str(message) == 'user1: Тестовое сообщение'


@pytest.mark.django_db
class TestNotificationModel:
    """Тесты модели уведомлений"""
    
    def test_create_notification(self):
        user = User.objects.create_user(username='testuser', password='pass')
        notification = Notification.objects.create(
            user=user,
            notification_type='system',
            title='Тест',
            message='Тестовое уведомление'
        )
        assert notification.title == 'Тест'
        assert notification.is_read is False


@pytest.mark.django_db
class TestPenaltyModel:
    """Тесты модели взысканий"""
    
    def test_create_penalty(self):
        user = User.objects.create_user(username='student', password='pass')
        group = Group.objects.create(name='ТЕСТ', course=1, specialty='Тест')
        student = StudentProfile.objects.create(user=user, group=group, enrollment_year=2023)
        admin = User.objects.create_superuser(username='admin', password='pass', email='admin@test.com')
        penalty = Penalty.objects.create(
            student=student,
            penalty_type='warning',
            reason='Нарушение',
            issued_by=admin
        )
        assert penalty.penalty_type == 'warning'
        assert penalty.get_penalty_color() == 'warning'


@pytest.mark.django_db
class TestAnnouncementModel:
    """Тесты модели объявлений"""
    
    def test_create_announcement(self):
        group = Group.objects.create(name='ТЕСТ', course=1, specialty='Тест')
        user = User.objects.create_user(username='curator', password='pass', role='curator')
        announcement = Announcement.objects.create(
            title='Важное объявление',
            content='Завтра нет пар',
            group=group,
            created_by=user
        )
        assert announcement.title == 'Важное объявление'
        assert str(announcement) == f'Важное объявление - {group.name}'