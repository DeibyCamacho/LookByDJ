from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from .models import Proveedor


# LISTAR PROVEEDORES
def listar_proveedores(request):
    proveedores = Proveedor.objects.all()

    return render(request, 'proveedores/lista.html', {
        'proveedores': proveedores
    })


# REGISTRAR PROVEEDOR
def crear_proveedor(request):
    if request.method == 'POST':
        proveedor = Proveedor(
            nombre=request.POST.get('nombre'),
            telefono=request.POST.get('telefono'),
            correo=request.POST.get('correo')
        )

        try:
            proveedor.full_clean()
            proveedor.save()
            return redirect('listar_proveedores')

        except ValidationError as error:
            return render(request, 'proveedores/formulario.html', {
                'error': error.message_dict.get('telefono', ['Datos incorrectos'])[0],
                'proveedor': proveedor
            })

    return render(request, 'proveedores/formulario.html')


# VER DETALLES
def detalle_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)

    return render(request, 'proveedores/detalle.html', {
        'proveedor': proveedor
    })


# EDITAR PROVEEDOR
def editar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)

    if request.method == 'POST':
        proveedor.nombre = request.POST.get('nombre')
        proveedor.telefono = request.POST.get('telefono')
        proveedor.correo = request.POST.get('correo')

        try:
            proveedor.full_clean()
            proveedor.save()
            return redirect('listar_proveedores')

        except ValidationError as error:
            return render(request, 'proveedores/formulario.html', {
                'proveedor': proveedor,
                'error': error.message_dict.get('telefono', ['Datos incorrectos'])[0]
            })

    return render(request, 'proveedores/formulario.html', {
        'proveedor': proveedor
    })


# ELIMINAR PROVEEDOR
def eliminar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)

    if request.method == 'POST':
        proveedor.delete()
        return redirect('listar_proveedores')

    return render(request, 'proveedores/eliminar.html', {
        'proveedor': proveedor
    })