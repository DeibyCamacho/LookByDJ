from django.urls import path

from . import views

app_name = 'locales'

urlpatterns = [
    path('', views.lista_locales, name='lista'),
    path('crear/', views.crear_local, name='crear'),
    path('<int:pk>/', views.detalle_local, name='detalle'),
    path('<int:pk>/editar/', views.editar_local, name='editar'),
    # La baja es lógica: una sola ruta, con un nombre que dice lo que hace.
    path('<int:pk>/eliminar/', views.desactivar_local, name='desactivar'),
]
