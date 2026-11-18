from django.shortcuts import render
from .models import Producto

def lista_productos(views):
    # Consultamos todos los productos de la base de datos
    productos = Producto.objects.all()
    # Los enviamos a un archivo HTML que ya vamos a crear
    return render(views, 'productos/lista_productos.html', {'productos': productos})