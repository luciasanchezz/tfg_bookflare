
from django.urls import path, include
from .views import *

urlpatterns = [
    path('', inicio, name='inicio'),
]
