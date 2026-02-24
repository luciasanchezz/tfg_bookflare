from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Biblioteca, Libro, Inventario, Prestamo, Reseña

#1. registro de usuario personalizado
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Permisos de Biblioteca", {"fields": ("es_bibliotecario",)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Permisos de Biblioteca", {"fields": ("es_bibliotecario",)}),
    )

    list_display = ["username", "email", "es_bibliotecario", "is_staff", "is_active"]
    list_filter = ["es_bibliotecario", "is_staff", "is_active"]

#2. registro de biblioteca
@admin.register(Biblioteca)
class BibliotecaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug']
    prepopulated_fields = {'slug': ('nombre',)} #se rellena solo al escribir el nombre

#3. registro de libro (catálogo)
@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'isbn', 'genero', 'visitas_totales']
    search_fields = ['titulo', 'autor', 'isbn']
    list_filter = ['genero', 'anio']
    # imagen de portada en pequeño
    #readonly_fields = ['visitas_totales']

#4. registro de inventario (stock)
@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    #optimización: carga los datos relacionados en la misma consulta SQL
    list_select_related = ('libro', 'biblioteca')
    
    list_display = ['libro', 'biblioteca', 'licencias_ocupadas', 'licencias_totales', 'hay_stock']
    list_filter = ['biblioteca']
    
    #permite buscar por título del libro desde aquí
    search_fields = ['libro__titulo']

#5. registro de préstamo
@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_select_related = ('usuario', 'inventario', 'inventario__libro')
    list_display = ['usuario', 'obtener_libro', 'estado', 'fecha_inicio', 'dias_restantes']
    list_filter = ['estado', 'fecha_inicio']
    search_fields = ['usuario__username', 'inventario__libro__titulo']

    #función auxiliar para mostrar el título del libro en la tabla
    @admin.display(description='Libro')
    def obtener_libro(self, obj):
        return obj.inventario.libro.titulo

#6. registro de reseñas
@admin.register(Reseña)
class ResenaAdmin(admin.ModelAdmin):
    list_select_related = ('usuario', 'libro')
    list_display = ['usuario', 'libro', 'rating', 'creada_en']
    list_filter = ['rating']