from django.urls import path
from . import views

app_name = 'questions'
urlpatterns = [
    path('', views.QuestionBankView.as_view(), name='bank'),
    path('criar/', views.QuestionCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.QuestionUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.QuestionDeleteView.as_view(), name='delete'),
    path('<int:pk>/resolver/', views.resolve_question, name='resolve'),
    path('treino/', views.treino_inteligente, name='treino_inteligente'),
    path('treino/sessao/', views.treino_sessao, name='treino_sessao'),
    path('simulado/', views.SimuladoListView.as_view(), name='simulado_list'),
    path('simulado/criar/', views.SimuladoCreateView.as_view(), name='simulado_create'),
    path('simulado/<int:pk>/', views.simulado_iniciar, name='simulado_iniciar'),
    path('simulado/<int:pk>/resolver/', views.simulado_resolver, name='simulado_resolver'),
    path('simulado/<int:pk>/responder/', views.simulado_responder, name='simulado_responder'),
    path('simulado/<int:pk>/finalizar/', views.simulado_finalizar, name='simulado_finalizar'),
    path('erros/', views.error_log_list, name='error_log'),
    path('erros/<int:pk>/', views.error_log_detail, name='error_log_detail'),
    path('performance/', views.performance, name='performance'),
    path('import/', views.import_questions, name='import'),
    path('<int:pk>/resolver/', views.resolve_question, name='resolve'),
    path('erros/', views.error_log_list, name='error_log'),
    path('treino/', views.treino_inteligente, name='treino_inteligente'),
    path('treino/sessao/', views.treino_sessao, name='treino_sessao'),
    path('treino/responder/', views.treino_responder, name='treino_responder'),
]
