from django.urls import path
from .views import lista_pedidos

urlpatterns = [
    path('', lista_pedidos, name='lista_pedidos'),
]