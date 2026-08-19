from django.urls import path
from . import views

app_name = 'study'
urlpatterns = [
    path('', views.study_view, name='study'),
    path('api/materias-por-estudo/<int:estudo_id>/', views.api_materias_por_estudo, name='api_materias'),
    path('api/topicos-por-materia/<int:materia_id>/', views.api_topicos_por_materia, name='api_topicos'),
    path('start/', views.start_session, name='start_session'),
    path('end/', views.end_session, name='end_session'),
]
