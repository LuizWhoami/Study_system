from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Flashcard
from apps.subjects.models import Topic
from apps.notes.models import Note
from datetime import date
import logging

logger = logging.getLogger(__name__)

@login_required
def listar_flashcards(request):
    hoje = date.today()
    flashcards = Flashcard.objects.filter(
        user=request.user,
        proxima_revisao__lte=hoje
    ).order_by('proxima_revisao')
    total_pendentes = flashcards.count()
    context = {
        'flashcards': flashcards,
        'total_pendentes': total_pendentes,
    }
    return render(request, 'flashcards/list.html', context)

@login_required
def revisar_flashcard(request, pk):
    flashcard = get_object_or_404(Flashcard, pk=pk, user=request.user)
    if request.method == 'POST':
        avaliacao = request.POST.get('avaliacao')
        if avaliacao in ['errei', 'dificil', 'bom', 'facil']:
            flashcard.revisar(avaliacao)
            return redirect('flashcards:listar')
    context = {'flashcard': flashcard}
    return render(request, 'flashcards/review.html', context)

@login_required
def criar_flashcard(request):
    topics = Topic.objects.filter(subject__contest__user=request.user).select_related('subject__contest')
    erro = None
    sucesso = None

    if request.method == 'POST':
        topic_id = request.POST.get('topic')
        pergunta = request.POST.get('pergunta')
        resposta = request.POST.get('resposta')
        nivel = request.POST.get('nivel', 3)

        if not all([topic_id, pergunta, resposta]):
            erro = 'Preencha todos os campos obrigatórios.'
        else:
            try:
                topic = get_object_or_404(Topic, id=topic_id, subject__contest__user=request.user)
                Flashcard.objects.create(
                    user=request.user,
                    topic=topic,
                    pergunta=pergunta,
                    resposta=resposta,
                    nivel=nivel
                )
                sucesso = 'Flashcard criado com sucesso!'
            except Exception as e:
                logger.error(f"Erro ao criar flashcard: {e}")
                erro = 'Erro ao criar flashcard. Tente novamente.'

    context = {
        'topics': topics,
        'erro': erro,
        'sucesso': sucesso,
    }
    return render(request, 'flashcards/criar.html', context)

@login_required
def estatisticas_flashcards(request):
    total = Flashcard.objects.filter(user=request.user).count()
    revisados_hoje = Flashcard.objects.filter(
        user=request.user,
        updated_at__date=date.today()
    ).count()
    pendentes = Flashcard.objects.filter(
        user=request.user,
        proxima_revisao__lte=date.today()
    ).count()
    por_materia = {}
    for flashcard in Flashcard.objects.filter(user=request.user):
        materia = flashcard.topic.subject.name
        por_materia[materia] = por_materia.get(materia, 0) + 1
    context = {
        'total': total,
        'revisados_hoje': revisados_hoje,
        'pendentes': pendentes,
        'por_materia': por_materia.items(),
    }
    return render(request, 'flashcards/estatisticas.html', context)

@login_required
def api_notas_por_topico(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, subject__contest__user=request.user)
    notas = Note.objects.filter(topic=topic, user=request.user).values('id', 'title')
    return JsonResponse(list(notas), safe=False)
