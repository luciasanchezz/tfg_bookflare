from django.contrib import admin
from .models import Biblioteca, Libro,Perfil, Ejemplar, Reseña, Importacion

# Register your models here.
admin.site.register(Biblioteca)
admin.site.register(Libro)
admin.site.register(Perfil)
admin.site.register(Ejemplar)
admin.site.register(Reseña)
admin.site.register(Importacion)