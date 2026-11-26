from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from locales.models import Local
from usuarios.permisos import admin_required

from .forms import ProductoForm
from .models import Producto


MENSAJE_PRODUCTO_AJENO = (
    'No puedes gestionar un producto que pertenece a locales que no administras.'
)


def puede_administrar_producto(usuario, producto=None):
    """El catálogo base solo lo edita quien administra alguno de sus locales.

    Si el producto aún no tiene inventario (alta inicial), basta con administrar
    algún local. Los superusuarios siempre pasan; ``puede_administrar`` ya lo
    contempla para cada local.
    """
    if not getattr(usuario, 'is_authenticated', False):
        return False
    if getattr(usuario, 'is_superuser', False):
        return True
    if producto is not None:
        locales = {inv.local for inv in producto.inventarios.select_related('local')}
        if locales:
            return any(local.puede_administrar(usuario) for local in locales)
    return any(local.puede_administrar(usuario) for local in Local.objects.all())


def exigir_administrador_producto(usuario, producto=None):
    if not puede_administrar_producto(usuario, producto):
        raise PermissionDenied(MENSAJE_PRODUCTO_AJENO)


def lista_productos(request):
    """Catálogo público. El precio no vive aquí: está en InventarioLocal."""
    productos = Producto.objects.filter(activo=True).prefetch_related(
        'inventarios__local'
    ).order_by('pk')
    pagina = Paginator(productos, 20).get_page(request.GET.get('page'))
    return render(request, 'productos/lista_productos.html', {
        'productos': pagina, 'page_obj': pagina,
    })


def detalle_producto(request, pk):
    producto = get_object_or_404(
        Producto.objects.prefetch_related('inventarios__local'), pk=pk
    )
    return render(request, 'productos/detalle.html', {'producto': producto})


@login_required
@admin_required
def crear_producto(request):
    exigir_administrador_producto(request.user)
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, 'Producto registrado correctamente.')
            return redirect('productos:detalle', pk=producto.pk)
    else:
        form = ProductoForm()
    return render(request, 'productos/form.html', {
        'form': form, 'titulo': 'Registrar producto',
    })


@login_required
@admin_required
def editar_producto(request, pk):
    producto = get_object_or_404(
        Producto.objects.prefetch_related('inventarios__local'), pk=pk
    )
    exigir_administrador_producto(request.user, producto)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado.')
            return redirect('productos:detalle', pk=producto.pk)
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/form.html', {
        'form': form, 'titulo': 'Editar producto', 'producto': producto,
    })


@login_required
@admin_required
def eliminar_producto(request, pk):
    """Baja lógica: se desactiva para no romper inventario ni pedidos."""
    producto = get_object_or_404(
        Producto.objects.prefetch_related('inventarios__local'), pk=pk
    )
    exigir_administrador_producto(request.user, producto)
    if request.method == 'POST':
        producto.activo = False
        producto.save(update_fields=['activo'])
        messages.success(request, 'Producto desactivado. Se conservó su historial.')
        return redirect('productos:lista')
    return render(request, 'productos/confirmar_eliminar.html', {
        'producto': producto,
    })
