from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

#Usuario para personalizar
class CustomUser(AbstractUser):
    nick = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=200, unique=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["nick"]

    def __str__(self):
        return self.username


#Biblioteca
class Biblioteca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    direccion = models.CharField(max_length=200)
    email_contacto = models.EmailField(max_length=200)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Biblioteca"
        verbose_name_plural = "Bibliotecas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


#Libro
class Libro(models.Model):
    isbn = models.CharField(primary_key=True, max_length=13)
    titulo = models.CharField(max_length=30)
    autor = models.CharField(max_length=50)
    genero = models.CharField(max_length=30)
    anio = models.PositiveIntegerField()
    portada_url = models.URLField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ["titulo"]

    def __str__(self):
        return f"{self.titulo} ({self.isbn})"


#Perfil
class Perfil(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="perfil")
    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.SET_NULL, null=True, blank=True, related_name="perfiles")
    es_bibliotecario = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        rol = "Bibliotecario" if self.es_bibliotecario else "Personal"
        return f"{self.usuario} y es {rol}"


#Ejemplar
class Ejemplar(models.Model):
    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.CASCADE, related_name="ejemplares")
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="ejemplares")
    cantidad_total = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    cantidad_disponible = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = "Ejemplar"
        verbose_name_plural = "Ejemplares"
        constraints = [
            models.UniqueConstraint(
                fields=["biblioteca", "libro"],
                name="unique_ejemplar_por_libro_en_biblioteca",
            ),
            models.CheckConstraint(
                check=models.Q(cantidad_disponible__lte=models.F("cantidad_total")),
                name="ejemplar_disponible_no_supera_total",
            ),
        ]

    def __str__(self):
        return f"{self.libro.titulo} en {self.biblioteca.nombre}"


#Reseña
class Reseña(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="resenas")
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="resenas")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering = ["-creada_en"]
        constraints = [
            models.UniqueConstraint(fields=["usuario", "libro"], name="unique_resena_por_usuario_y_libro"),
        ]

    def __str__(self):
        return f"{self.usuario} → {self.libro.titulo} ({self.rating}/5)"


#Importaciones
class Importacion(models.Model):
    class Formato(models.TextChoices):
        JSON = "JSON", "JSON"

    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.CASCADE, related_name="importaciones")
    formato = models.CharField(max_length=10, choices=Formato.choices)
    archivo_nombre = models.CharField(max_length=200)
    nuevas = models.PositiveIntegerField(default=0)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Importación"
        verbose_name_plural = "Importaciones"
        ordering = ["-creada_en"]

    def __str__(self):
        return f"{self.formato} - ({self.archivo_nombre})"
