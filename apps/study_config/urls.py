from django.urls import path
from . import views

app_name = 'study_config'
urlpatterns = [
    path('', views.config_view, name='config'),
    path('preview/', views.preview_config, name='preview'),
    path('save/', views.save_config, name='save'),
    path('recalculate/', views.recalculate_plan, name='recalculate'),
    path('meu-plano/', views.meu_plano, name='meu_plano'),
    path('estatisticas/', views.stats_view, name='stats'),
    path('planos/', views.planos_list, name='planos_list'),
    path('planos/<int:pk>/excluir/', views.plano_delete, name='plano_delete'),
    path('planos/<int:pk>/ativar/', views.plano_activate, name='plano_activate'),
    # Fase 2 — ações em sessões planejadas
    path('sessao/<int:pk>/concluir/', views.session_complete, name='session_complete'),
    path('sessao/<int:pk>/pular/', views.session_skip, name='session_skip'),
    path('sessao/<int:pk>/reagendar/', views.session_reschedule, name='session_reschedule'),
]
