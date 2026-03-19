import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student.settings')
django.setup()

from django.contrib.auth.models import User
from counseling.models import StudentCounseling, Grievance

# Delete non-staff users
students = User.objects.filter(is_staff=False, is_superuser=False)
print(f"Deleting {students.count()} user accounts (students)...")
students.delete()

# Delete their records
counseling_count = StudentCounseling.objects.all().count()
print(f"Deleting {counseling_count} counseling forms...")
StudentCounseling.objects.all().delete()

grievance_count = Grievance.objects.all().count()
print(f"Deleting {grievance_count} grievances...")
Grievance.objects.all().delete()

print("Database cleared of all student logins and records. Faculty logins preserved.")
