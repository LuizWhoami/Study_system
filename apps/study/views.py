import logging

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta

from .models import StudyContent
from . import services
from .services import ActiveSessionExists, NoActiveSession
from apps.subjects.models import Subject, Topic
from apps.contests.models import Contest

logger = logging.getLogger(__name__)


# ============================================================
# PÁGINAS HTML
# ============================================================


# ============================================================
# ENDPOINTS AUXILIARES (selects em cascata)
# ============================================================
@login_required
def api_materias_por_estudo(request, estudo_id):
    estudo = get_object_or_404(Contest, id=estudo_id, user=request.user)
    materias = Subject.objects.filter(contest=estudo).values('id', 'name')
    return JsonResponse(list(materias), safe=False)


@login_required
def api_assuntos_por_materia(request, materia_id):
    materia = get_object_or_404(Subject, id=materia_id, contest__user=request.user)
    assuntos = Topic.objects.filter(subject=materia).values('id', 'name')
    return JsonResponse(list(assuntos), safe=False)


# ============================================================
# CRONÔMETRO — endpoints principais
# ============================================================
@login_required
@require_http_methods(['GET'])
def current_session(request):
    """Retorna o estado atual do cronômetro. Usado em TODA página autenticada."""
    session = services.get_current_session(request.user)
    return JsonResponse(services.serialize_session(session))


@login_required
@require_http_methods(['POST'])
def start_session(request):
    """
    Cria nova sessão. Mantém compatibilidade com o frontend antigo.

    POST: topic=<id>
    Retorna: {'session_id': N} ou erro.
    """
    topic_id = request.POST.get('topic')
    if not topic_id:
        return JsonResponse({'error': 'Assunto não informado'}, status=400)

    topic = get_object_or_404(Topic, id=topic_id, subject__contest__user=request.user)

    try:
        session = services.start_session(request.user, topic)
    except ActiveSessionExists as exc:
        return JsonResponse(
            {
                'error': 'Já existe uma sessão ativa.',
                'active_session_id': exc.session.id,
                'active_session': services.serialize_session(exc.session),
            },
            status=409,
        )

    return JsonResponse({'session_id': session.id})


@login_required
@require_http_methods(['POST'])
def pause_session_view(request):
    try:
        session = services.pause_session(request.user)
    except NoActiveSession as exc:
        return JsonResponse({'error': str(exc)}, status=404)
    return JsonResponse({'success': True, 'session': services.serialize_session(session)})


@login_required
@require_http_methods(['POST'])
def resume_session_view(request):
    try:
        session = services.resume_session(request.user)
    except NoActiveSession as exc:
        return JsonResponse({'error': str(exc)}, status=404)
    return JsonResponse({'success': True, 'session': services.serialize_session(session)})


@login_required
@require_http_methods(['POST'])
def end_session(request):
    """
    Finaliza a sessão ativa.

    Compatibilidade:
    - O frontend antigo envia `session_id` e `duration_minutes`.
    - O `duration_minutes` é IGNORADO. O servidor calcula a duração real.
    - O `session_id` é validado (se enviado) contra a sessão ativa.

    Retorna (formato legado): {'success': True, 'hours': ..., 'duration': ...}
    """
    session_id = request.POST.get('session_id')

    try:
        if session_id:
            # Frontend antigo pode estar finalizando uma sessão específica.
            # Só aceitamos se for a mesma do usuário.
            from .models import StudySession
            stale = StudySession.objects.filter(id=session_id, user=request.user).first()
            current = services.get_current_session(request.user)
            if stale and current and stale.id != current.id:
                return JsonResponse({'error': 'Sessão não é a ativa.'}, status=400)

        session = services.finish_session(request.user)
    except NoActiveSession as exc:
        return JsonResponse({'error': str(exc)}, status=404)

    hours = round(session.duration_minutes / 60, 2)
    return JsonResponse({
        'success': True,
        'hours': hours,
        'duration': session.duration_minutes,
    })


# ============================================================
# SRS / REVISÕES (existentes — inalterados)
# ============================================================
@login_required
@require_http_methods(['POST'])
def mark_studied(request):
    topic_id = request.POST.get('topic_id')
    difficulty = request.POST.get('difficulty', 3)
    if not topic_id:
        return JsonResponse({'error': 'Tópico não informado'}, status=400)

    topic = get_object_or_404(Topic, id=topic_id, subject__contest__user=request.user)

    content, created = StudyContent.objects.get_or_create(
        user=request.user,
        topic=topic,
        defaults={'difficulty': difficulty},
    )
    if not created:
        content.difficulty = difficulty
        content.save()

    content.schedule_next_review()
    return JsonResponse({
        'success': True,
        'next_review': content.next_review.strftime('%Y-%m-%d'),
        'review_count': content.review_count,
    })


@login_required
@require_http_methods(['GET'])
def pending_reviews(request):
    today = timezone.now().date()
    contents = StudyContent.objects.filter(
        user=request.user,
        next_review__lte=today + timedelta(days=3),
    ).order_by('next_review')

    data = [
        {
            'id': c.id,
            'topic': c.topic.name,
            'subject': c.topic.subject.name,
            'next_review': c.next_review.strftime('%d/%m/%Y'),
            'days_until': (c.next_review - today).days,
            'difficulty': c.get_difficulty_display(),
        }
        for c in contents
    ]
    return JsonResponse(data, safe=False)


# ============================================================
# API — lista de concursos (para o modal do timer global)
# ============================================================
@login_required
@require_http_methods(['GET'])
def api_contests(request):
    """Lista de concursos do usuário — usada pelo modal do cronômetro global."""
    contests = Contest.objects.filter(user=request.user).values('id', 'name')
    return JsonResponse(list(contests), safe=False)
