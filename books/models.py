from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

#1. usuario
class CustomUser(AbstractUser):
    email = models.EmailField(max_length=200, unique=True)
    
    #requisito 5: rol de bibliotecario
    #default=False asegura que el registro público cree usuarios estándar sin permisos de gestión
    es_bibliotecario = models.BooleanField(default=False, verbose_name="¿Es bibliotecario?")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username

    #requisito 3: control de límite de préstamos
    #usamos @property para calcular el valor en tiempo real sin guardarlo en BD
    @property
    def num_libros_activos(self):
        return self.prestamos.filter(estado=Prestamo.Estado.ACTIVO).count()


#2. biblioteca
class Biblioteca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True) #identificador amigable para las URLs (SEO)
    
    def __str__(self):
        return self.nombre


#3. libro digital (requisito 4: archivos digitales)
class Libro(models.Model):
    isbn = models.CharField(max_length=13, unique=True)
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=100)
    genero = models.CharField(max_length=50) #permitirá filtrar por categorías en el frontend
    descripcion = models.TextField(blank=True)
    anio = models.PositiveIntegerField()
    
    portada = models.ImageField(upload_to='portadas/', blank=True)
    
    #requisito de seguridad:
    #guarda el archivo físico en el servidor 'media/libros_digitales/'
    #el acceso directo por URL estará protegido; la vista (views.py) verificará fechas y estado antes de servirlo
    archivo_digital = models.FileField(upload_to='libros_digitales/', help_text="Archivo del libro (.pdf, .html, etc)")
    
    #campo para generar el ranking "Top 10 más leídos"
    visitas_totales = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Libro Digital"
        verbose_name_plural = "Libros Digitales"
        ordering = ["-visitas_totales"] #orden predeterminado: primero los más populares

    def __str__(self):
        return self.titulo


#4. inventario (gestión de stock y licencias)
class Inventario(models.Model):
    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.CASCADE, related_name="inventario")
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="inventario_disponible")
    
    #simulación de licencias digitales concurrentes (eBiblio)
    #si licencias_ocupadas == licencias_totales, el libro no estará disponible
    licencias_totales = models.PositiveIntegerField(default=1)
    licencias_ocupadas = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Inventario de Licencias"
        #constraint: evita duplicar la ficha de un mismo libro en una misma biblioteca
        unique_together = ('biblioteca', 'libro')

    def __str__(self):
        disponibles = self.licencias_totales - self.licencias_ocupadas
        return f"{self.libro.titulo} ({disponibles} libres)"
    
    #propiedad auxiliar para simplificar la lógica en las vistas
    @property
    def hay_stock(self):
        return self.licencias_ocupadas < self.licencias_totales


#5. préstamo (requisito 3: caducidad automática y estados)
class Prestamo(models.Model):
    #máquina de estados para controlar el ciclo de vida del préstamo
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Leyendo"           #usuario tiene acceso al archivo
        FINALIZADO = "FINALIZADO", "Devuelto"  #usuario devolvió voluntariamente (libera licencia)
        CADUCADO = "CADUCADO", "Caducado"      #sistema revocó acceso por tiempo (libera licencia)

    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="prestamos")
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name="prestamos_activos")
    
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    
    #se calcula automáticamente en save(). editable=False evita manipulación manual en el Admin
    fecha_vencimiento = models.DateTimeField(editable=False) 
    
    #null=True permite que esté vacío mientras el libro está prestado. se rellena al devolver
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)

    class Meta:
        verbose_name = "Préstamo"
        ordering = ["-fecha_inicio"] #muestra los préstamos más recientes primero

    def save(self, *args, **kwargs):
        #lógica de creación (solo si no tiene ID):
        if not self.id:
            #1. establecer caducidad a 60 días
            self.fecha_vencimiento = timezone.now() + timedelta(days=60)
            #2. actualizar estadísticas del libro
            self.inventario.libro.visitas_totales += 1
            self.inventario.libro.save()
            
        super().save(*args, **kwargs)

    @property
    def dias_restantes(self):
        #cálculo dinámico de días para mostrar al usuario. retorna 0 si ya no está activo
        if self.estado != self.Estado.ACTIVO:
            return 0
        restante = self.fecha_vencimiento - timezone.now()
        return max(restante.days, 0)


#6. reseña (requisito 2: sistema de valoraciones)
class Reseña(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="resenas")
    #validadores aseguran que el rating esté estrictamente entre 1 y 5
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField()
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        #constraint: un usuario solo puede escribir UNA reseña por libro (evita spam)
        unique_together = ('usuario', 'libro')
        ordering = ["-creada_en"]

    def __str__(self):
        return f"{self.usuario.username} - {self.libro.titulo}"