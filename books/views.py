from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import os
from django.http import FileResponse
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.views.generic import *
from .models import *
from .forms import *
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone


#la pantalla inicial, principal
def principal(request):
    return ListaLibro.as_view()(request)

def register(request):
    #muestra y procesa el formulario de registro
    if request.method == "POST":
        #si llega un post, validamos el formulario
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            #crea el usuario (es_bibliotecario queda en false por defecto)
            user = form.save()
            #inicia sesión automáticamente tras registrarse
            login(request, user)
            messages.success(request, "Te has registrado correctamente.")
            #redirige a la página principal
            return redirect("principal")
    else:
        #si llega un get, mostramos el formulario vacío
        form = CustomUserCreationForm()

    return render(request, "books/register.html", {"form": form})

class ListaLibro(ListView):
    #muestra la página principal y, si es bibliotecario, lista la librería
    model = Libro
    template_name = "books/principal.html"
    context_object_name = "libros"

    # bibliotecario ve librería + licencias + editar/eliminar
    # usuario normal ve catálogo con portadas/título/autor/género
    def get_queryset(self):
    #si no está autenticado, no mostramos lista
        if not self.request.user.is_authenticated:
            return Libro.objects.none()

        #si es bibliotecario, mostramos libros con licencias totales
        if self.request.user.es_bibliotecario:
            return (
                Libro.objects
                .annotate(
                    licencias_totales=Coalesce(
                        Sum("inventario_disponible__licencias_totales"), 0
                    ),
                    licencias_ocupadas=Coalesce(
                        Sum("inventario_disponible__licencias_ocupadas"), 0
                    ),
                )
                .annotate(
                    licencias_disponibles=F("licencias_totales") - F("licencias_ocupadas")
                )
                .order_by("titulo")
            )


        #si es usuario normal, mostramos catálogo completo sin botones
        return Libro.objects.all().order_by("titulo")


#si es bibliotecario y tiene una biblioteca asociada
def _es_bibliotecario(user):
    return user.is_authenticated and hasattr(user, "perfil") and user.perfil.es_bibliotecario and user.perfil.biblioteca


class LibroCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    #crea libros y permite acceso solo a bibliotecarios
    model = Libro
    form_class = LibroForm
    template_name = "books/libro_form.html"
    success_url = reverse_lazy("principal")

    def test_func(self):
        #solo bibliotecarios pueden acceder
        return self.request.user.es_bibliotecario
    
class LibroUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    #edita libros y permite acceso solo a bibliotecarios
    model = Libro
    form_class = LibroForm
    template_name = "books/libro_form.html"
    success_url = reverse_lazy("principal")

    def test_func(self):
        #solo bibliotecarios pueden acceder
        return self.request.user.es_bibliotecario
    
class LibroDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    #elimina libros y permite acceso solo a bibliotecarios
    model = Libro
    template_name = "books/libro_confirm_delete.html"
    success_url = reverse_lazy("principal")

    def test_func(self):
        #solo bibliotecarios pueden acceder
        return self.request.user.es_bibliotecario
    
def filtrar_libros(request):
    #filtra libros por título y/o categoría para bibliotecarios
    if not request.user.is_authenticated or not request.user.es_bibliotecario:
        return redirect("principal")

    titulo = request.GET.get("titulo", "").strip()
    genero = request.GET.get("genero", "").strip()

    libros = (
    Libro.objects
    .annotate(
        licencias_totales=Coalesce(Sum("inventario_disponible__licencias_totales"), 0),
        licencias_ocupadas=Coalesce(Sum("inventario_disponible__licencias_ocupadas"), 0),
    )
    .annotate(
        licencias_disponibles=F("licencias_totales") - F("licencias_ocupadas")
    )
    .order_by("titulo")
)


    #si viene título, filtramos por coincidencia parcial
    if titulo:
        libros = libros.filter(titulo__icontains=titulo)

    #si viene género, filtramos por coincidencia parcial (permite escribir "fan" y filtra fantasía)
    if genero:
        libros = libros.filter(genero__icontains=genero)

    #renderiza principal con el resultado
    return render(request, "books/principal.html", {"libros": libros})

def catalogo(request):
    #muestra el catálogo para usuarios autenticados con filtros por título y categoría
    if not request.user.is_authenticated:
        return redirect("login")

    titulo = request.GET.get("titulo", "").strip()
    genero = request.GET.get("genero", "").strip()

    libros = Libro.objects.all().order_by("titulo")

    #si viene título, filtramos por coincidencia parcial
    if titulo:
        libros = libros.filter(titulo__icontains=titulo)

    #si viene género, filtramos por coincidencia parcial
    if genero:
        libros = libros.filter(genero__icontains=genero)

    #renderiza la principal reutilizando la lista
    return render(request, "books/principal.html", {"libros": libros})

class LibroDetailView(LoginRequiredMixin, DetailView):
    model = Libro
    template_name = "books/libro_detail.html"
    context_object_name = "libro"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        #busca inventario del libro (el primero, si hay varios)
        inventario = self.object.inventario_disponible.first()
        context["inventario_id"] = inventario.id if inventario else None

        #comprueba si el usuario ya tiene un préstamo activo de este libro
        if self.request.user.is_authenticated and not self.request.user.es_bibliotecario:
            context["prestamo_activo"] = Prestamo.objects.filter(
                usuario=self.request.user,
                inventario__libro=self.object,
                estado=Prestamo.Estado.ACTIVO,
            ).exists()
        else:
            context["prestamo_activo"] = False

        return context


@login_required
def prestar_libro(request, inventario_id):
    #realizamos un préstamo si hay licencias y no supera 3 activos

    if request.user.es_bibliotecario:
        messages.error(request, "Los bibliotecarios no pueden realizar préstamos.")
        return redirect("principal")

    #autodevolución: caduca préstamos vencidos y libera licencias
    vencidos = (
        Prestamo.objects
        .filter(
            usuario=request.user,
            estado=Prestamo.Estado.ACTIVO,
            fecha_vencimiento__lt=timezone.now(),
        )
        .select_related("inventario")
    )

    for p in vencidos:
        p.estado = Prestamo.Estado.CADUCADO
        p.fecha_devolucion = timezone.now()
        p.save(update_fields=["estado", "fecha_devolucion"])

        inv = p.inventario
        if inv.licencias_ocupadas > 0:
            inv.licencias_ocupadas -= 1
            inv.save(update_fields=["licencias_ocupadas"])

    #límite de 3 préstamos activos
    if request.user.num_libros_activos >= 3:
        messages.error(request, "Has alcanzado el límite de 3 préstamos activos.")
        return redirect("principal")

    inventario = get_object_or_404(Inventario, id=inventario_id)

    #evitar préstamo duplicado del mismo libro/inventario
    ya_activo = Prestamo.objects.filter(
        usuario=request.user,
        inventario=inventario,
        estado=Prestamo.Estado.ACTIVO,
    ).exists()

    if ya_activo:
        messages.info(request, "Ya tienes este libro en préstamo.")
        return redirect("libro_detalle", pk=inventario.libro.pk)

    #stock
    if not inventario.hay_stock:
        messages.error(request, "No hay licencias disponibles para este libro.")
        return redirect("libro_detalle", pk=inventario.libro.pk)

    #ocupar licencia
    inventario.licencias_ocupadas += 1
    inventario.save(update_fields=["licencias_ocupadas"])

    #crear préstamo
    Prestamo.objects.create(usuario=request.user, inventario=inventario)

    messages.success(request, "Préstamo realizado. Ya puedes leer el libro.")
    return redirect("libro_detalle", pk=inventario.libro.pk)


@login_required
def leer_libro_por_libro(request, libro_id):
    #abre el libro en navegador si el usuario tiene un préstamo activo de ese libro

    #busca el libro
    libro = get_object_or_404(Libro, id=libro_id)

    #busca un préstamo activo de ese usuario para ese libro
    prestamo = Prestamo.objects.filter(
        usuario=request.user,
        inventario__libro=libro,
        estado=Prestamo.Estado.ACTIVO,
    ).select_related("inventario").first()

    #si no hay préstamo activo, no se permite leer
    if not prestamo:
        messages.error(request, "Necesitas pedir el préstamo para poder leer este libro.")
        return redirect("libro_detalle", pk=libro.id)

    #si el préstamo venció, lo caduca y bloquea acceso
    if prestamo.fecha_vencimiento < timezone.now():
        prestamo.estado = Prestamo.Estado.CADUCADO
        prestamo.fecha_devolucion = timezone.now()
        prestamo.save(update_fields=["estado", "fecha_devolucion"])

        inv = prestamo.inventario
        if inv.licencias_ocupadas > 0:
            inv.licencias_ocupadas -= 1
            inv.save(update_fields=["licencias_ocupadas"])

        messages.error(request, "Tu préstamo ha caducado. Ya no puedes acceder al libro.")
        return redirect("libro_detalle", pk=libro.id)

    #obtiene el archivo digital
    archivo = libro.archivo_digital
    if not archivo:
        messages.error(request, "Este libro no tiene archivo digital.")
        return redirect("libro_detalle", pk=libro.id)

    #content type correcto para que se muestre en navegador
    nombre = archivo.name.lower()
    if nombre.endswith(".pdf"):
        content_type = "application/pdf"
    elif nombre.endswith(".html") or nombre.endswith(".htm"):
        content_type = "text/html"
    else:
        content_type = "application/octet-stream"

    filename = os.path.basename(archivo.name)

    #si es pdf, mostramos visor html embebido
    if archivo.name.lower().endswith(".pdf"):
        return render(request, "books/visor_pdf.html", {
            "libro": libro,
            "pdf_url": reverse("stream_pdf", args=[prestamo.id]),
        })

    return redirect("libro_detalle", pk=libro.id)

from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.urls import reverse


@xframe_options_sameorigin
@login_required
def stream_pdf(request, prestamo_id):
    #sirve el pdf para el visor embebido solo si el préstamo está activo

    prestamo = get_object_or_404(
        Prestamo,
        id=prestamo_id,
        usuario=request.user,
        estado=Prestamo.Estado.ACTIVO,
    )

    archivo = prestamo.inventario.libro.archivo_digital
    if not archivo or not archivo.name.lower().endswith(".pdf"):
        messages.error(request, "Este libro no tiene PDF disponible.")
        return redirect("libro_detalle", pk=prestamo.inventario.libro.pk)

    response = FileResponse(archivo.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="libro.pdf"'
    response["Cache-Control"] = "no-store"
    return response

