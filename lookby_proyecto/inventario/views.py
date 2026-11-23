from django.shortcuts import render
from .models import InventarioLocal

def lista_inventario(request):
    inventarios = InventarioLocal.objects.select_related('local', 'producto').all()
    return render(request, 'inventario/lista_inventario.html', {'inventarios': inventarios})