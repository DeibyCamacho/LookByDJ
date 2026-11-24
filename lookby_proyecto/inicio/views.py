from django.shortcuts import render


def home(request):
    """Página de inicio de LookBy."""
    return render(request, 'inicio/home.html')
