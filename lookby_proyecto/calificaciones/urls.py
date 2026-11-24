from django.urls import path
from . import views

app_name = 'calificaciones'

urlpatterns = [
    path('', views.lista_calificaciones, name='lista'),
    path('crear/', views.crear_calificacion, name='crear'),
    path('<int:pk>/', views.detalle_calificacion, name='detalle'),
    path('<int:pk>/editar/', views.editar_calificacion, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_calificacion, name='eliminar'),
]
