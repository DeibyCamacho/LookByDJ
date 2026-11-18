from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import LoginForm, PerfilForm, RegistroForm


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
