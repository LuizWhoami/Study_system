from django.urls import path
from . import views

app_name = 'questions'
urlpatterns = [
    path('', views.QuestionListView.as_view(), name='list'),
    path('criar/', views.QuestionCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.QuestionUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.QuestionDeleteView.as_view(), name='delete'),
]
