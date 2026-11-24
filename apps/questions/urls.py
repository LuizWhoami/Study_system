from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    # Banco e CRUD
    path('', views.QuestionBankView.as_view(), name='bank'),
    path('criar/', views.QuestionCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.QuestionUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.QuestionDeleteView.as_view(), name='delete'),
    path('<int:pk>/resolver/', views.resolve_question, name='resolve'),

    # Simulados (stubs 501 — implementar futuramente)
    path('simulado/', views.SimuladoListView.as_view(), name='simulado_list'),
    path('simulado/criar/', views.SimuladoCreateView.as_view(), name='simulado_create'),
    path('simulado/<int:pk>/', views.simulado_iniciar, name='simulado_iniciar'),
    path('simulado/<int:pk>/resolver/', views.simulado_resolver, name='simulado_resolver'),
    path('simulado/<int:pk>/responder/', views.simulado_responder, name='simulado_responder'),
    path('simulado/<int:pk>/finalizar/', views.simulado_finalizar, name='simulado_finalizar'),

    # Caderno de erros
    path('erros/', views.error_log_list, name='error_log'),
    path('erros/<int:pk>/', views.error_log_detail, name='error_log_detail'),
    path('erros/<int:pk>/excluir/', views.error_log_delete, name='error_log_delete'),

    # Performance e import
    path('performance/', views.performance, name='performance'),
    path('import/', views.import_questions, name='import'),

    # Treino — DESATIVADO 2026-10-08
    # Para reativar, descomente as 3 linhas abaixo:
    # path('treino/', views.treino_inteligente, name='treino_inteligente'),
    # path('treino/sessao/', views.treino_sessao, name='treino_sessao'),
    # path('treino/responder/', views.treino_responder, name='treino_responder'),

    # IA — geração de questões via Groq
    path('ia/', views.ia_gerar_page, name='ia_gerar'),
    path('ia/api/gerar/', views.ia_gerar_api, name='ia_gerar_api'),
]
