from django.urls import path
from . import views

app_name = 'profesionales'

urlpatterns = [
    path('', views.lista_profesionales, name='lista'),
    path('crear/', views.crear_profesional, name='crear'),
    path('<int:pk>/', views.detalle_profesional, name='detalle'),
    path('<int:pk>/editar/', views.editar_profesional, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_profesional, name='eliminar'),
    path('horarios/', views.lista_horarios, name='horarios_lista'),
    path('horarios/crear/', views.crear_horario, name='horario_crear'),
    path('horarios/<int:pk>/', views.detalle_horario, name='horario_detalle'),
    path('horarios/<int:pk>/editar/', views.editar_horario, name='horario_editar'),
    path('horarios/<int:pk>/eliminar/', views.eliminar_horario, name='horario_eliminar'),
]
