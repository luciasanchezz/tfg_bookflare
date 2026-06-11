from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import LibroCreateView, LibroUpdateView, LibroDeleteView, LibroDetailView

urlpatterns = [
    path("", views.principal, name="principal"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("filtrar/", views.filtrar_libros, name="filtrar_libros"),

    path("libros/crear/", LibroCreateView.as_view(), name="libro_crear"),
    path("libros/<str:isbn>/editar/", LibroUpdateView.as_view(), name="libro_editar"),
    path("libros/<str:isbn>/eliminar/", LibroDeleteView.as_view(), name="libro_eliminar"),
    path("libros/<str:isbn>/", LibroDetailView.as_view(), name="libro_detalle"),

    path("prestar/<int:inventario_id>/", views.prestar_libro, name="prestar_libro"),
    path("leer/<str:isbn>/", views.leer_libro, name="leer_libro"),
    path("stream/pdf/<int:prestamo_id>/", views.stream_pdf, name="stream_pdf"),
    path("portada/<str:isbn>/", views.ver_portada, name="ver_portada"),

    path("libros/<str:isbn>/resena/", views.ResenaCreateView.as_view(), name="crear_resena"),
    path("devolver/<int:prestamo_id>/", views.devolver_libro, name="devolver_libro"),

    path("resenas/", views.ListaResenasView.as_view(), name="lista_resenas"),
    path("libros/<str:isbn>/resena/", views.ResenaCreateView.as_view(), name="crear_resena"),
    
    path("resena/<int:pk>/eliminar/", views.eliminar_resena, name="eliminar_resena"),

    path("recomendaciones/", views.RecomendacionesView.as_view(), name="recomendaciones"),

    path("perfil/", views.perfil, name="perfil"),

    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="registration/logged_out.html"), name="logout"),
    path("register/", views.register, name="register"),
]