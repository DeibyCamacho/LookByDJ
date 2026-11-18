from django.contrib import admin
from .models import Servicio, OfertaServicio

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'categoria')
    search_fields = ('nombre', 'categoria')

@admin.register(OfertaServicio)
class OfertaServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'servicio', 'profesional', 'local', 'precio', 'duracion', 'activa')
    list_filter = ('activa', 'servicio')  # Cambiamos 'categoria' por 'servicio'
    search_fields = ('servicio__nombre',)