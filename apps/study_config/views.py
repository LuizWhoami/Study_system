import json
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import StudyConfig, PlannedSession
from apps.contests.models import Contest
from apps.study.models import StudySession, StudyContent

logger = logging.getLogger(__name__)

@login_required
def config_view(request):
    config, created = StudyConfig.objects.get_or_create(user=request.user)
    contests = Contest.objects.filter(user=request.user)
    selected_ids = config.selected_contests.values_list('id', flat=True)
    context = {
        'config': config,
        'contests': contests,
        'selected_ids': list(selected_ids),
        'step': int(request.GET.get('step', 1)),
    }
    return render(request, 'study_config/config.html', context)

@login_required
def preview_config(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    try:
        data = json.loads(request.body)
        max_subjects = int(data.get('max_subjects', 3))
        selected_contests = data.get('selected_contests', [])
        target_hours_week = float(data.get('target_hours_week', 15))
        days_per_week = int(data.get('days_per_week', 5))
        hours_per_day = float(data.get('hours_per_day', 3))
        total_hours = target_hours_week
        actual_hours = days_per_week * hours_per_day
        conflicts = []
        if actual_hours < total_hours:
            conflicts.append({
                'type': 'meta_maior_que_disponibilidade',
                'message': f'Sua meta é de {total_hours}h por semana, mas sua disponibilidade atual é de {actual_hours}h. Considere ajustar a meta ou aumentar a disponibilidade.'
            })
        if len(selected_contests) > max_subjects:
            conflicts.append({
                'type': 'muitas_materias',
                'message': f'Você selecionou {len(selected_contests)} matérias, mas o limite é {max_subjects}. Selecione apenas as prioridades.'
            })
        recommended_subjects = min(max_subjects, len(selected_contests))
        hours_per_subject = total_hours / recommended_subjects if recommended_subjects > 0 else 0
        response = {
            'total_hours': round(total_hours, 1),
            'actual_hours': round(actual_hours, 1),
            'selected_count': len(selected_contests),
            'recommended_subjects': recommended_subjects,
            'hours_per_subject': round(hours_per_subject, 1),
            'conflicts': conflicts,
            'has_conflicts': len(conflicts) > 0,
            'is_valid': len(conflicts) == 0 and len(selected_contests) > 0,
        }
        return JsonResponse(response)
    except Exception as e:
        logger.error(f'Erro na prévia: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def save_config(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    try:
        data = json.loads(request.body)
        config, created = StudyConfig.objects.get_or_create(user=request.user)
        
        # Etapa 1
        config.objective = data.get('objective', 'concurso')
        config.objective_custom = data.get('objective_custom', '')
        config.level = data.get('level', 'intermediario')
        config.priority = data.get('priority', 'alta')
        
        # Etapa 2
        config.max_subjects = int(data.get('max_subjects', 3))
        selected_ids = data.get('selected_contests', [])
        config.selected_contests.set(selected_ids)
        
        # Etapa 3
        config.available_days = data.get('available_days', [])
        config.hours_per_day = Decimal(str(data.get('hours_per_day', 3)))
        config.days_per_week = int(data.get('days_per_week', 5))
        config.study_weekend = data.get('study_weekend', False)
        
        # Etapa 4
        config.target_hours_week = Decimal(str(data.get('target_hours_week', 15)))
        config.target_hours_month = Decimal(str(data.get('target_hours_month', 60)))
        config.sessions_per_week = int(data.get('sessions_per_week', 5))
        config.daily_goal_hours = Decimal(str(data.get('daily_goal_hours', 2)))
        
        # Etapa 5
        config.active_recall = data.get('active_recall', True)
        config.spaced_repetition = data.get('spaced_repetition', True)
        config.practice_questions = data.get('practice_questions', True)
        config.flashcards_active = data.get('flashcards_active', True)
        config.interleaving = data.get('interleaving', True)
        config.active_review = data.get('active_review', True)
        
        # Etapa 6
        config.review_intervals = data.get('review_intervals', [1, 3, 7, 14, 30])
        config.review_intensity = int(data.get('review_intensity', 3))
        
        config.is_active = True
        config.save()
        
        generate_plan(request.user, config)
        
        return JsonResponse({'success': True, 'message': 'Configuração salva com sucesso!'})
        
    except Exception as e:
        logger.error(f'Erro ao salvar configuração: {e}')
        return JsonResponse({'error': str(e)}, status=500)

def generate_plan(user, config):
    """Gera sessões planejadas para as próximas 4 semanas."""
    PlannedSession.objects.filter(user=user, is_completed=False).delete()
    today = timezone.now().date()
    weeks_to_plan = 4
    
    selected_contests = config.selected_contests.all()
    if not selected_contests:
        return
    
    days_map = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    available_days = config.available_days or ['mon', 'tue', 'wed', 'thu', 'fri']
    hours_per_day = float(config.hours_per_day) if config.hours_per_day else 3.0
    
    subjects_list = list(selected_contests)
    import random
    random.shuffle(subjects_list)
    
    start_hour = 19
    end_hour = 22
    
    for week in range(weeks_to_plan):
        for day_offset in range(7):
            current_date = today + timedelta(days=week*7 + day_offset)
            day_name = days_map[current_date.weekday()]
            if day_name not in available_days:
                continue
            if not subjects_list:
                break
            subject_idx = (day_offset) % len(subjects_list)
            subject = subjects_list[subject_idx]
            duration_minutes = int(hours_per_day * 60)
            PlannedSession.objects.create(
                user=user,
                contest=subject,
                date=current_date,
                start_time=datetime.strptime(f"{start_hour:02d}:00", '%H:%M').time(),
                end_time=datetime.strptime(f"{end_hour:02d}:00", '%H:%M').time(),
                duration_minutes=duration_minutes,
                subject_name=subject.name,
                session_type='study'
            )

@login_required
def stats_view(request):
    """Página de estatísticas com logs para depuração."""
    user = request.user
    config = StudyConfig.objects.filter(user=user, is_active=True).first()
    logger.info(f"Config encontrada: {config}")
    
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    sessions = StudySession.objects.filter(user=user)
    total_hours = sum(s.duration_minutes for s in sessions) / 60 if sessions else 0
    sessions_week = sessions.filter(start_time__date__gte=start_of_week)
    hours_week = sum(s.duration_minutes for s in sessions_week) / 60 if sessions_week else 0
    
    contents = StudyContent.objects.filter(user=user)
    subjects_progress = {}
    for c in contents:
        subject_name = c.topic.subject.name
        if subject_name not in subjects_progress:
            subjects_progress[subject_name] = {'total': 0, 'reviewed': 0}
        subjects_progress[subject_name]['total'] += 1
        if c.review_count > 0:
            subjects_progress[subject_name]['reviewed'] += 1
    
    pending_reviews = contents.filter(next_review__lte=today + timedelta(days=3))
    
    from apps.flashcards.models import Flashcard
    flashcards_total = Flashcard.objects.filter(user=user).count()
    flashcards_pending = Flashcard.objects.filter(user=user, proxima_revisao__lte=today).count()
    
    from apps.questions.models import Question
    questions_total = Question.objects.filter(user=user).count()
    
    target_hours = float(config.target_hours_week) if config and config.target_hours_week else 15.0
    
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
