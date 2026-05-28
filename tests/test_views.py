import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from apps.accounts.models import Group, StudentProfile, Subject, TeacherProfile

User = get_user_model()

@pytest.mark.django_db
class TestAuthViews:
    """Тесты авторизации"""
    
    def setup_method(self):
        self.client = Client()
    
    def test_home_page(self):
        response = self.client.get(reverse('home'))
        assert response.status_code == 200
    
    def test_login_page(self):
        response = self.client.get(reverse('login'))
        assert response.status_code == 200
    
    def test_register_page(self):
        response = self.client.get(reverse('register'))
        assert response.status_code == 200
    
    def test_user_login_success(self):
        User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == 302  # Redirect after login
    
    def test_user_login_fail(self):
        response = self.client.post(reverse('login'), {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        assert response.status_code == 200  # Stays on login page


@pytest.mark.django_db
class TestStudentViews:
    """Тесты страниц студента"""
    
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='student',
            password='pass123',
            first_name='Иван',
            last_name='Петров'
        )
        group = Group.objects.create(name='ТЕСТ-01', course=1, specialty='Тест')
        StudentProfile.objects.create(
            user=self.user,
            group=group,
            enrollment_year=2024
        )
        self.client.login(username='student', password='pass123')
    
    def test_gradebook_view(self):
        response = self.client.get(reverse('gradebook_view'))
        assert response.status_code == 200
    
    def test_schedule_view(self):
        response = self.client.get(reverse('schedule_view'))
        assert response.status_code == 200
    
    def test_assignments_list(self):
        response = self.client.get(reverse('assignments_list'))
        assert response.status_code == 200
    
    def test_rating_list(self):
        response = self.client.get(reverse('rating_list'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestTeacherViews:
    """Тесты страниц преподавателя"""
    
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='teacher',
            password='pass123',
            role='teacher'
        )
        TeacherProfile.objects.create(
            user=self.user,
            department='Кафедра ПО',
            position='Преподаватель',
            hire_date=date(2020, 1, 1)
        )
        self.client.login(username='teacher', password='pass123')
    
    def test_teacher_gradebook(self):
        response = self.client.get(reverse('teacher_gradebook'))
        assert response.status_code == 200
    
    def test_teacher_attendance(self):
        response = self.client.get(reverse('teacher_attendance'))
        assert response.status_code == 200
    
    def test_teacher_assignments(self):
        response = self.client.get(reverse('teacher_assignments'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminViews:
    """Тесты страниц админа"""
    
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.client.login(username='admin', password='admin123')
    
    def test_admin_penalties(self):
        response = self.client.get(reverse('admin_penalties'))
        assert response.status_code == 200
    
    def test_admin_all_grades(self):
        response = self.client.get(reverse('admin_all_grades'))
        assert response.status_code == 200
    
    def test_admin_all_schedule(self):
        response = self.client.get(reverse('admin_all_schedule'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestApiEndpoints:
    """Тесты API"""
    
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
    
    def test_unread_count_api(self):
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('unread_count'))
        assert response.status_code == 200
        assert response.json()['count'] == 0