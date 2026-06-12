from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta


#1. usuario
class CustomUser(AbstractUser):
    email = models.EmailField(max_length=200, unique=True)
    
    #rol para diferenciar usuario normal de bibliotecario
    #si es false se registra como usuario normal
    es_bibliotecario = models.BooleanField(default=False, verbose_name="¿Es bibliotecario?")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username

    #devuelve cuantos libros tiene prestados actualmente
    #no se guarda en la bd, se calcula cada vez
    @property
    def num_libros_activos(self):
        return self.prestamos.filter(estado=Prestamo.Estado.ACTIVO).count()


#2. biblioteca
class Biblioteca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True) #para urls mas limpias
    
    def __str__(self):
        return self.nombre


#3. libro digital
class Libro(models.Model):
    #uso el isbn como clave primaria porque es unico
    isbn = models.CharField(max_length=13, primary_key=True)
    
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=100)
    genero = models.CharField(max_length=50) #sirve para filtrar por categorias
    descripcion = models.TextField(blank=True)
    anio = models.PositiveIntegerField()
    
    portada = models.ImageField(upload_to='portadas/', blank=True)
    
    #aqui se guarda el pdf o archivo digital del libro
    #se almacena dentro de media/libros_digitales
    archivo_digital = models.FileField(upload_to='libros_digitales/', help_text="Archivo del libro (.pdf, .html, etc)")
    
    #contador para saber cuales son los mas leidos
    visitas_totales = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Libro Digital"
        verbose_name_plural = "Libros Digitales"
        ordering = ["-visitas_totales"] #ordenados por popularidad

    def __str__(self):
        return self.titulo


#4. inventario
class Inventario(models.Model):
    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.CASCADE, related_name="inventario")
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="inventario_disponible")
    
    #simula licencias digitales tipo eBiblio
    licencias_totales = models.PositiveIntegerField(default=1)
    licencias_ocupadas = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Inventario de Licencias"
        #evita que el mismo libro se duplique en la misma biblioteca
        unique_together = ('biblioteca', 'libro')

    def __str__(self):
        disponibles = self.licencias_totales - self.licencias_ocupadas
        return f"{self.libro.titulo} ({disponibles} libres)"
    
    #comprueba si queda alguna licencia libre
    @property
    def hay_stock(self):
        return self.licencias_ocupadas < self.licencias_totales
    
    #calcula cuantas quedan disponibles
    @property
    def licencias_disponibles(self):
        return self.licencias_totales - self.licencias_ocupadas


#5. prestamo
class Prestamo(models.Model):

    #estados posibles del prestamo
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Leyendo"
        FINALIZADO = "FINALIZADO", "Devuelto"
        CADUCADO = "CADUCADO", "Caducado"

    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="prestamos")
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name="prestamos_activos")
    
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    
    #se calcula automaticamente al crear el prestamo
    fecha_vencimiento = models.DateTimeField(editable=False)
    
    #se rellena cuando se devuelve
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)

    class Meta:
        verbose_name = "Préstamo"
        ordering = ["-fecha_inicio"]

    def save(self, *args, **kwargs):
        #solo cuando se crea por primera vez
        if not self.id:

            #comprueba que haya licencias disponibles
            if self.inventario.licencias_ocupadas >= self.inventario.licencias_totales:
                raise ValueError("No hay licencias disponibles para este libro.")

            #ocupa una licencia
            self.inventario.licencias_ocupadas += 1
            self.inventario.save()

            #establece duracion de 60 dias
            self.fecha_vencimiento = timezone.now() + timedelta(days=60)

            #aumenta contador de visitas
            self.inventario.libro.visitas_totales += 1
            self.inventario.libro.save()
            
        super().save(*args, **kwargs)

    #devuelve el libro manualmente
    def devolver(self):
        if self.estado == self.Estado.ACTIVO:
            self.estado = self.Estado.FINALIZADO
            self.fecha_devolucion = timezone.now()
            self.save(update_fields=["estado", "fecha_devolucion"])

            #libera la licencia ocupada
            self.inventario.licencias_ocupadas = max(self.inventario.licencias_ocupadas - 1, 0)
            self.inventario.save()

    #calcula dias restantes para mostrar al usuario
    @property
    def dias_restantes(self):
        if self.estado != self.Estado.ACTIVO:
            return 0
        restante = self.fecha_vencimiento - timezone.now()
        return max(restante.days, 0)


#6. reseña
class Reseña(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="resenas")
    
    #valoracion entre 1 y 5
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    comentario = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        #un usuario solo puede poner una reseña por libro
        unique_together = ('usuario', 'libro')
        ordering = ["-creada_en"]

    def __str__(self):
        return f"{self.usuario.username} - {self.libro.titulo}"