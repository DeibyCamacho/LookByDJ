from django.urls import path
from . import views

app_name = 'calificaciones'

urlpatterns = [
    path('', views.lista_calificaciones, name='lista'),
    path('crear/', views.crear_calificacion, name='crear'),
]
