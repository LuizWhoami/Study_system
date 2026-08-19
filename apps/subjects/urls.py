from django.urls import path
from . import views

app_name = 'subjects'
urlpatterns = [
    # Matérias
    path('', views.SubjectListView.as_view(), name='list'),
    path('estudo/<int:estudo_id>/', views.SubjectByContestView.as_view(), name='by_contest'),
    path('criar/', views.SubjectCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.SubjectUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.SubjectDeleteView.as_view(), name='delete'),
    path('concluir_materia/<int:pk>/', views.concluir_materia, name='concluir_materia'),

    # Tópicos
    path('materia/<int:subject_id>/assuntos/', views.TopicBySubjectView.as_view(), name='topics_by_subject'),
    path('topico/criar/', views.TopicCreateView.as_view(), name='topic_create'),
    path('topico/<int:pk>/editar/', views.TopicUpdateView.as_view(), name='topic_update'),
    path('topico/<int:pk>/excluir/', views.TopicDeleteView.as_view(), name='topic_delete'),
    path('concluir_topico/<int:pk>/', views.concluir_topico, name='concluir_topico'),
]
