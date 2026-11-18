from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('entrar/', views.EntrarView.as_view(), name='entrar'),
    path('salir/', LogoutView.as_view(), name='salir'),  # solo acepta POST
    path('perfil/', views.perfil, name='perfil'),
]
