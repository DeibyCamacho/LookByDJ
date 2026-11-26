from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from usuarios.permisos import admin_required, es_admin

from .forms import HorarioForm, ProfesionalForm
from .models import Horario, Profesional


def puede_editar_profesional(usuario, profesional):
    """Un administrador o el propio profesional pueden gestionar sus datos."""
    return usuario.is_authenticated and (
        es_admin(usuario) or profesional.usuario_id == usuario.pk
    )


def lista_profesionales(request):
    profesionales = Profesional.objects.select_related('usuario').prefetch_related(
        'horarios__local'
    ).order_by('pk')
    pagina = Paginator(profesionales, 20).get_page(request.GET.get('page'))
    return render(
        request,
        'profesionales/lista.html',
        {'profesionales': pagina, 'page_obj': pagina},
    )


@login_required
@admin_required
def crear_profesional(request):
    if request.method == 'POST':
        form = ProfesionalForm(request.POST)
        if form.is_valid():
            profesional = form.save()
            messages.success(request, 'Perfil profesional creado correctamente.')
            return redirect('profesionales:detalle', pk=profesional.pk)
    else:
        form = ProfesionalForm()
    return render(request, 'profesionales/form.html', {'form': form, 'accion': 'Crear'})


def detalle_profesional(request, pk):
    profesional = get_object_or_404(
        Profesional.objects.select_related('usuario').prefetch_related('horarios__local'),
        pk=pk,
    )
    return render(
        request,
        'profesionales/detalle.html',
        {
            'profesional': profesional,
            'puede_editar': puede_editar_profesional(request.user, profesional),
        },
    )


@login_required
def editar_profesional(request, pk):
    profesional = get_object_or_404(Profesional, pk=pk)
    if not puede_editar_profesional(request.user, profesional):
        return HttpResponseForbidden('No puedes editar este perfil profesional.')
    if request.method == 'POST':
        form = ProfesionalForm(request.POST, instance=profesional)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil profesional actualizado.')
            return redirect('profesionales:detalle', pk=profesional.pk)
    else:
        form = ProfesionalForm(instance=profesional)
    return render(
        request,
        'profesionales/form.html',
        {'form': form, 'accion': 'Editar', 'profesional': profesional},
    )


@login_required
@require_POST
def eliminar_profesional(request, pk):
    profesional = get_object_or_404(Profesional, pk=pk)
    if not puede_editar_profesional(request.user, profesional):
        return HttpResponseForbidden('No puedes eliminar este perfil profesional.')
    try:
        profesional.delete()
    except ProtectedError:
        messages.error(
            request,
            'No se puede eliminar: el profesional tiene citas asociadas.',
        )
        return redirect('profesionales:detalle', pk=pk)
    messages.success(request, 'Perfil profesional eliminado.')
    return redirect('profesionales:lista')


def lista_horarios(request):
    horarios = Horario.objects.select_related(
        'profesional__usuario', 'local'
    ).order_by('pk')
    pagina = Paginator(horarios, 20).get_page(request.GET.get('page'))
    return render(request, 'profesionales/horarios_lista.html', {
        'horarios': pagina, 'page_obj': pagina,
    })


@login_required
def crear_horario(request):
    if request.method == 'POST':
        form = HorarioForm(request.POST, usuario=request.user)
        if form.is_valid():
            horario = form.save()
            messages.success(request, 'Horario creado correctamente.')
            return redirect('profesionales:horario_detalle', pk=horario.pk)
    else:
        form = HorarioForm(usuario=request.user)
    return render(
        request,
        'profesionales/horario_form.html',
        {'form': form, 'accion': 'Crear'},
    )


def detalle_horario(request, pk):
    horario = get_object_or_404(
        Horario.objects.select_related('profesional__usuario', 'local'), pk=pk
    )
    return render(
        request,
        'profesionales/horario_detalle.html',
        {
            'horario': horario,
            'puede_editar': puede_editar_profesional(request.user, horario.profesional),
        },
    )


@login_required
def editar_horario(request, pk):
    horario = get_object_or_404(Horario, pk=pk)
    if not puede_editar_profesional(request.user, horario.profesional):
        return HttpResponseForbidden('No puedes editar este horario.')
    if request.method == 'POST':
        form = HorarioForm(request.POST, instance=horario, usuario=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario actualizado.')
            return redirect('profesionales:horario_detalle', pk=horario.pk)
    else:
        form = HorarioForm(instance=horario, usuario=request.user)
    return render(
        request,
        'profesionales/horario_form.html',
        {'form': form, 'accion': 'Editar', 'horario': horario},
    )


@login_required
@require_POST
def eliminar_horario(request, pk):
    horario = get_object_or_404(Horario, pk=pk)
    if not puede_editar_profesional(request.user, horario.profesional):
        return HttpResponseForbidden('No puedes eliminar este horario.')
    horario.delete()
    messages.success(request, 'Horario eliminado.')
    return redirect('profesionales:horarios_lista')
