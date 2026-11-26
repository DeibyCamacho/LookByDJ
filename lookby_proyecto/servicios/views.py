from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from usuarios.permisos import admin_required, es_admin

from locales.models import Local
from profesionales.views import puede_editar_profesional

from .forms import OfertaServicioForm, ServicioForm
from .models import OfertaServicio, Servicio


MENSAJE_LOCAL_AJENO = (
    'No puedes gestionar ofertas de un local que no administras.'
)


def exigir_administrador_local(usuario, local):
    """Una oferta ligada a un local solo la gestiona quien administre ese local."""
    if local is not None and not local.puede_administrar(usuario):
        raise PermissionDenied(MENSAJE_LOCAL_AJENO)


def _local_enviado(request):
    local_id = request.POST.get('local')
    if not local_id or not str(local_id).isdigit():
        return None
    return Local.objects.filter(pk=local_id).first()


def lista_servicios(request):
    ofertas = OfertaServicio.objects.select_related(
        'servicio', 'profesional__usuario', 'local'
    ).filter(activa=True).order_by('pk')
    servicios = Servicio.objects.order_by('pk')
    pagina_ofertas = Paginator(ofertas, 20).get_page(request.GET.get('page'))
    pagina_servicios = Paginator(servicios, 20).get_page(
        request.GET.get('page_servicios')
    )
    return render(
        request,
        'servicios/lista.html',
        {
            'servicios': pagina_servicios,
            'ofertas': pagina_ofertas,
            'page_obj': pagina_ofertas,
            'servicios_page': pagina_servicios,
        },
    )


def precios_servicios(request):
    """Vista de precios sin identificador: reutiliza el listado con su sección #precios."""
    return lista_servicios(request)


@login_required
@admin_required
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save()
            messages.success(request, 'Servicio creado correctamente.')
            return redirect('servicios:detalle', pk=servicio.pk)
    else:
        form = ServicioForm()
    return render(request, 'servicios/form.html', {'form': form, 'accion': 'Crear'})


def detalle_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    ofertas = servicio.ofertas.select_related(
        'profesional__usuario', 'local'
    ).all()
    return render(
        request,
        'servicios/detalle.html',
        {
            'servicio': servicio,
            'ofertas': ofertas,
            'puede_editar': es_admin(request.user),
        },
    )


@login_required
@admin_required
def editar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio actualizado.')
            return redirect('servicios:detalle', pk=servicio.pk)
    else:
        form = ServicioForm(instance=servicio)
    return render(
        request,
        'servicios/form.html',
        {'form': form, 'accion': 'Editar', 'servicio': servicio},
    )


@login_required
@admin_required
@require_POST
def eliminar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    try:
        servicio.delete()
    except ProtectedError:
        messages.error(request, 'No se puede eliminar: el servicio tiene citas asociadas.')
        return redirect('servicios:detalle', pk=pk)
    messages.success(request, 'Servicio eliminado.')
    return redirect('servicios:lista')


def lista_ofertas(request):
    ofertas = OfertaServicio.objects.select_related(
        'servicio', 'profesional__usuario', 'local'
    ).order_by('pk')
    pagina = Paginator(ofertas, 20).get_page(request.GET.get('page'))
    return render(request, 'servicios/ofertas_lista.html', {
        'ofertas': pagina, 'page_obj': pagina,
    })


@login_required
def crear_oferta(request):
    if request.method == 'POST':
        local = _local_enviado(request)
        exigir_administrador_local(request.user, local)
        form = OfertaServicioForm(request.POST, usuario=request.user)
        if form.is_valid():
            exigir_administrador_local(request.user, form.cleaned_data.get('local'))
            oferta = form.save()
            messages.success(request, 'Oferta creada correctamente.')
            return redirect('servicios:oferta_detalle', pk=oferta.pk)
    else:
        form = OfertaServicioForm(usuario=request.user)
    return render(
        request,
        'servicios/oferta_form.html',
        {'form': form, 'accion': 'Crear'},
    )


def detalle_oferta(request, pk):
    oferta = get_object_or_404(
        OfertaServicio.objects.select_related(
            'servicio', 'profesional__usuario', 'local'
        ),
        pk=pk,
    )
    return render(
        request,
        'servicios/oferta_detalle.html',
        {
            'oferta': oferta,
            'puede_editar': puede_editar_profesional(request.user, oferta.profesional),
        },
    )


@login_required
def editar_oferta(request, pk):
    oferta = get_object_or_404(
        OfertaServicio.objects.select_related('profesional', 'local'), pk=pk
    )
    if not puede_editar_profesional(request.user, oferta.profesional):
        raise PermissionDenied('No puedes editar esta oferta.')
    exigir_administrador_local(request.user, oferta.local)
    if request.method == 'POST':
        local = _local_enviado(request)
        exigir_administrador_local(request.user, local)
        form = OfertaServicioForm(
            request.POST, instance=oferta, usuario=request.user
        )
        if form.is_valid():
            exigir_administrador_local(request.user, form.cleaned_data.get('local'))
            form.save()
            messages.success(request, 'Oferta actualizada.')
            return redirect('servicios:oferta_detalle', pk=oferta.pk)
    else:
        form = OfertaServicioForm(instance=oferta, usuario=request.user)
    return render(
        request,
        'servicios/oferta_form.html',
        {'form': form, 'accion': 'Editar', 'oferta': oferta},
    )


@login_required
@require_POST
def eliminar_oferta(request, pk):
    """Las ofertas se desactivan para no borrar el histórico de citas."""
    oferta = get_object_or_404(
        OfertaServicio.objects.select_related('profesional', 'local'), pk=pk
    )
    if not puede_editar_profesional(request.user, oferta.profesional):
        raise PermissionDenied('No puedes desactivar esta oferta.')
    exigir_administrador_local(request.user, oferta.local)
    oferta.activa = False
    oferta.save(update_fields=['activa'])
    messages.success(request, 'La oferta fue desactivada.')
    return redirect('servicios:ofertas_lista')
