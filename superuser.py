import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docpulse_core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

phone = '9999999999'
password = 'admin123'
name = 'Internal Admin'

if not User.objects.filter(phone=phone).exists():
    User.objects.create_superuser(
        phone=phone,
        password=password,
        name=name
    )
    print(f"Superuser {phone} created successfully.")
else:
    print(f"Superuser {phone} already exists.")