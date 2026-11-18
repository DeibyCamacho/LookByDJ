from django.contrib import admin
from .models import Profesional, Horario

@admin.register(Profesional)
class ProfesionalAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'domicilio')
    list_filter = ('domicilio',)
    search_fields = ('usuario__correo', 'usuario__nombre')

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'profesional', 'local', 'dia_semana', 'hora_inicio', 'hora_fin')
    list_filter = ('dia_semana',)