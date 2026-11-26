"""
URL configuration for lookby_proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

# Páginas de error con el diseño de la app. Nunca muestran trazas ni rutas.
handler400 = 'lookby_proyecto.vistas_error.error_400'
handler403 = 'lookby_proyecto.vistas_error.error_403'
handler404 = 'lookby_proyecto.vistas_error.error_404'
handler413 = 'lookby_proyecto.vistas_error.error_413'
handler500 = 'lookby_proyecto.vistas_error.error_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('locales/', include('locales.urls')),
    path('productos/', include('productos.urls')),
    path('inventario/', include('inventario.urls')),
    path('pedidos/', include('pedidos.urls')),
    path('catalogos/', include('catalogos.urls')),
    path('profesionales/', include('profesionales.urls')),
    path('servicios/', include('servicios.urls')),
    path('citas/', include('citas.urls')),
    path('proveedores/', include('proveedores.urls')),
    path('calificaciones/', include('calificaciones.urls')),
    path('mapas/', include('mapas.urls')),
    path('', include('inicio.urls')),
]
