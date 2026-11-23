from django.contrib import admin
from .models import Pedido, DetallePedido

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente_id', 'local_id', 'estado', 'total', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    inlines = [DetallePedidoInline]