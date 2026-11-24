from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Flashcard
from apps.subjects.models import Topic
from apps.notes.models import Note
from datetime import date
import logging
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.urls import reverse

logger = logging.getLogger(__name__)

@login_required
def listar_flashcards(request):
    """
    Lista categorizada + filtros por status e tópico.
    Query string:
      ?status=todos|atrasados|hoje|proximos|concluidos (padrão: todos)
      ?topic=<id>  (opcional)
    """
    hoje = timezone.localdate()
    status = request.GET.get('status', 'todos')
    topic_id = request.GET.get('topic', '').strip()

    todos = Flashcard.objects.filter(user=request.user).select_related('topic')

    # Filtro por tópico
    if topic_id and topic_id.isdigit():
        todos = todos.filter(topic_id=int(topic_id))

    # Contadores ANTES de filtrar por status (chips sempre mostram o real)
    atrasados_qs = todos.filter(proxima_revisao__lt=hoje)
    hoje_qs      = todos.filter(proxima_revisao=hoje)
    proximos_qs  = todos.filter(proxima_revisao__gt=hoje)

    contadores = {
        'todos':      todos.count(),
        'atrasados':  atrasados_qs.count(),
        'hoje':       hoje_qs.count(),
        'proximos':   proximos_qs.count(),
    }

    # Aplica filtro de status
    if status == 'atrasados':
        atrasados_list = atrasados_qs.order_by('proxima_revisao')
        hoje_list, proximos_list, concluidos_list = [], [], []
    elif status == 'hoje':
        atrasados_list, proximos_list, concluidos_list = [], [], []
        hoje_list = hoje_qs.order_by('id')
    elif status == 'proximos':
        atrasados_list, hoje_list, concluidos_list = [], [], []
        proximos_list = proximos_qs.order_by('proxima_revisao')[:50]
    elif status == 'concluidos':
        atrasados_list, hoje_list, proximos_list = [], [], []
        concluidos_list = todos.filter(
            vezes_revisado__gt=0,
            updated_at__date=hoje,
        ).order_by('-updated_at')[:50]
    else:  # todos
        atrasados_list = atrasados_qs.order_by('proxima_revisao')
        hoje_list      = hoje_qs.order_by('id')
        proximos_list  = proximos_qs.order_by('proxima_revisao')[:30]
        concluidos_list = todos.filter(
            vezes_revisado__gt=0,
            updated_at__date=hoje,
        ).order_by('-updated_at')[:10]

    total_pendentes = contadores['atrasados'] + contadores['hoje']

    # Tópicos do usuário (para o dropdown de filtro)
    from apps.subjects.models import Topic
    topics = (
        Topic.objects
        .filter(subjects_owned__isnull=False) if False else  # placeholder
        Topic.objects.filter(flashcards__user=request.user).distinct()
    )

    context = {
        'flashcards':        todos,
        'total_pendentes':   total_pendentes,
        'atrasados_list':    atrasados_list,
        'hoje_list':         hoje_list,
        'proximos_list':     proximos_list,
        'concluidos_list':   concluidos_list,
        'contadores':        contadores,
        'status_ativo':      status,
        'topic_ativo':       int(topic_id) if topic_id.isdigit() else None,
        'topics':            topics,
    }
    return render(request, 'flashcards/list.html', context)


@login_required
@require_http_methods(['POST'])
def excluir_flashcard(request, pk):
    """Remove um flashcard. Preserva o filtro ativo via ?next= ou referrer."""
    from django.utils.http import url_has_allowed_host_and_scheme
    from django.contrib import messages

    fc = get_object_or_404(Flashcard, pk=pk, user=request.user)
    fc.delete()
    messages.success(request, 'Flashcard removido.')

    next_url = request.POST.get('next') or ''
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(reverse('flashcards:listar'))


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
        updated_at__date=timezone.localdate()
    ).count()
    pendentes = Flashcard.objects.filter(
        user=request.user,
        proxima_revisao__lte=timezone.localdate()
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


@login_required
@require_http_methods(['POST'])
def excluir_flashcard(request, pk):
    """Remove um flashcard. Preserva o filtro ativo via ?next=."""
    from django.utils.http import url_has_allowed_host_and_scheme
    from django.contrib import messages

    fc = get_object_or_404(Flashcard, pk=pk, user=request.user)
    fc.delete()
    messages.success(request, 'Flashcard removido.')

    next_url = request.POST.get('next') or ''
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(reverse('flashcards:listar'))
