from django.urls import path
from . import views

app_name = 'flashcards'
urlpatterns = [
    path('', views.listar_flashcards, name='listar'),
    path('revisar/<int:pk>/', views.revisar_flashcard, name='revisar'),
    path('criar/', views.criar_flashcard, name='criar'),
    path('estatisticas/', views.estatisticas_flashcards, name='estatisticas'),
    path('api/notas-por-topico/<int:topic_id>/', views.api_notas_por_topico, name='api_notas'),
]
