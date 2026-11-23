from django.contrib import admin
from .models import Calificacion


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('idCalificacion', 'puntuacion', 'cliente', 'local', 'profesional')
    list_filter = ('puntuacion',)
    search_fields = ('comentario', 'cliente__correo')
