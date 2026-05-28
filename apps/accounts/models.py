from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date

class User(AbstractUser):
    """
    Кастомная модель пользователя с ролями
    """
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('teacher', 'Преподаватель'),
        ('student', 'Студент'),
        ('headman', 'Староста'),
        ('curator', 'Куратор'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name='Роль')
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$')],
        verbose_name='Номер телефона'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='Дата рождения')
    address = models.TextField(blank=True, null=True, verbose_name='Адрес')
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        if self.get_full_name():
            return f"{self.get_full_name()} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"
    
    def age(self):
        """Расчёт возраста пользователя"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role in ['student', 'headman']
    
    def is_headman(self):
        return self.role == 'headman'
    
    def is_curator(self):
        return self.role == 'curator'
    
    def save(self, *args, **kwargs):
        if self.is_superuser and self.role == 'student':
            self.role = 'admin'
        super().save(*args, **kwargs)

class StudentProfile(models.Model):
    """
    Профиль студента
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', verbose_name='Пользователь')
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name='Группа')
    student_card_number = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Номер студенческого')
    average_grade = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Средний балл')
    rating = models.IntegerField(default=0, verbose_name='Рейтинг')
    enrollment_year = models.IntegerField(verbose_name='Год поступления')
    
    class Meta:
        verbose_name = 'Профиль студента'
        verbose_name_plural = 'Профили студентов'
    
    def __str__(self):
        return f"Студент: {self.user.get_full_name()}"
    
    def get_course(self):
        """Определение текущего курса"""
        current_year = date.today().year
        course = current_year - self.enrollment_year + 1
        if course < 1:
            course = 1
        if course > 5:
            course = 5
        return course
    
    def calculate_rating(self):
        """Расчёт рейтинга студента по формуле: 70% оценки + 20% посещаемость + 10% активность"""
        from django.db.models import Avg
        
        # 1. Оценки (70%)
        grades = Grade.objects.filter(student=self)
        avg_grade = grades.aggregate(Avg('value'))['value__avg'] or 0
        grade_score = (avg_grade / 10) * 70
        
        # 2. Посещаемость (20%)
        attendances = Attendance.objects.filter(student=self)
        total = attendances.count()
        present = attendances.filter(status='present').count()
        attendance_percent = (present / total * 100) if total > 0 else 0
        attendance_score = (attendance_percent / 100) * 20
        
        # 3. Активность (10%) - сданные задания
        submissions_score = 0
        try:
            # Локальный импорт для избежания циклических зависимостей
            submissions = AssignmentSubmission.objects.filter(student=self, status='graded')
            submissions_count = submissions.count()
            submissions_score = min((submissions_count / 20) * 10, 10)
        except ImportError:
            # Если модуль assignments ещё не загружен
            submissions_score = 0
        
        # Итоговый рейтинг
        rating = grade_score + attendance_score + submissions_score
        
        # Обновляем поле rating
        self.rating = round(rating, 2)
        self.save(update_fields=['rating'])
        
        return self.rating


class TeacherProfile(models.Model):
    """
    Профиль преподавателя
    """
    DEGREE_CHOICES = [
        ('assistant', 'Ассистент'),
        ('senior_teacher', 'Старший преподаватель'),
        ('docent', 'Доцент'),
        ('professor', 'Профессор'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile', verbose_name='Пользователь')
    department = models.CharField(max_length=200, verbose_name='Кафедра')
    position = models.CharField(max_length=100, verbose_name='Должность')
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES, blank=True, null=True, verbose_name='Учёная степень')
    hire_date = models.DateField(verbose_name='Дата найма')
    office = models.CharField(max_length=50, blank=True, null=True, verbose_name='Кабинет')
    
    class Meta:
        verbose_name = 'Профиль преподавателя'
        verbose_name_plural = 'Профили преподавателей'
    
    def __str__(self):
        return f"Преподаватель: {self.user.get_full_name()}"


class Group(models.Model):
    """
    Учебная группа
    """
    name = models.CharField(max_length=20, unique=True, verbose_name='Название группы')
    course = models.IntegerField(verbose_name='Курс')
    specialty = models.CharField(max_length=200, verbose_name='Специальность')
    curator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='curated_groups', limit_choices_to={'role': 'curator'}, verbose_name='Куратор')
    headman = models.OneToOneField(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_group', verbose_name='Староста')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['course', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.course} курс)"
    
    def get_student_count(self):
        return self.students.count()


class Subject(models.Model):
    """
    Учебная дисциплина
    """
    SEMESTER_CHOICES = [(i, f"{i} семестр") for i in range(1, 9)]
    
    name = models.CharField(max_length=200, verbose_name='Название')
    code = models.CharField(max_length=20, unique=True, verbose_name='Код дисциплины')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    credits = models.IntegerField(default=3, verbose_name='Кредиты')
    semester = models.IntegerField(choices=SEMESTER_CHOICES, verbose_name='Семестр')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='subjects', limit_choices_to={'role': 'teacher'}, verbose_name='Преподаватель')
    groups = models.ManyToManyField(Group, related_name='subjects', verbose_name='Группы')
    
    class Meta:
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'
        ordering = ['semester', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.semester} семестр)"
    
class News(models.Model):
    """Новости системы"""
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    summary = models.CharField(max_length=300, verbose_name='Краткое описание')
    content = models.TextField(verbose_name='Содержание')
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    
    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
# ========== МОДЕЛИ ДЛЯ ОЦЕНОК ==========

class Grade(models.Model):
    """Оценка студента по предмету"""
    
    GRADE_TYPES = [
        ('lab', 'Лабораторная работа'),
        ('practice', 'Практическая работа'),
        ('control', 'Контрольная работа'),
        ('exam', 'Экзамен'),
        ('credit', 'Зачёт'),
        ('homework', 'Домашнее задание'),
        ('coursework', 'Курсовая работа'),
    ]
    
    GRADE_VALUES = [(i, str(i)) for i in range(1, 11)] + [(0, 'Не сдано')]
    
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='grades', verbose_name='Студент')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='grades', verbose_name='Предмет')
    value = models.IntegerField(choices=GRADE_VALUES, verbose_name='Оценка')
    grade_type = models.CharField(max_length=20, choices=GRADE_TYPES, verbose_name='Тип работы')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_grades', verbose_name='Кто поставил')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата выставления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        ordering = ['-created_at']
        unique_together = ['student', 'subject', 'grade_type']  # Одна оценка за тип работы
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name}: {self.value}"
    
    def get_grade_display_color(self):
        """Цвет оценки для отображения"""
        if self.value >= 9:
            return 'success'
        elif self.value >= 7:
            return 'primary'
        elif self.value >= 5:
            return 'warning'
        else:
            return 'danger'


class SemesterGrade(models.Model):
    """Итоговая оценка за семестр"""
    
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='semester_grades', verbose_name='Студент')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='semester_grades', verbose_name='Предмет')
    value = models.IntegerField(choices=[(i, str(i)) for i in range(1, 11)], verbose_name='Итоговая оценка')
    semester = models.IntegerField(verbose_name='Семестр')
    academic_year = models.CharField(max_length=9, verbose_name='Учебный год')  # 2024/2025
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Итоговая оценка'
        verbose_name_plural = 'Итоговые оценки'
        unique_together = ['student', 'subject', 'semester', 'academic_year']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name}: {self.value} ({self.semester} семестр)"
    
# ========== МОДЕЛИ ДЛЯ РАСПИСАНИЯ И ПОСЕЩАЕМОСТИ ==========

class Schedule(models.Model):
    """Расписание занятий"""
    
    WEEKDAYS = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
    ]
    
    LESSON_TYPES = [
        ('lecture', 'Лекция'),
        ('practice', 'Практика'),
        ('lab', 'Лабораторная'),
        ('seminar', 'Семинар'),
    ]
    
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name='schedule', verbose_name='Группа')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='schedule', verbose_name='Предмет')
    teacher = models.ForeignKey('User', on_delete=models.CASCADE, related_name='schedule', limit_choices_to={'role': 'teacher'}, verbose_name='Преподаватель')
    weekday = models.IntegerField(choices=WEEKDAYS, verbose_name='День недели')
    lesson_number = models.IntegerField(verbose_name='Номер пары')  # 1-6
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    classroom = models.CharField(max_length=50, verbose_name='Аудитория')
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='practice', verbose_name='Тип занятия')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['weekday', 'lesson_number']
        unique_together = ['group', 'weekday', 'lesson_number']
    
    def __str__(self):
        return f"{self.group.name} - {self.subject.name} ({self.get_weekday_display()}, {self.lesson_number} пара)"


class Attendance(models.Model):
    """Посещаемость студентов"""
    
    STATUS_CHOICES = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
        ('excused', 'Уважительная причина'),
    ]
    
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='attendances', verbose_name='Студент')
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE, related_name='attendances', verbose_name='Занятие')
    date = models.DateField(verbose_name='Дата занятия')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present', verbose_name='Статус')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    marked_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='marked_attendances', verbose_name='Отметил')
    marked_at = models.DateTimeField(auto_now_add=True, verbose_name='Время отметки')
    
    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        unique_together = ['student', 'schedule', 'date']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.date} ({self.get_status_display()})"
    
    def get_status_color(self):
        """Цвет статуса для отображения"""
        colors = {
            'present': 'success',
            'absent': 'danger',
            'late': 'warning',
            'excused': 'info',
        }
        return colors.get(self.status, 'secondary')
    
# ========== МОДЕЛИ ДЛЯ ЗАЯВОК ==========

class Request(models.Model):
    """Заявки студентов"""
    
    REQUEST_TYPES = [
        ('certificate', 'Справка об обучении'),
        ('reschedule', 'Перенос занятия'),
        ('academic_certificate', 'Академическая справка'),
        ('grade_correction', 'Исправление оценки'),
        ('excused_absence', 'Пропуск по уважительной причине'),
        ('technical', 'Техническая проблема'),
        ('other', 'Другое'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Создана'),
        ('processing', 'В обработке'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
        ('completed', 'Выполнена'),
    ]
    
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='requests', verbose_name='Студент')
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES, verbose_name='Тип заявки')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    admin_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий администратора')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_requests', verbose_name='Создал')
    reviewed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests', verbose_name='Рассмотрел')
    attachment = models.FileField(upload_to='requests/', blank=True, null=True, verbose_name='Вложение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_request_type_display()} - {self.student.user.get_full_name()}"
    
    def get_status_color(self):
        colors = {
            'pending': 'warning',
            'processing': 'info',
            'approved': 'success',
            'rejected': 'danger',
            'completed': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
# ========== МОДЕЛИ ДЛЯ УВЕДОМЛЕНИЙ ==========

class Notification(models.Model):
    """Уведомления для пользователей"""
    
    NOTIFICATION_TYPES = [
        ('grade', 'Новая оценка'),
        ('attendance', 'Посещаемость'),
        ('schedule', 'Изменение расписания'),
        ('deadline', 'Дедлайн'),
        ('request', 'Статус заявки'),
        ('message', 'Новое сообщение'),
        ('system', 'Системное уведомление'),
    ]
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications', verbose_name='Пользователь')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name='Тип')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    link = models.CharField(max_length=500, blank=True, null=True, verbose_name='Ссылка')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
# ========== МОДЕЛИ ДЛЯ ДОМАШНИХ ЗАДАНИЙ ==========

class Assignment(models.Model):
    """Домашнее задание"""
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='assignments', verbose_name='Предмет')
    created_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='created_assignments', verbose_name='Создал')
    deadline = models.DateTimeField(verbose_name='Дедлайн')
    max_score = models.IntegerField(default=10, verbose_name='Максимальный балл')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True, verbose_name='Вложение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['deadline', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.subject.name}"
    
    def is_overdue(self):
        """Проверка, просрочено ли задание"""
        from django.utils import timezone
        return timezone.now() > self.deadline
    
    def get_priority_color(self):
        colors = {
            'low': 'secondary',
            'medium': 'warning',
            'high': 'danger',
        }
        return colors.get(self.priority, 'secondary')


class AssignmentSubmission(models.Model):
    """Сданное домашнее задание студентом"""
    
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('submitted', 'Сдано'),
        ('graded', 'Проверено'),
        ('late', 'Просрочено'),
    ]
    
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name='submissions', verbose_name='Задание')
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='submissions', verbose_name='Студент')
    content = models.TextField(blank=True, null=True, verbose_name='Текст ответа')
    attachment = models.FileField(upload_to='submissions/', blank=True, null=True, verbose_name='Файл')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    score = models.IntegerField(null=True, blank=True, verbose_name='Оценка')
    feedback = models.TextField(blank=True, null=True, verbose_name='Отзыв преподавателя')
    submitted_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата сдачи')
    graded_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата проверки')
    graded_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions', verbose_name='Проверил')
    
    class Meta:
        verbose_name = 'Сданное задание'
        verbose_name_plural = 'Сданные задания'
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f"{self.assignment.title} - {self.student.user.get_full_name()}"
    
    def is_late(self):
        from django.utils import timezone
        if self.submitted_at and self.assignment.deadline:
            return self.submitted_at > self.assignment.deadline
        return False
    
    def save(self, *args, **kwargs):
        if self.status == 'submitted' and not self.submitted_at:
            from django.utils import timezone
            self.submitted_at = timezone.now()
        super().save(*args, **kwargs)

# ========== МОДЕЛЬ ДЛЯ ВЗЫСКАНИЙ ==========

class Penalty(models.Model):
    """Взыскания студентов"""
    
    PENALTY_TYPES = [
        ('warning', 'Замечание'),
        ('reprimand', 'Выговор'),
        ('severe_reprimand', 'Строгий выговор'),
        ('expulsion', 'Отчисление'),
    ]
    
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE, related_name='penalties', verbose_name='Студент')
    penalty_type = models.CharField(max_length=20, choices=PENALTY_TYPES, verbose_name='Тип взыскания')
    reason = models.TextField(verbose_name='Причина')
    issued_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='issued_penalties', verbose_name='Кто выдал')
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата выдачи')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        verbose_name = 'Взыскание'
        verbose_name_plural = 'Взыскания'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_penalty_type_display()}"
    
    def get_penalty_color(self):
        colors = {
            'warning': 'warning',
            'reprimand': 'danger',
            'severe_reprimand': 'dark',
            'expulsion': 'black',
        }
        return colors.get(self.penalty_type, 'secondary')
    
# ========== МОДЕЛЬ ДЛЯ ОБЪЯВЛЕНИЙ ==========

class Announcement(models.Model):
    """Объявления от куратора"""
    
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name='announcements', verbose_name='Группа')
    created_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='created_announcements', verbose_name='Создал')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.group.name}"