import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookflare.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

user, created = User.objects.get_or_create(
    username="admin",
    defaults={"email": "admin@gmail.com"}
)

user.set_password("Admin12345")
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()

print("Admin corregido correctamente")