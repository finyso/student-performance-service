import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from apps.accounts.models import User, StudentProfile, TeacherProfile, Group, Subject, Grade, Attendance, Schedule

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
        assert str(grade) == f"{student.user.get_full_name()} - {subject.name}: 8"
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