from django.urls import path
from . import views
app_name = 'notes'
urlpatterns = [
    path('', views.NoteListView.as_view(), name='list'),
    path('criar/', views.NoteCreateView.as_view(), name='create'),
    path('<int:pk>/', views.NoteDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.NoteUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.NoteDeleteView.as_view(), name='delete'),
]
