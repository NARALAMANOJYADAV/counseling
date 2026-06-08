import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student.settings')
django.setup()

User = get_user_model()
username = 'MANOJ'
password = 'manoj@007'
email = 'admin@example.com'

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser {username}...")
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Superuser created successfully.")
else:
    print(f"Superuser {username} already exists.")
    # Optional: Update password if needed
    u = User.objects.get(username=username)
    u.set_password(password)
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print("Superuser credentials updated.")
