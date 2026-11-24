from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    LoginForm,
    PerfilForm,
    RegistroForm,
    UsuarioAdminForm,
    UsuarioEdicionForm,
)
from .models import Usuario
from .permisos import admin_required, es_admin


def registro(request):
    if request.user.is_authenticated:
        return redirect('usuarios:perfil')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, '¡Cuenta creada! Bienvenido a LookBy.')
            return redirect('usuarios:perfil')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


class EntrarView(LoginView):
    template_name = 'usuarios/entrar.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


@login_required
def perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado.')
            return redirect('usuarios:perfil')
    else:
        form = PerfilForm(instance=request.user)
    return render(request, 'usuarios/perfil.html', {
        'form': form,
        'roles': request.user.roles.all(),
        'locales': request.user.locales_administrados.filter(activo=True),
    })


@login_required
@admin_required
def lista_usuarios(request):
    """Listado de cuentas: solo administradores."""
    usuarios = Usuario.objects.all().order_by('correo')
    q = (request.GET.get('q') or '').strip()
    if q:
        usuarios = usuarios.filter(
            Q(correo__icontains=q)
            | Q(nombre__icontains=q)
            | Q(apellido__icontains=q)
        )
    return render(request, 'usuarios/lista.html', {'usuarios': usuarios, 'q': q})


def _cuenta_gestionable(request, pk):
    """La propia cuenta siempre; las ajenas solo para administradores."""
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario.pk != request.user.pk and not es_admin(request.user):
        raise PermissionDenied('No puedes gestionar la cuenta de otra persona.')
    return usuario


@login_required
def detalle_usuario(request, pk):
    usuario = _cuenta_gestionable(request, pk)
    return render(request, 'usuarios/detalle.html', {
        'usuario': usuario,
        'es_propio': usuario.pk == request.user.pk,
        'puede_editar_roles': es_admin(request.user),
    })


@login_required
def editar_usuario(request, pk):
    usuario = _cuenta_gestionable(request, pk)
    formulario_admin = es_admin(request.user)
    Formulario = UsuarioAdminForm if formulario_admin else UsuarioEdicionForm

    if request.method == 'POST':
        form = Formulario(request.POST, instance=usuario, editor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta actualizada.')
            return redirect('usuarios:detalle', pk=usuario.pk)
    else:
        form = Formulario(instance=usuario, editor=request.user)

    return render(request, 'usuarios/form.html', {
        'form': form,
        'usuario': usuario,
        'titulo': 'Editar cuenta',
        'formulario_admin': formulario_admin,
    })


@login_required
def desactivar_usuario(request, pk):
    """Baja lógica: la cuenta conserva su historial."""
    usuario = _cuenta_gestionable(request, pk)
    if request.method == 'POST':
        propio = usuario.pk == request.user.pk
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        messages.success(
            request,
            'Tu cuenta ha sido desactivada.' if propio
            else f'La cuenta de {usuario.correo} ha sido desactivada.',
        )
        if propio:
            logout(request)
            return redirect('locales:lista')
        return redirect('usuarios:lista')
    return render(request, 'usuarios/confirmar_desactivar.html', {'usuario': usuario})
