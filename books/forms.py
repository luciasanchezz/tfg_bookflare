from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Libro, Inventario, Reseña


#formulario de registro de usuario
class CustomUserCreationForm(UserCreationForm):

    #sobreescribo password1 para poder darle estilo
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="La contraseña debe cumplir los requisitos de seguridad."
    )

    #confirmacion de contraseña
    password2 = forms.CharField(
        label="Repite la contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Introduce la misma contraseña para confirmarla."
    )

    class Meta:
        model = CustomUser

        #campos que quiero mostrar en el formulario
        fields = ("username", "email", "password1", "password2")

        #aqui solo aplico clases css para que se vea mejor
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


#formulario para crear o editar libro
class LibroForm(forms.ModelForm):

    class Meta:
        model = Libro

        #campos del modelo libro que permito editar
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

        #solo es para dar formato visual
        widgets = {
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'autor': forms.TextInput(attrs={'class': 'form-control'}),
            'genero': forms.TextInput(attrs={'class': 'form-control'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }


#formulario para definir numero de licencias digitales
#no incluyo biblioteca porque se asigna desde la vista
class InventarioForm(forms.ModelForm):

    class Meta:
        model = Inventario

        #solo permito modificar licencias_totales
        fields = ['licencias_totales']

        #mensaje informativo debajo del campo
        help_texts = {
            'licencias_totales': 'Número de licencias digitales disponibles en la biblioteca.',
        }

        #minimo 1 licencia
        widgets = {
            'licencias_totales': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }


#formulario de reseña
class ResenaForm(forms.ModelForm):

    class Meta:
        model = Reseña

        #solo rating y comentario
        fields = ['rating', 'comentario']

        widgets = {
            #rating se oculta porque lo controlo con estrellas en js
            'rating': forms.HiddenInput(),

            #textarea para opinion
            'comentario': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Escribe tu opinión (opcional)...'
            }),
        }

    #valido que el usuario haya elegido puntuacion
    def clean_rating(self):

        rating = self.cleaned_data.get("rating")

        #si no hay valor lanzo error
        if not rating:
            raise forms.ValidationError("Debes seleccionar una puntuación.")

        return rating