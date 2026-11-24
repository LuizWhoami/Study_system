import json
import logging
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Note, Tag
from .forms import NoteForm
from apps.subjects.models import Topic
from apps.core.services import GroqService
from apps.flashcards.models import Flashcard
from apps.questions.models import Question

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
# QUESTÕES COM IA (EMBARALHAMENTO FORÇADO)
# ============================

def shuffle_alternatives(questao):
    """Embaralha as alternativas e atualiza a correta."""
    alt = questao.get('alternativas', {})
    if not alt or not isinstance(alt, dict):
        return questao

    # Pega a letra correta original e seu texto
    correta_original = questao.get('correta', 'a')
    texto_correta = alt.get(correta_original, '')

    # Embaralha as chaves
    keys = list(alt.keys())
    random.shuffle(keys)
    novas_alt = {k: alt[k] for k in keys}

    # Encontra a nova chave que contém o texto correto
    nova_correta = None
    for k, v in novas_alt.items():
        if v == texto_correta:
            nova_correta = k
            break

    questao['alternativas'] = novas_alt
    questao['correta'] = nova_correta if nova_correta else 'a'
    return questao

@login_required
def gerar_questoes_nota(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    service = GroqService()
    questoes = service.gerar_questoes(note.content, quantidade=3)
    if not questoes:
        return JsonResponse({'questoes': [], 'error': 'Não foi possível gerar questões. Verifique o conteúdo da nota.'})
    # Embaralha cada questão
    for q in questoes:
        shuffle_alternatives(q)
    return JsonResponse({'questoes': questoes, 'note_id': note.id})

@login_required
@csrf_exempt
def salvar_questoes_nota(request, note_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    note = get_object_or_404(Note, id=note_id, user=request.user)
    try:
        data = json.loads(request.body)
        questoes = data.get('questoes', [])
        for q in questoes:
            # Embaralha novamente (garantia extra)
            q = shuffle_alternatives(q)
            alt = q.get('alternativas', {})
            if isinstance(alt, str):
                alt = {}
            # Cria a questão
            Question.objects.create(
                user=request.user,
                topic=note.topic,
                enunciado=q.get('enunciado', ''),
                alternativa_a=alt.get('a', ''),
                alternativa_b=alt.get('b', ''),
                alternativa_c=alt.get('c', ''),
                alternativa_d=alt.get('d', ''),
                alternativa_correta=q.get('correta', 'a'),
                explicacao=q.get('explicacao', ''),
                dificuldade=3
            )
        return JsonResponse({'success': True, 'count': len(questoes)})
    except Exception as e:
        logger.error(f'Erro ao salvar questões: {e}')
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
