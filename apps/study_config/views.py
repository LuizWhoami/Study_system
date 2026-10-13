import json
import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import StudyConfig, PlannedSession
from .services import PlanningService
from apps.contests.models import Contest
from apps.subjects.models import Topic
from apps.learning.services import LearningEngine

logger = logging.getLogger(__name__)

@login_required
def config_view(request):
    """
    Página principal de configuração (wizard evoluído).

    IMPORTANTE: não faz get_or_create aqui. O plano só é persistido quando
    o usuário clica em Salvar. Sem isso, o plano "voltava" após ser excluído
    (get_or_create recriava um vazio a cada visita a /config/).
    """
    config = StudyConfig.objects.filter(user=request.user).first()
    is_new = config is None
    if is_new:
        config = StudyConfig(user=request.user)  # em memória, não salvo

    contests = Contest.objects.filter(user=request.user)
    selected_ids = list(config.selected_contests.values_list('id', flat=True)) if config.pk else []

    has_history = LearningEngine(request.user).get_today_plan() is not None

    context = {
        'config': config,
        'contests': contests,
        'selected_ids': selected_ids,
        'step': int(request.GET.get('step', 1)),
        'has_history': has_history,
        'is_new': is_new,
    }
    return render(request, 'study_config/config.html', context)

@login_required
def preview_config(request):
    """Prévia inteligente com diagnóstico e alertas."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    try:
        data = json.loads(request.body)
        user = request.user
        engine = LearningEngine(user)

        # Extrair dados
        max_subjects = int(data.get('max_subjects', 3))
        selected_ids = data.get('selected_contests', [])
        target_hours = float(data.get('target_hours_week', 15))
        available_hours = float(data.get('available_hours', 0))
        diagnostic = data.get('diagnostic_level', '')

        # Calcular disponibilidade (se fornecida)
        conflicts = []
        if available_hours > 0 and target_hours > available_hours:
            conflicts.append({
                'type': 'meta_maior_que_disponibilidade',
                'message': f'Sua meta é de {target_hours}h por semana, mas sua disponibilidade atual é de {available_hours}h. Considere ajustar a meta ou aumentar a disponibilidade.'
            })

        # Usar Learning Engine para identificar pontos fracos (se houver histórico)
        weak_topics = engine.identify_weak_topics(limit=3)

        # Estratégia recomendada (simplificada)
        strategy = {}
        if weak_topics:
            strategy['focus'] = [{'topic': wt['topic'].name, 'mastery': wt['mastery']} for wt in weak_topics[:2]]
            strategy['recommendation'] = f"Priorizar {', '.join([wt['topic'].name for wt in weak_topics[:2]])}"
        else:
            strategy['recommendation'] = "Distribuição equilibrada entre todas as matérias."

        response = {
            'total_hours': target_hours,
            'selected_count': len(selected_ids),
            'conflicts': conflicts,
            'has_conflicts': len(conflicts) > 0,
            'is_valid': len(conflicts) == 0 and len(selected_ids) > 0,
            'weak_topics': weak_topics,
            'strategy': strategy,
        }
        return JsonResponse(response)
    except Exception as e:
        logger.error(f'Erro na prévia: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def save_config(request):
    """Salva a configuração e gera o plano inicial."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    try:
        data = json.loads(request.body)
        user = request.user
        config, created = StudyConfig.objects.get_or_create(user=user)
        
        # Etapa 1: Objetivo
        config.objective = data.get('objective', 'concurso')
        config.objective_custom = data.get('objective_custom', '')
        config.level = data.get('level', 'intermediario')
        config.priority = data.get('priority', 'alta')
        
        # Etapa 2: Matérias
        config.max_subjects = int(data.get('max_subjects', 3))
        selected_ids = data.get('selected_contests', [])
        config.selected_contests.set(selected_ids)
        
        # Etapa 3: Disponibilidade
        # Aceita 2 formatos:
        #   1) availability: [{day, periods}, ...]   (formato novo)
        #   2) available_days + hours_per_day         (formato atual do frontend)
        availability_in = data.get('availability') or []
        available_days_in = data.get('available_days') or []
        hours_per_day = float(data.get('hours_per_day', 3) or 3)

        if availability_in:
            # Formato novo — usa direto
            config.availability = availability_in
            config.available_days = [d['day'] for d in availability_in if d.get('day')]
        elif available_days_in:
            # Formato do frontend atual — deriva availability a partir de available_days + hours_per_day
            start_dt = datetime(2000, 1, 1, 19, 0)
            end_dt = start_dt + timedelta(hours=hours_per_day)
            period = {
                'start': start_dt.strftime('%H:%M'),
                'end': end_dt.strftime('%H:%M'),
            }
            config.availability = [
                {'day': d, 'periods': [period]} for d in available_days_in
            ]
            config.available_days = list(available_days_in)
        else:
            config.availability = []
            config.available_days = []

        config.hours_per_day = Decimal(str(hours_per_day))
        config.days_per_week = len(config.available_days)
        config.study_weekend = data.get('study_weekend', False)
        
        # Etapa 4: Metas
        config.min_hours_week = Decimal(str(data.get('min_hours_week', 10)))
        config.target_hours_week = Decimal(str(data.get('target_hours_week', 15)))
        config.max_hours_week = Decimal(str(data.get('max_hours_week', 18)))
        config.target_hours_month = Decimal(str(data.get('target_hours_month', 60)))
        config.sessions_per_week = int(data.get('sessions_per_week', 5))
        config.daily_goal_hours = Decimal(str(data.get('daily_goal_hours', 2)))
        config.target_questions_week = int(data.get('target_questions_week', 30))
        config.target_flashcards_week = int(data.get('target_flashcards_week', 20))
        
        # Etapa 5: Preferências
        config.preferred_methods = data.get('preferred_methods', [])
        config.session_duration = int(data.get('session_duration', 40))
        config.intensity = data.get('intensity', 'equilibrada')
        config.rest_days = data.get('rest_days', [])
        
        # Etapa 6: Diagnóstico
        config.diagnostic_level = data.get('diagnostic_level', '')
        if config.diagnostic_level:
            config.diagnostic_date = timezone.now()
        
        # Modo de adaptação
        config.adaptation_mode = data.get('adaptation_mode', 'assistida')
        
        config.is_active = True
        config.save()
        # Gerar plano inicial usando PlanningService
        service = PlanningService(user)
        sessions = service.generate_initial_plan() or []

        if not sessions:
            logger.warning(
                "Plano salvo mas nenhuma sessão gerada. user=%s, "
                "available_days=%s, contests=%s",
                user.username, config.available_days,
                list(config.selected_contests.values_list('name', flat=True)),
            )
            return JsonResponse({
                'success': False,
                'message': (
                    'Configuração salva, mas nenhuma sessão foi gerada. '
                    'Verifique se (1) você selecionou ao menos uma matéria, '
                    '(2) ao menos um dia da semana está marcado, e '
                    '(3) as matérias selecionadas têm tópicos cadastrados.'
                ),
                'sessions_count': 0,
                'reason': 'sem_sessoes_geradas',
            })

        return JsonResponse({
            'success': True,
            'message': f'Configuração salva e {len(sessions)} sessões planejadas!',
            'sessions_count': len(sessions),
        })
        
    except Exception as e:
        logger.error(f'Erro ao salvar configuração: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def recalculate_plan(request):
    """Endpoint para replanejar manualmente."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    try:
        service = PlanningService(request.user)
        result = service.recalculate_plan()
        return JsonResponse({
            'success': True,
            'message': f'Plano recalculado. {result["updated"]} sessões atualizadas, {result["created"]} nova(s) sessão(ões) criada(s).',
            'updated': result['updated'],
            'created': result['created']
        })
    except Exception as e:
        logger.error(f'Erro ao recalcular plano: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def meu_plano(request):
    """Página 'Meu Plano' com visão geral do planejamento e execução."""
    user = request.user
    config = StudyConfig.objects.filter(user=user, is_active=True).first()
    if not config:
        return redirect('study_config:config')
    
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Sessões da semana
    sessions = PlannedSession.objects.filter(
        user=user,
        date__gte=week_start,
        date__lte=week_end
    ).order_by('date', 'start_time')
    
    # Agrupar por dia
    week_plan = {}
    for day in range(7):
        d = week_start + timedelta(days=day)
        week_plan[d] = [s for s in sessions if s.date == d]
    
    # Estatísticas da semana
    planned_minutes = sum(s.duration_minutes for s in sessions if s.status != 'skipped')
    completed_minutes = sum(s.duration_minutes for s in sessions if s.status == 'completed')
    planned_hours = planned_minutes / 60
    completed_hours = completed_minutes / 60
    
    # Distribuição por matéria
    distribution = {}
    for s in sessions:
        key = s.contest.name
        distribution[key] = distribution.get(key, 0) + s.duration_minutes / 60
    
    # Pontos fracos (Learning Engine)
    engine = LearningEngine(user)
    weak_topics = engine.identify_weak_topics(limit=5)
    
    # Próxima atividade recomendada
    next_activity = engine.recommend_next_activity()
    
    context = {
        'config': config,
        'week_plan': week_plan,
        'planned_hours': round(planned_hours, 2),
        'completed_hours': round(completed_hours, 2),
        'percent': int((completed_hours / planned_hours) * 100) if planned_hours > 0 else 0,
        'distribution': distribution.items(),
        'weak_topics': weak_topics,
        'next_activity': next_activity,
        'today': today,
        'week_start': week_start,
        'week_end': week_end,
    }
    return render(request, 'study_config/meu_plano.html', context)

@login_required
def stats_view(request):
    """Página de estatísticas (mantida do sistema anterior)."""
    from apps.study.models import StudySession, StudyContent
    from apps.flashcards.models import Flashcard
    from apps.questions.models import Question, QuestionAttempt
    from datetime import timedelta
    from decimal import Decimal

    user = request.user
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())

    # Sessões de estudo
    sessions = StudySession.objects.filter(user=user)
    total_hours = sum(s.duration_minutes for s in sessions) / 60 if sessions else 0
    sessions_week = sessions.filter(start_time__date__gte=start_of_week)
    hours_week = sum(s.duration_minutes for s in sessions_week) / 60 if sessions_week else 0

    # Progresso por matéria (via StudyContent)
    contents = StudyContent.objects.filter(user=user)
    subjects_progress = {}
    for c in contents:
        subject_name = c.topic.subject.name
        if subject_name not in subjects_progress:
            subjects_progress[subject_name] = {'total': 0, 'reviewed': 0}
        subjects_progress[subject_name]['total'] += 1
        if c.review_count > 0:
            subjects_progress[subject_name]['reviewed'] += 1

    # Revisões pendentes
    pending_reviews = contents.filter(next_review__lte=today + timedelta(days=3))

    # Flashcards
    flashcards_total = Flashcard.objects.filter(user=user).count()
    flashcards_pending = Flashcard.objects.filter(user=user, proxima_revisao__lte=today).count()

    # Questões
    questions_total = Question.objects.filter(user=user).count()

    # Meta semanal (da configuração)
    config = StudyConfig.objects.filter(user=user, is_active=True).first()
    target_hours = float(config.target_hours_week) if config and config.target_hours_week else 15.0

    # Últimas sessões
    last_sessions = sessions.order_by('-start_time')[:5]

    context = {
        'total_hours': round(total_hours, 1),
        'hours_week': round(hours_week, 1),
        'subjects_progress': subjects_progress,
        'pending_reviews_count': pending_reviews.count(),
        'flashcards_total': flashcards_total,
        'flashcards_pending': flashcards_pending,
        'questions_total': questions_total,
        'target_hours': target_hours,
        'hours_progress': min(100, int((hours_week / target_hours) * 100)) if target_hours > 0 else 0,
        'config_active': config is not None,
        'last_sessions': last_sessions,
    }
    return render(request, 'study_config/stats.html', context)

@login_required
def planos_list(request):
    """Lista todos os planos de estudos do usuário."""
    planos = StudyConfig.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'study_config/planos_list.html', {'planos': planos})

@login_required
@require_POST
def plano_delete(request, pk):
    """
    Exclui um plano de estudos.
    Protegido por @login_required + @require_POST (antes aceitava GET
    e era possível apagar via <img src="...">).
    """
    plano = get_object_or_404(StudyConfig, pk=pk, user=request.user)

    nome = str(plano)
    era_ativo = plano.is_active

    plano.delete()

    if era_ativo:
        messages.success(request, f'Plano "{nome}" (que estava ativo) foi excluído.')
    else:
        messages.success(request, f'Plano "{nome}" excluído com sucesso.')

    return redirect('study_config:planos_list')

@login_required
@require_POST
def plano_activate(request, pk):
    """Ativa um plano (desativa os outros)."""
    plano = get_object_or_404(StudyConfig, pk=pk, user=request.user)
    # Desativa todos os outros planos do usuário
    StudyConfig.objects.filter(user=request.user, is_active=True).update(is_active=False)
    plano.is_active = True
    plano.save()
    messages.success(request, f'Plano "{plano}" ativado com sucesso.')
    return redirect('study_config:planos_list')

# ============================================================
# AÇÕES EM SESSÕES PLANEJADAS (Fase 2)
# ============================================================


@login_required
@require_POST
def session_complete(request, pk):
    """Marca uma sessão planejada como concluída."""
    sessao = get_object_or_404(PlannedSession, pk=pk, user=request.user)
    if sessao.status == 'skipped':
        messages.error(request, 'Uma sessão pulada não pode ser concluída.')
        return redirect('dashboard:index')

    sessao.status = 'completed'
    sessao.is_completed = True
    sessao.save(update_fields=['status', 'is_completed', 'updated_at'])
    messages.success(
        request,
        f'Sessão de {sessao.topic.name if sessao.topic else sessao.contest.name} concluída.'
    )
    return redirect('dashboard:index')


@login_required
@require_POST
def session_skip(request, pk):
    """Marca uma sessão planejada como pulada."""
    sessao = get_object_or_404(PlannedSession, pk=pk, user=request.user)
    if sessao.status == 'completed':
        messages.error(request, 'Uma sessão concluída não pode ser pulada.')
        return redirect('dashboard:index')

    sessao.status = 'skipped'
    sessao.save(update_fields=['status', 'updated_at'])
    messages.warning(
        request,
        f'Sessão de {sessao.topic.name if sessao.topic else sessao.contest.name} pulada.'
    )
    return redirect('dashboard:index')


@login_required
@require_POST
def session_reschedule(request, pk):
    """
    Reagenda uma sessão: marca a original como `rescheduled` e cria uma nova
    com a data/hora escolhidas. Preserva histórico.
    """
    sessao_original = get_object_or_404(PlannedSession, pk=pk, user=request.user)

    nova_data_str = request.POST.get('date')
    novo_inicio_str = request.POST.get('start_time')
    novo_fim_str = request.POST.get('end_time')

    if not nova_data_str:
        messages.error(request, 'Informe a nova data.')
        return redirect('dashboard:index')

    try:
        nova_data = datetime.strptime(nova_data_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Data inválida.')
        return redirect('dashboard:index')

    # Horários: se não vierem, mantém os originais
    try:
        novo_inicio = (
            datetime.strptime(novo_inicio_str, '%H:%M').time()
            if novo_inicio_str else sessao_original.start_time
        )
        novo_fim = (
            datetime.strptime(novo_fim_str, '%H:%M').time()
            if novo_fim_str else sessao_original.end_time
        )
    except ValueError:
        messages.error(request, 'Horário inválido.')
        return redirect('dashboard:index')

    # 1. Preserva a original marcando como reagendada
    sessao_original.status = 'rescheduled'
    sessao_original.save(update_fields=['status', 'updated_at'])

    # 2. Cria a nova
    PlannedSession.objects.create(
        user=request.user,
        contest=sessao_original.contest,
        topic=sessao_original.topic,
        date=nova_data,
        start_time=novo_inicio,
        end_time=novo_fim,
        duration_minutes=sessao_original.duration_minutes,
        session_type=sessao_original.session_type,
        priority=sessao_original.priority,
        reason=f'Reagendada de {sessao_original.date.strftime("%d/%m/%Y")}. {sessao_original.reason}'.strip(),
        origin='rescheduled',
        status='planned',
    )

    messages.success(request, f'Sessão reagendada para {nova_data.strftime("%d/%m/%Y")}.')
    return redirect('dashboard:index')
