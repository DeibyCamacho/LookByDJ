from django.urls import path
from . import views

app_name = 'citas'

urlpatterns = [
    path('', views.lista_citas, name='lista'),
    path('crear/', views.crear_cita, name='crear'),
    path('reservar/', views.crear_cita, name='reservar'),
    path('<int:pk>/', views.detalle_cita, name='detalle'),
    path('<int:pk>/editar/', views.editar_cita, name='editar'),
    path('<int:pk>/reprogramar/', views.editar_cita, name='reprogramar'),
    path('<int:pk>/cancelar/', views.cancelar_cita, name='cancelar'),
]
