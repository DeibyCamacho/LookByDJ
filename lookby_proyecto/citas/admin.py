from django.contrib import admin
from .models import Cita

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'oferta', 'fecha_inicio', 'fecha_fin', 'estado', 'precio')
    list_filter = ('estado', 'fecha_inicio')
    search_fields = ('cliente__correo', 'oferta__servicio__nombre')