from django.urls import path

from . import views

app_name = 'locales'

urlpatterns = [
    path('', views.lista_locales, name='lista'),
    path('crear/', views.crear_local, name='crear'),
    path('<int:pk>/', views.detalle_local, name='detalle'),
    path('<int:pk>/editar/', views.editar_local, name='editar'),
    path('<int:pk>/eliminar/', views.desactivar_local, name='desactivar'),
    # Alias para quienes usen la convención 'eliminar' (la baja es lógica).
    path('<int:pk>/eliminar/', views.desactivar_local, name='eliminar'),
]
