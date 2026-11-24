from django.urls import path
from . import views

app_name = 'contests'
urlpatterns = [
    path('', views.ContestListView.as_view(), name='list'),
    path('criar/', views.ContestCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.ContestUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.ContestDeleteView.as_view(), name='delete'),
    path('<int:pk>/', views.ContestDetailView.as_view(), name='detail'),
    path('geral/', views.GeneralView.as_view(), name='general'),  # nova rota
]
