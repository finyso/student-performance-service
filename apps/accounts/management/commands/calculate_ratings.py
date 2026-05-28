from django.core.management.base import BaseCommand
from apps.accounts.models import StudentProfile

class Command(BaseCommand):
    help = 'Calculate ratings for all students'
    
    def handle(self, *args, **options):
        students = StudentProfile.objects.all()
        count = 0
        for student in students:
            student.calculate_rating()
            count += 1
            self.stdout.write(f"Calculated rating for {student.user.get_full_name()}: {student.rating}")
        
        self.stdout.write(self.style.SUCCESS(f"Successfully calculated ratings for {count} students"))