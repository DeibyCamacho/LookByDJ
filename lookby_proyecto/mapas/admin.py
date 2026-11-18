from django.contrib import admin
from .models import Ubicacion

@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('idUbicacion', 'nombreLugar', 'latitud', 'longitud', 'direccion')
    search_fields = ('nombreLugar', 'direccion')