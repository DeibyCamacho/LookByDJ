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
    # Recuperación y cambio de contraseña (vistas nativas, plantillas propias).
    path('recuperar/', views.RecuperarClaveView.as_view(), name='recuperar'),
    path('recuperar/enviado/', views.RecuperarEnviadoView.as_view(),
         name='recuperar_enviado'),
    path('recuperar/<uidb64>/<token>/', views.RecuperarConfirmarView.as_view(),
         name='recuperar_confirmar'),
    path('recuperar/listo/', views.RecuperarListoView.as_view(),
         name='recuperar_listo'),
    path('cambiar-clave/', views.CambiarClaveView.as_view(),
         name='cambiar_clave'),
    path('cambiar-clave/listo/', views.CambiarClaveListoView.as_view(),
         name='cambiar_clave_listo'),
    path('perfil/', views.perfil, name='perfil'),
    path('<int:pk>/', views.detalle_usuario, name='detalle'),
    path('<int:pk>/editar/', views.editar_usuario, name='editar'),
    # En cuentas la baja es lógica: una sola ruta, confirmación por POST.
    path('<int:pk>/eliminar/', views.desactivar_usuario, name='desactivar'),
]
