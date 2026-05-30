import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from apps.accounts.models import Group, StudentProfile, Subject, TeacherProfile, ChatRoom, ChatMessage

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
        assert response.status_code == 302
    
    def test_user_login_fail(self):
        response = self.client.post(reverse('login'), {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestStudentViews:
    """Тесты страниц студента"""
    
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='student',
            password='pass123',
            first_name='Иван',
            last_name='Петров',
            role='student'
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
    
    def test_chat_list(self):
        response = self.client.get(reverse('chat_list'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestTeacherViews:
    """Тесты страниц преподавателя"""
    
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='teacher',
            password='pass123',
            first_name='Иван',
            last_name='Иванов',
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
    
    def test_chat_list(self):
        response = self.client.get(reverse('chat_list'))
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
    
    def test_admin_attendance(self):
        response = self.client.get(reverse('admin_attendance'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestChatViews:
    """Тесты чатов"""
    
    def setup_method(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123',
            first_name='Первый',
            last_name='Пользователь'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123',
            first_name='Второй',
            last_name='Пользователь'
        )
        self.client.login(username='user1', password='pass123')
    
    def test_chat_list(self):
        response = self.client.get(reverse('chat_list'))
        assert response.status_code == 200
    
    def test_chat_room_creation(self):
        response = self.client.get(reverse('chat_room', args=[self.user2.id]))
        assert response.status_code in [200, 302]
        if response.status_code == 302:
            assert response.url.startswith('/chat/')
    
    def test_api_get_messages(self):
        room = ChatRoom.objects.create()
        room.participants.add(self.user1, self.user2)
        response = self.client.get(reverse('api_get_messages', args=[room.id]))
        assert response.status_code == 200
        assert 'messages' in response.json()
    
    def test_api_send_message(self):
        room = ChatRoom.objects.create()
        room.participants.add(self.user1, self.user2)
        import json
        response = self.client.post(
            reverse('api_send_message'),
            data=json.dumps({'room_id': room.id, 'message': 'Тест'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert response.json().get('status') == 'ok'


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
        assert 'count' in response.json()
    
    def test_notifications_api(self):
        self.client.login(username='testuser', password='pass123')
        response = self.client.get(reverse('api_new_notifications'))
        assert response.status_code == 200
        assert 'notifications' in response.json()