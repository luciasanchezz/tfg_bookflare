from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(
        username="admin",
        email="tuemail@gmail.com",
        password="UnaPasswordSegura123"
    )
    print("Superusuario creado")
else:
    print("Superusuario ya existe")