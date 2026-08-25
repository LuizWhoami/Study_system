import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Note, Tag
from .forms import NoteForm  # <-- Importação adicionada
from apps.subjects.models import Topic
from apps.core.services import GroqService
from apps.flashcards.models import Flashcard

logger = logging.getLogger(__name__)

# ============================
# VIEWS CRUD PARA NOTAS
# ============================

class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'notes/list.html'
    context_object_name = 'notes'

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    form_class = NoteForm
    template_name = 'notes/form.html'
    success_url = reverse_lazy('notes:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = 'notes/form.html'
    success_url = reverse_lazy('notes:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = 'notes/confirm_delete.html'
    success_url = reverse_lazy('notes:list')

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

class NoteDetailView(LoginRequiredMixin, DetailView):
    model = Note
    template_name = 'notes/detail.html'
    context_object_name = 'note'

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

# ============================
# FLASHCARDS COM IA
# ============================

@login_required
def gerar_flashcards_nota(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    service = GroqService()
    flashcards = service.gerar_flashcards(note.content, quantidade=5)
    if not flashcards:
        return JsonResponse({'flashcards': [], 'error': 'Não foi possível gerar flashcards. Verifique o conteúdo da nota.'})
    return JsonResponse({'flashcards': flashcards, 'note_id': note.id})

@login_required
@csrf_exempt
def salvar_flashcards_nota(request, note_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    note = get_object_or_404(Note, id=note_id, user=request.user)
    try:
        data = json.loads(request.body)
        flashcards = data.get('flashcards', [])
        for f in flashcards:
            Flashcard.objects.create(
                user=request.user,
                topic=note.topic,
                pergunta=f.get('pergunta', ''),
                resposta=f.get('resposta', ''),
                nivel=3
            )
        return JsonResponse({'success': True, 'count': len(flashcards)})
    except Exception as e:
        logger.error(f'Erro ao salvar flashcards: {e}')
        return JsonResponse({'error': str(e)}, status=500)

# ============================
# AUTOSAVE (AJAX)
# ============================

@login_required
@csrf_exempt
def autosave_note(request, pk=None):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    content = request.POST.get('content', '').strip()
    title = request.POST.get('title', '').strip()

    if not title:
        return JsonResponse({'error': 'Título é obrigatório'}, status=400)

    if pk:
        note = get_object_or_404(Note, pk=pk, user=request.user)
        note.content = content
        note.title = title
        note.save()
        return JsonResponse({'success': True, 'id': note.id})
    else:
        topic = Topic.objects.filter(subject__contest__user=request.user).first()
        note = Note.objects.create(
            user=request.user,
            topic=topic,
            title=title,
            content=content
        )
        return JsonResponse({'success': True, 'id': note.id})
