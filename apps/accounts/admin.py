from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, TeacherProfile, Group, Subject, News, Schedule, Attendance, Notification, Penalty, Announcement

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'phone_number', 'avatar', 'date_of_birth', 'address')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'phone_number', 'date_of_birth')}),
    )

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'student_card_number', 'average_grade', 'rating']
    list_filter = ['group', 'enrollment_year']
    search_fields = ['user__first_name', 'user__last_name', 'student_card_number']

class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'position', 'degree']
    list_filter = ['department', 'degree']
    search_fields = ['user__first_name', 'user__last_name']

class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'specialty', 'curator', 'get_student_count']
    list_filter = ['course', 'specialty']
    search_fields = ['name']

class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'credits', 'semester', 'teacher']
    list_filter = ['semester', 'credits']
    search_fields = ['name', 'code']

admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(TeacherProfile, TeacherProfileAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Subject, SubjectAdmin)

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'is_published']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {}

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['group', 'subject', 'teacher', 'get_weekday_display', 'lesson_number', 'start_time', 'end_time', 'classroom']
    list_filter = ['weekday', 'is_active', 'group']
    search_fields = ['group__name', 'subject__name', 'teacher__username']
    fieldsets = (
        ('Основная информация', {
            'fields': ('group', 'subject', 'teacher', 'lesson_type')
        }),
        ('Время и место', {
            'fields': ('weekday', 'lesson_number', 'start_time', 'end_time', 'classroom')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'schedule', 'date', 'status', 'marked_at']
    list_filter = ['status', 'date', 'schedule__subject']
    search_fields = ['student__user__first_name', 'student__user__last_name']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']

@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ['student', 'penalty_type', 'reason', 'issued_by', 'issued_at']
    list_filter = ['penalty_type', 'issued_at']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'reason']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'created_by', 'created_at']
    list_filter = ['group', 'created_at']
    search_fields = ['title', 'content']