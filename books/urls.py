
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path("", views.principal, name="principal"),
    #path("catalogo/", views.catalogo, name="catalogo"),

    # panel biblioteca
    path("libros/crear/", LibroCreateView.as_view(), name="libro_crear"),
    path("libros/<int:pk>/editar/", LibroUpdateView.as_view(), name="libro_editar"),
    path("libros/<int:pk>/eliminar/", LibroDeleteView.as_view(), name="libro_eliminar"),

    path("filtrar/", views.filtrar_libros, name="filtrar_libros"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("libros/<int:pk>/", LibroDetailView.as_view(), name="libro_detalle"),

    path("prestar/<int:inventario_id>/", views.prestar_libro, name="prestar_libro"),

    path("leer/libro/<int:libro_id>/", views.leer_libro_por_libro, name="leer_libro_por_libro"),

    path("stream/pdf/<int:prestamo_id>/", views.stream_pdf, name="stream_pdf"),

    path("stream/pdf/<int:prestamo_id>/", views.stream_pdf, name="stream_pdf"),

    # auth
    path("login/",  auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="logged_out.html"), name="logout"),
    path("register/", views.register, name="register"),

]
