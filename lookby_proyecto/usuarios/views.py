from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

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
    """Login con límite de intentos por IP+correo y mensaje genérico."""

    template_name = 'usuarios/entrar.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True
    MAX_INTENTOS = 5
    VENTANA_SEGUNDOS = 5 * 60

    def _clave_intentos(self, request):
        """Clave de caché que separa intentos por origen y correo."""
        correo = (request.POST.get('username') or '').strip().lower()
        ip = request.META.get('REMOTE_ADDR', 'desconocida')
        return f'lookby:login:{ip}:{correo}'

    def dispatch(self, request, *args, **kwargs):
        """Bloquea temporalmente tras cinco intentos fallidos."""
        if request.method == 'POST':
            clave = self._clave_intentos(request)
            if cache.get(clave, 0) >= self.MAX_INTENTOS:
                messages.error(
                    request,
                    'Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.',
                )
                return redirect('usuarios:entrar')
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        """Cuenta el fallo sin revelar si el correo existe."""
        clave = self._clave_intentos(self.request)
        cache.set(
            clave,
            cache.get(clave, 0) + 1,
            self.VENTANA_SEGUNDOS,
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        """Limpia el contador y muestra un mensaje de bienvenida."""
        cache.delete(self._clave_intentos(self.request))
        messages.success(self.request, '¡Bienvenido de nuevo a LookBy!')
        return super().form_valid(form)


# --- Recuperación y cambio de contraseña (vistas nativas de Django) ------------

class RecuperarClaveView(PasswordResetView):
    """Envía el correo con el token de recuperación."""

    template_name = 'usuarios/password_reset_form.html'
    email_template_name = 'usuarios/email_recuperacion.txt'
    subject_template_name = 'usuarios/email_recuperacion_asunto.txt'
    success_url = reverse_lazy('usuarios:recuperar_enviado')


class RecuperarEnviadoView(PasswordResetDoneView):
    """Mensaje genérico: no dice si el correo estaba registrado."""

    template_name = 'usuarios/password_reset_done.html'


class RecuperarConfirmarView(PasswordResetConfirmView):
    """Formulario de nueva contraseña; el token caduca en una hora."""

    template_name = 'usuarios/password_reset_confirm.html'
    success_url = reverse_lazy('usuarios:recuperar_listo')


class RecuperarListoView(PasswordResetCompleteView):
    """Confirmación de contraseña cambiada."""

    template_name = 'usuarios/password_reset_complete.html'


class CambiarClaveView(LoginRequiredMixin, PasswordChangeView):
    """Cambio de contraseña estando logueado."""

    template_name = 'usuarios/password_change_form.html'
    success_url = reverse_lazy('usuarios:cambiar_clave_listo')


class CambiarClaveListoView(LoginRequiredMixin, PasswordChangeDoneView):
    """Confirmación del cambio de contraseña."""

    template_name = 'usuarios/password_change_done.html'


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
