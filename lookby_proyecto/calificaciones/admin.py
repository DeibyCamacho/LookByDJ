from django.contrib import admin
from .models import Calificacion

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('idCalificacion', 'puntuacion', 'idCliente', 'idLocal', 'idProfesional')
    list_filter = ('puntuacion',)
    search_fields = ('comentario',)