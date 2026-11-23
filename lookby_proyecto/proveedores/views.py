from django.shortcuts import render
from usuarios.permisos import admin_required
from .models import Proveedor


@admin_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'proveedores/lista.html', {'proveedores': proveedores})
