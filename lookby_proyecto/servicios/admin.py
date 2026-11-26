from django import forms
from django.contrib import admin

from usuarios.validators import validadores_precio

from .forms import ServicioForm
from .models import OfertaServicio, Servicio


class OfertaServicioAdminForm(forms.ModelForm):
    """Formulario pequeño para el admin: mismo validador de precio que el modelo."""

    precio = forms.DecimalField(
        label='Precio',
        max_digits=10,
        decimal_places=2,
        validators=validadores_precio(),
        help_text='Precio en pesos. Puede ser 0; máximo 2 decimales.',
        error_messages={
            'min_value': 'El precio no puede ser negativo. Usa 0 si es gratuito.',
            'max_value': 'El precio supera el máximo permitido.',
            'decimal_places': 'El precio admite máximo 2 decimales.',
        },
    )

    class Meta:
        model = OfertaServicio
        fields = '__all__'


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    form = ServicioForm
    list_display = ('id', 'nombre', 'categoria')
    search_fields = ('nombre', 'categoria')


@admin.register(OfertaServicio)
class OfertaServicioAdmin(admin.ModelAdmin):
    form = OfertaServicioAdminForm
    list_display = ('id', 'servicio', 'profesional', 'local', 'precio', 'duracion', 'activa')
    list_filter = ('activa', 'servicio')  # Cambiamos 'categoria' por 'servicio'
    search_fields = ('servicio__nombre',)
    list_select_related = ('servicio', 'profesional__usuario', 'local')
