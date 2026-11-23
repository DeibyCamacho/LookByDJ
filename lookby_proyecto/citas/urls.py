from django.urls import path
from . import views

app_name = 'citas'

urlpatterns = [
    path('', views.lista_citas, name='lista'),
    path('crear/', views.crear_cita, name='crear'),
    path('<int:pk>/cancelar/', views.cancelar_cita, name='cancelar'),
]
