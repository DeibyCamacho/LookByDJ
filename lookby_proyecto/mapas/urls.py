from django.urls import path
from . import views

app_name = 'mapas'

urlpatterns = [
    path('', views.lista_mapa, name='lista'),
    path('api/locales/', views.api_mapa_locales, name='api_locales'),
]
