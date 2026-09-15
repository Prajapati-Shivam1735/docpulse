import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docpulse_core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

phone_number = '9999999999'
password = 'admin123'
full_name = 'Internal Admin'

if not User.objects.filter(phone_number=phone_number).exists():
    User.objects.create_superuser(
        phone_number=phone_number,
        password=password,
        full_name=full_name
    )
    print(f"Superuser {phone_number} created successfully.")
else:
    print(f"Superuser {phone_number} already exists.")