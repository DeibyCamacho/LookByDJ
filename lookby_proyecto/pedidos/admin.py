from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import DetallePedido, Pedido
from .services import cancelar_pedido


@admin.action(description='Cancelar pedidos seleccionados (en vez de borrarlos)')
def cancelar_seleccionados(modeladmin, request, queryset):
    cancelados = 0
    for pedido in queryset:
        try:
            cancelar_pedido(pedido)
        except ValidationError as exc:
            modeladmin.message_user(request, f'Pedido #{pedido.pk}: {exc.messages[0]}', 'error')
        else:
            cancelados += 1
    modeladmin.message_user(request, f'{cancelados} pedido(s) cancelado(s).')


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1

    def has_delete_permission(self, request, obj=None):
        """No se pueden quitar líneas de un pedido confirmado."""
        if obj is not None and obj.estado == 'CONFIRMADO':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'local', 'estado', 'total', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion', 'local')
    search_fields = ('cliente__correo', 'cliente__nombre')
    inlines = [DetallePedidoInline]
    actions = [cancelar_seleccionados]

    def has_delete_permission(self, request, obj=None):
        """Los pedidos confirmados se cancelan, no se borran."""
        if obj is not None and obj.estado == 'CONFIRMADO':
            return False
        return super().has_delete_permission(request, obj)
