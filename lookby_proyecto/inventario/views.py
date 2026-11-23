from django.shortcuts import render
from usuarios.permisos import admin_required
from .models import InventarioLocal


@admin_required
def lista_inventario(request):
    inventarios = InventarioLocal.objects.select_related('local', 'producto').all()
    return render(request, 'inventario/lista_inventario.html', {'inventarios': inventarios})
