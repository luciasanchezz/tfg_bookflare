import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookflare.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(
        username="admin",
        email="admin@gmail.com",
        password="Admin12345"
    )
    print("Superusuario creado")
else:
    print("Superusuario ya existe")