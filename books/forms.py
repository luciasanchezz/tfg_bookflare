from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Libro, Inventario, Reseña


#Formulario de registro
class CustomUserCreationForm(UserCreationForm):

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="La contraseña debe cumplir los requisitos de seguridad."
    )

    password2 = forms.CharField(
        label="Repite la contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Introduce la misma contraseña para confirmarla."
    )

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


#Formulario de libro digital
class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = [
            'isbn',
            'titulo',
            'autor',
            'genero',
            'anio',
            'descripcion',
            'portada',
            'archivo_digital'
        ]
        widgets = {
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'autor': forms.TextInput(attrs={'class': 'form-control'}),
            'genero': forms.TextInput(attrs={'class': 'form-control'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }


#Formulario de inventario (licencias digitales)
#no incluimos biblioteca porque se asigna automáticamente en la vista
class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['licencias_totales']
        help_texts = {
            'licencias_totales': 'Número de licencias digitales disponibles en la biblioteca.',
        }
        widgets = {
            'licencias_totales': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }


#Formulario de reseña
class ResenaForm(forms.ModelForm):
    class Meta:
        model = Reseña
        fields = ['rating', 'comentario']
        widgets = {
            # lo ocultamos, lo rellenará JS al pulsar estrella
            'rating': forms.HiddenInput(),
            'comentario': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Escribe tu opinión (opcional)...'
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if not rating:
            raise forms.ValidationError("Debes seleccionar una puntuación.")
        return rating
    

class ResenaForm(forms.ModelForm):
    class Meta:
        model = Reseña
        fields = ['rating', 'comentario']
        widgets = {
            'rating': forms.HiddenInput(),
            'comentario': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Escribe tu opinión (opcional)...'
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if not rating:
            raise forms.ValidationError("Debes seleccionar una puntuación.")
        return rating