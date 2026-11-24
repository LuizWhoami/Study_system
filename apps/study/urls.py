from django.urls import path
from . import views

app_name = 'study'
urlpatterns = [
    path('', views.study_view, name='study'),
    path('api/materias-por-estudo/<int:estudo_id>/', views.api_materias_por_estudo, name='api_materias'),
    path('api/assuntos-por-materia/<int:materia_id>/', views.api_assuntos_por_materia, name='api_assuntos'),
    path('start/', views.start_session, name='start_session'),
    path('end/', views.end_session, name='end_session'),
    path('mark-studied/', views.mark_studied, name='mark_studied'),
    path('pending-reviews/', views.pending_reviews, name='pending_reviews'),
]
