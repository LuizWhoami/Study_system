from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    # ---------- Pastas (rotas literais primeiro) ----------
    path('',                        views.NoteFolderListView.as_view(),   name='folder_list'),
    path('pasta/criar/',            views.NoteFolderCreateView.as_view(), name='folder_create'),
    path('pasta/<int:pk>/',         views.NoteFolderDetailView.as_view(), name='folder_detail'),
    path('pasta/<int:pk>/editar/',  views.NoteFolderUpdateView.as_view(), name='folder_update'),
    path('pasta/<int:pk>/excluir/', views.NoteFolderDeleteView.as_view(), name='folder_delete'),
    path('sem-pasta/',              views.NoteFolderlessView.as_view(),   name='folderless'),

    # ---------- Notas ----------
    path('todas/',      views.NoteListView.as_view(),   name='list'),
    path('criar/',      views.NoteCreateView.as_view(), name='create'),
    path('<int:pk>/',         views.NoteDetailView.as_view(),  name='detail'),
    path('<int:pk>/editar/',  views.NoteUpdateView.as_view(),  name='update'),
    path('<int:pk>/excluir/', views.NoteDeleteView.as_view(),  name='delete'),

    # ---------- IA ----------
    path('nota/<int:note_id>/gerar-flashcards/',  views.gerar_flashcards_nota,  name='gerar_flashcards_nota'),
    path('nota/<int:note_id>/salvar-flashcards/', views.salvar_flashcards_nota, name='salvar_flashcards_nota'),
    path('nota/<int:note_id>/gerar-questoes/',    views.gerar_questoes_nota,    name='gerar_questoes_nota'),
    path('nota/<int:note_id>/salvar-questoes/',   views.salvar_questoes_nota,   name='salvar_questoes_nota'),
]
