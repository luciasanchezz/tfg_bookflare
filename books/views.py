from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.views.generic import *
from .models import *
from .forms import *
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import Avg
import os


# HOME 
def principal(request):
    libros = Libro.objects.all().order_by("genero", "titulo")

    generos = {}
    for libro in libros:
        if libro.genero not in generos:
            generos[libro.genero] = []
        generos[libro.genero].append(libro)

    return render(request, "books/principal.html", {
        "generos": generos
    })

# CATÁLOGO (para usuarios autenticados)
def catalogo(request):
    if not request.user.is_authenticated:
        return redirect("login")

    titulo = request.GET.get("titulo", "").strip()
    genero = request.GET.get("genero", "").strip()

    libros = Libro.objects.order_by("titulo")

    if titulo:
        libros = libros.filter(titulo__icontains=titulo)

    if genero:
        libros = libros.filter(genero__icontains=genero)

    return render(request, "books/principal.html", {"libros": libros})


# FILTRAR (buscador para bibliotecarios)
def filtrar_libros(request):
    if not request.user.is_authenticated or not request.user.es_bibliotecario:
        return redirect("principal")

    titulo = request.GET.get("titulo", "").strip()
    genero = request.GET.get("genero", "").strip()

    libros = (Libro.objects
        .annotate(
            licencias_totales=Coalesce(Sum("inventario_disponible__licencias_totales"), 0),
            licencias_ocupadas=Coalesce(Sum("inventario_disponible__licencias_ocupadas"), 0),
        )
        .annotate(licencias_disponibles=F("licencias_totales") - F("licencias_ocupadas"))
        .order_by("titulo")
    )

    if titulo:
        libros = libros.filter(titulo__icontains=titulo)

    if genero:
        libros = libros.filter(genero__icontains=genero)

    return render(request, "books/principal.html", {"libros": libros})

# REGISTRO
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Te has registrado correctamente.")
            return redirect("principal")
    else:
        form = CustomUserCreationForm()

    return render(request, "books/register.html", {"form": form})


# LISTA LIBROS
class ListaLibro(ListView):
    model = Libro
    template_name = "books/principal.html"
    context_object_name = "libros"

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Libro.objects.none()

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

        return Libro.objects.all().order_by("titulo")


# CRUD LIBROS (BIBLIOTECARIO)
class LibroCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Libro
    form_class = LibroForm
    template_name = "books/libro_form.html"
    success_url = reverse_lazy("principal")

    def test_func(self):
        return self.request.user.es_bibliotecario


class LibroUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Libro
    form_class = LibroForm
    template_name = "books/libro_form.html"
    success_url = reverse_lazy("principal")
    pk_url_kwarg = "isbn"

    def test_func(self):
        return self.request.user.es_bibliotecario


class LibroDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Libro
    template_name = "books/libro_confirm_delete.html"
    success_url = reverse_lazy("principal")
    pk_url_kwarg = "isbn"

    def test_func(self):
        return self.request.user.es_bibliotecario


# DETALLE LIBRO
class LibroDetailView(DetailView):
    model = Libro
    template_name = "books/libro_detail.html"
    context_object_name = "libro"
    slug_field = "isbn"
    slug_url_kwarg = "isbn"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        libro = self.object
        # RESEÑAS
        resenas = (
            Reseña.objects
            .filter(libro=libro)
            .select_related("usuario")
            .order_by("-creada_en")
        )

        context["resenas"] = resenas
        context["media_rating"] = resenas.aggregate(media=Avg("rating"))["media"]

        # INVENTARIO
        inventario = Inventario.objects.filter(libro=libro).first()
        context["inventario"] = inventario

        # PRÉSTAMO ACTIVO
        prestamo = None
        if self.request.user.is_authenticated:
            prestamo = Prestamo.objects.filter(
                usuario=self.request.user,
                inventario__libro=libro,
                estado=Prestamo.Estado.ACTIVO
            ).first()

        context["prestamo"] = prestamo

        # PUEDE RESEÑAR
        puede_resenar = False

        if self.request.user.is_authenticated:
            ha_leido = Prestamo.objects.filter(
                usuario=self.request.user,
                inventario__libro=libro,
                estado=Prestamo.Estado.FINALIZADO
            ).exists()

            ya_reseno = Reseña.objects.filter(
                usuario=self.request.user,
                libro=libro
            ).exists()

            if ha_leido and not ya_reseno:
                puede_resenar = True

        context["puede_resenar"] = puede_resenar

        return context


# PRESTAR LIBRO
@login_required
def prestar_libro(request, inventario_id):

    if request.user.es_bibliotecario:
        messages.error(request, "Los bibliotecarios no pueden realizar préstamos.")
        return redirect("principal")

    if request.user.num_libros_activos >= 3:
        messages.error(request, "Has alcanzado el límite de 3 préstamos activos.")
        return redirect("principal")

    inventario = get_object_or_404(Inventario, id=inventario_id)

    if not inventario.hay_stock:
        messages.error(request, "No hay licencias disponibles.")
        return redirect("libro_detalle", isbn=inventario.libro.isbn)

    try:
        Prestamo.objects.create(usuario=request.user, inventario=inventario)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("libro_detalle", isbn=inventario.libro.isbn)

    messages.success(request, "Préstamo realizado correctamente.")
    return redirect("libro_detalle", isbn=inventario.libro.isbn)


# LEER LIBRO
@login_required
def leer_libro(request, isbn):

    libro = get_object_or_404(Libro, isbn=isbn)

    prestamo = Prestamo.objects.filter(
        usuario=request.user,
        inventario__libro=libro,
        estado=Prestamo.Estado.ACTIVO,
    ).first()

    if not prestamo:
        messages.error(request, "Necesitas un préstamo activo.")
        return redirect("libro_detalle", isbn=isbn)

    if prestamo.fecha_vencimiento < timezone.now():
        prestamo.devolver()
        messages.error(request, "Tu préstamo ha caducado.")
        return redirect("libro_detalle", isbn=isbn)

    archivo = libro.archivo_digital
    if not archivo:
        messages.error(request, "Este libro no tiene archivo digital.")
        return redirect("libro_detalle", isbn=isbn)

    return render(request, "books/visor_pdf.html", {
        "libro": libro,
        "pdf_url": reverse("stream_pdf", args=[prestamo.id]),
    })


# STREAM PDF
@xframe_options_sameorigin
@login_required
def stream_pdf(request, prestamo_id):

    prestamo = get_object_or_404(
        Prestamo,
        id=prestamo_id,
        usuario=request.user,
        estado=Prestamo.Estado.ACTIVO,
    )

    archivo = prestamo.inventario.libro.archivo_digital

    response = FileResponse(archivo.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="libro.pdf"'
    response["Cache-Control"] = "no-store"
    return response

class ResenaCreateView(LoginRequiredMixin, CreateView):
    model = Reseña
    form_class = ResenaForm
    template_name = "books/resena_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.libro = get_object_or_404(Libro, isbn=self.kwargs["isbn"])

        # verificar que ha tenido préstamo finalizado
        ha_leido = Prestamo.objects.filter(
            usuario=request.user,
            inventario__libro=self.libro,
            estado=Prestamo.Estado.FINALIZADO
        ).exists()

        if not ha_leido:
            messages.error(request, "Debes haber leído el libro para reseñarlo.")
            return redirect("libro_detalle", isbn=self.libro.isbn)

        # verificar que no haya reseñado ya
        if Reseña.objects.filter(usuario=request.user, libro=self.libro).exists():
            messages.error(request, "Ya has reseñado este libro.")
            return redirect("libro_detalle", isbn=self.libro.isbn)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.libro = self.libro
        messages.success(self.request, "Reseña publicada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("libro_detalle", args=[self.libro.isbn])
    
@login_required
def devolver_libro(request, prestamo_id):
    prestamo = get_object_or_404(
        Prestamo,
        id=prestamo_id,
        usuario=request.user,
        estado=Prestamo.Estado.ACTIVO
    )

    prestamo.devolver()

    messages.success(request, "Libro devuelto correctamente.")

    return redirect("libro_detalle", isbn=prestamo.inventario.libro.isbn)

class ResenaCreateView(LoginRequiredMixin, CreateView):
    model = Reseña
    form_class = ResenaForm
    template_name = "books/resena_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.libro = get_object_or_404(Libro, isbn=self.kwargs["isbn"])

        # Debe haber tenido préstamo finalizado
        ha_leido = Prestamo.objects.filter(
            usuario=request.user,
            inventario__libro=self.libro,
            estado=Prestamo.Estado.FINALIZADO
        ).exists()

        if not ha_leido:
            messages.error(request, "Debes haber leído el libro para reseñarlo.")
            return redirect("libro_detalle", isbn=self.libro.isbn)

        # No puede reseñar dos veces
        if Reseña.objects.filter(usuario=request.user, libro=self.libro).exists():
            messages.error(request, "Ya has reseñado este libro.")
            return redirect("libro_detalle", isbn=self.libro.isbn)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.libro = self.libro
        messages.success(self.request, "Reseña publicada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("libro_detalle", args=[self.libro.isbn])
    
class ListaResenasView(ListView):
    model = Reseña
    template_name = "books/lista_resenas.html"
    context_object_name = "resenas"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Reseña.objects
            .select_related("usuario", "libro")
            .order_by("-creada_en")
        )

        titulo = self.request.GET.get("titulo")
        genero = self.request.GET.get("genero")
        ordenar = self.request.GET.get("ordenar")

        if titulo:
            queryset = queryset.filter(libro__titulo__icontains=titulo)

        if genero:
            queryset = queryset.filter(libro__genero__icontains=genero)

        if ordenar == "mejor":
            queryset = queryset.order_by("-rating", "-creada_en")

        return queryset