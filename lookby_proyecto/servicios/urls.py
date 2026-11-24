from django.urls import path
from . import views

app_name = 'servicios'

urlpatterns = [
    path('', views.lista_servicios, name='lista'),
    path('precios/', views.precios_servicios, name='precios'),
    # Alias sin pk para que 'servicios:detalle' también sirva como página de precios.
    path('precios/', views.precios_servicios, name='detalle'),
    path('crear/', views.crear_servicio, name='crear'),
    path('<int:pk>/', views.detalle_servicio, name='detalle'),
    path('<int:pk>/editar/', views.editar_servicio, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_servicio, name='eliminar'),
    path('ofertas/', views.lista_ofertas, name='ofertas_lista'),
    path('ofertas/crear/', views.crear_oferta, name='oferta_crear'),
    path('ofertas/<int:pk>/', views.detalle_oferta, name='oferta_detalle'),
    path('ofertas/<int:pk>/editar/', views.editar_oferta, name='oferta_editar'),
    path('ofertas/<int:pk>/eliminar/', views.eliminar_oferta, name='oferta_eliminar'),
]
