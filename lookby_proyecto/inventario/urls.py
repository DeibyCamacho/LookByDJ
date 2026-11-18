from django.urls import path
from .views import lista_inventario

urlpatterns = [
    path('', lista_inventario, name='lista_inventario'),
]