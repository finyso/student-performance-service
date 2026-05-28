from apps.accounts.models import Attendance
from django.db.models import Count

# Найти дубликаты
duplicates = Attendance.objects.values('student', 'schedule', 'date').annotate(
    cnt=Count('id')
).filter(cnt__gt=1)

print(f"Найдено дубликатов: {duplicates.count()}")

# Удалить дубликаты (оставить только первый)
for dup in duplicates:
    atts = Attendance.objects.filter(
        student_id=dup['student'],
        schedule_id=dup['schedule'],
        date=dup['date']
    ).order_by('id')
    first = atts.first()
    for att in atts[1:]:
        att.delete()
        print(f"Удалён дубликат {att.id}")

print("Готово!")