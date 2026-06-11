from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse, HttpResponseForbidden
from django.db.models import Sum, F, Q
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
from django.db.models import Avg, Count


# HOME 
def principal(request):

    query = request.GET.get("q", "")
    genero = request.GET.get("genero", "")

    libros = Libro.objects.all()

    # 🔍 FILTRO POR TÍTULO
    if query:
        libros = libros.filter(
            Q(titulo__icontains=query)
        )

    # 🏷 FILTRO POR GÉNERO
    if genero:
        libros = libros.filter(
            Q(genero__icontains=genero)
        )

    # Agrupar por género
    generos = {}
    for libro in libros:
        generos.setdefault(libro.genero, []).append(libro)

    context = {
        "generos": generos,
        "query": query,
        "genero_seleccionado": genero,
    }

    return render(request, "books/principal.html", context)

#CATÁLOGO(para usuarios autenticados)
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
    fields = "__all__"
    template_name = "books/libro_form.html"
    slug_field = "isbn"
    slug_url_kwarg = "isbn"

    def test_func(self):
        return self.request.user.es_bibliotecario

    def get_success_url(self):
        return reverse("libro_detalle", args=[self.object.isbn])


class LibroDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Libro
    template_name = "books/libro_confirm_delete.html"
    success_url = reverse_lazy("principal")
    slug_field = "isbn"
    slug_url_kwarg = "isbn"

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
        user = self.request.user

        # ======================
        # RESEÑAS
        # ======================
        resenas = (
            Reseña.objects
            .filter(libro=libro)
            .select_related("usuario")
            .order_by("-creada_en")
        )

        context["resenas"] = resenas
        context["media_rating"] = resenas.aggregate(media=Avg("rating"))["media"]

        # ======================
        # INVENTARIO
        # ======================
        inventario = Inventario.objects.filter(libro=libro).first()
        context["inventario"] = inventario

        # ======================
        # PRÉSTAMO ACTIVO DEL LIBRO
        # ======================
        prestamo = None
        if user.is_authenticated:
            prestamo = Prestamo.objects.filter(
                usuario=user,
                inventario__libro=libro,
                estado=Prestamo.Estado.ACTIVO
            ).first()

        context["prestamo"] = prestamo

        # ======================
        # LÍMITE DE 3 PRÉSTAMOS
        # ======================
        puede_pedir = True

        if user.is_authenticated:
            prestamos_activos = Prestamo.objects.filter(
                usuario=user,
                estado=Prestamo.Estado.ACTIVO
            ).count()

            if prestamos_activos >= 3:
                puede_pedir = False

        context["puede_pedir"] = puede_pedir

        # ======================
        # PUEDE RESEÑAR
        # ======================
        puede_resenar = False

        if user.is_authenticated:
            ha_leido = Prestamo.objects.filter(
                usuario=user,
                inventario__libro=libro,
                estado=Prestamo.Estado.FINALIZADO
            ).exists()

            ya_reseno = Reseña.objects.filter(
                usuario=user,
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
        "pdf_url": libro.archivo_digital.url,
    })



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
    
class ListaResenasView(ListView):
    model = Reseña
    template_name = "books/lista_resenas.html"
    context_object_name = "resenas"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Reseña.objects
            .select_related("usuario", "libro")
            .order_by("libro__genero", "libro__titulo", "-creada_en")
        )

        query = self.request.GET.get("q", "")
        genero = self.request.GET.get("genero", "")

        if query:
            queryset = queryset.filter(
                Q(libro__titulo__icontains=query)
            )

        if genero:
            queryset = queryset.filter(
                Q(libro__genero__icontains=genero)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["genero_seleccionado"] = self.request.GET.get("genero", "")
        return context

@login_required
def eliminar_resena(request, pk):
    resena = get_object_or_404(Reseña, pk=pk)

    if not request.user.es_bibliotecario:
        return HttpResponseForbidden()

    resena.delete()
    messages.success(request, "Reseña eliminada correctamente.")    
    return redirect("lista_resenas")

@login_required
def perfil(request):

    prestamos_activos = request.user.prestamos.filter(
        estado=Prestamo.Estado.ACTIVO
    )

    prestamos_finalizados = request.user.prestamos.filter(
        estado=Prestamo.Estado.FINALIZADO
    )

    resenas = Reseña.objects.filter(
        usuario=request.user
    ).select_related("libro")

    return render(request, "books/perfil.html", {
        "prestamos_activos": prestamos_activos,
        "prestamos_finalizados": prestamos_finalizados,
        "resenas": resenas
    })

class RecomendacionesView(ListView):
    model = Libro
    template_name = "books/recomendaciones.html"
    context_object_name = "libros"

    def get_queryset(self):
        libros = (
            Libro.objects
            .annotate(
                media_rating=Avg("resenas__rating"),
                total_resenas=Count("resenas")
            )
            .filter(total_resenas__gt=0)
            .order_by("-media_rating", "-total_resenas")
        )

        for libro in libros:
            libro.estrellas_llenas = int(libro.media_rating or 0)
            libro.estrellas_vacias = 5 - libro.estrellas_llenas

            # Clasificación automática
            if libro.media_rating >= 4.5:
                libro.nivel = "Excelente"
            elif libro.media_rating >= 4:
                libro.nivel = "Muy recomendado"
            elif libro.media_rating >= 3:
                libro.nivel = "Recomendado"
            else:
                libro.nivel = "Valoración moderada"

        return libros