from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Rol, Usuario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre',)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ('correo',)
    list_display = ('correo', 'nombre', 'apellido', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'roles')
    search_fields = ('correo', 'nombre', 'apellido')
    filter_horizontal = ('roles', 'groups', 'user_permissions')
    fieldsets = (
        (None, {'fields': ('correo', 'password')}),
        ('Datos personales', {'fields': ('nombre', 'apellido', 'telefono')}),
        ('Roles y permisos', {'fields': (
            'roles', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
        )}),
        ('Fechas', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('correo', 'nombre', 'password1', 'password2'),
        }),
    )
