from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'study'

urlpatterns = [
    # Página legada — redireciona para o dashboard.
    # O cronômetro agora vive em `templates/components/study_timer.html`
    # e é incluído em todas as páginas autenticadas via `base.html`.
    path(
        '',
        RedirectView.as_view(pattern_name='dashboard:index', permanent=False),
        name='study',
    ),

    # APIs auxiliares (selects em cascata do widget global)
    path('api/contests/', views.api_contests, name='api_contests'),
    path('api/materias-por-estudo/<int:estudo_id>/', views.api_materias_por_estudo, name='api_materias'),
    path('api/assuntos-por-materia/<int:materia_id>/', views.api_assuntos_por_materia, name='api_assuntos'),

    # Cronômetro global
    path('session/current/', views.current_session, name='current_session'),
    path('start/', views.start_session, name='start_session'),
    path('session/pause/', views.pause_session_view, name='pause_session'),
    path('session/resume/', views.resume_session_view, name='resume_session'),
    path('end/', views.end_session, name='end_session'),

    # SRS
    path('mark-studied/', views.mark_studied, name='mark_studied'),
    path('pending-reviews/', views.pending_reviews, name='pending_reviews'),
]
