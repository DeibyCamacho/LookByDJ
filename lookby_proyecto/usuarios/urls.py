from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.lista_usuarios, name='lista'),
    path('registro/', views.registro, name='registro'),
    # Alias de convención: crear cuenta equivale al registro público.
    path('crear/', views.registro, name='crear'),
    path('entrar/', views.EntrarView.as_view(), name='entrar'),
    path('salir/', LogoutView.as_view(), name='salir'),  # solo acepta POST
    path('perfil/', views.perfil, name='perfil'),
    path('<int:pk>/', views.detalle_usuario, name='detalle'),
    path('<int:pk>/editar/', views.editar_usuario, name='editar'),
    path('<int:pk>/eliminar/', views.desactivar_usuario, name='desactivar'),
    # Alias: en cuentas la baja es lógica, no se borra el registro.
    path('<int:pk>/eliminar/', views.desactivar_usuario, name='eliminar'),
]
