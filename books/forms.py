from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Libro, Inventario, Reseña

#1. formulario de registro 
class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, help_text="")
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput, help_text="")

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password1", "password2")

#2. formulario de libro 
class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = [
            'isbn', 'titulo', 'autor', 'genero', 
            'anio', 'descripcion', 'portada', 'archivo_digital' 
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
        }

#3. Formulario de inventario
class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['biblioteca', 'licencias_totales']
        help_texts = {
            'licencias_totales': 'Número de licencias/copias digitales adquiridas.',
        }
        widgets = {
            'licencias_totales': forms.NumberInput(attrs={'min': 1}),
        }

#4. Formulario de reseña
class ResenaForm(forms.ModelForm):
    class Meta:
        model = Reseña
        fields = ['rating', 'comentario']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comentario': forms.Textarea(attrs={'rows': 3}),
        }