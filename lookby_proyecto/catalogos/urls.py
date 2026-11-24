from django.urls import path

from . import views

app_name = 'catalogos'

urlpatterns = [
    path('', views.lista_catalogos, name='lista'),
    path('crear/', views.crear_catalogo, name='crear'),
    path('<int:pk>/', views.detalle_catalogo, name='detalle'),
    path('<int:pk>/editar/', views.editar_catalogo, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_catalogo, name='eliminar'),
    path('<int:pk>/productos/crear/', views.agregar_producto, name='producto_crear'),
    path(
        '<int:pk>/productos/<int:item_pk>/editar/',
        views.editar_producto,
        name='producto_editar',
    ),
    path(
        '<int:pk>/productos/<int:item_pk>/eliminar/',
        views.eliminar_producto,
        name='producto_eliminar',
    ),
]
