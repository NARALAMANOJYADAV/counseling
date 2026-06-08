import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student.settings')
django.setup()

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from counseling.models import StudentCounseling, Grievance

users_to_create = [
    ('MANOJ', 'manoj@007', True),
    ('COUNSELOR', 'counselor@007', False),
    ('HOD', 'hod@007', False),
    ('INCHARGE', 'incharge@007', False),
    ('DIRECTOR', 'director@007', False),
]

# Permissions to grant
sc_content_type = ContentType.objects.get_for_model(StudentCounseling)
gr_content_type = ContentType.objects.get_for_model(Grievance)

sc_perms = Permission.objects.filter(content_type=sc_content_type)
gr_perms = Permission.objects.filter(content_type=gr_content_type)

for username, password, is_super in users_to_create:
    user, created = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = is_super
    user.save()
    
    if not is_super:
        # Give them change/view permissions for both models
        for perm in sc_perms:
            user.user_permissions.add(perm)
        for perm in gr_perms:
            user.user_permissions.add(perm)
    
    status = "Created" if created else "Updated"
    print(f"{status} user {username} and granted permissions.")
