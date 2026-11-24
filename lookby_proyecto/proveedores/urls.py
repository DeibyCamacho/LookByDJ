from django.urls import path

from . import views

app_name = 'proveedores'

urlpatterns = [
    path('', views.lista_proveedores, name='lista'),
    path('crear/', views.crear_proveedor, name='crear'),
    path('<int:pk>/', views.detalle_proveedor, name='detalle'),
    path('<int:pk>/editar/', views.editar_proveedor, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_proveedor, name='eliminar'),
    path('<int:pk>/productos/crear/', views.crear_suministro, name='suministro_crear'),
    path(
        '<int:pk>/productos/<int:suministro_pk>/editar/',
        views.editar_suministro,
        name='suministro_editar',
    ),
    path(
        '<int:pk>/productos/<int:suministro_pk>/eliminar/',
        views.eliminar_suministro,
        name='suministro_eliminar',
    ),
]
