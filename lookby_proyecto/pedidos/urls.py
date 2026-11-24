from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.lista_pedidos, name='lista'),
    path('crear/', views.crear_pedido, name='crear'),
    path('<int:pk>/', views.detalle_pedido, name='detalle'),
    path('<int:pk>/editar/', views.editar_pedido, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_pedido, name='eliminar'),
    # Alias semántico para la baja lógica (cancelar == eliminar en la web).
    path('<int:pk>/cancelar/', views.eliminar_pedido, name='cancelar'),
]
