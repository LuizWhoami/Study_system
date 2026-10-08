from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
import logging

from .models import StudyDay
from apps.study.models import StudyContent, StudySession
from apps.subjects.models import Topic

logger = logging.getLogger(__name__)


# ============================================================
# CONTEXTO DE ESTATÍSTICAS (movido de study_config.stats_view)
# ============================================================
def _build_stats_context(user):
    """Monta o dicionário de estatísticas usado no template."""
    from apps.flashcards.models import Flashcard
    from apps.questions.models import Question
    from apps.study_config.models import StudyConfig

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())

    # Sessões
    sessions = StudySession.objects.filter(user=user)
    total_hours = sum(s.duration_minutes for s in sessions) / 60 if sessions else 0
    sessions_week = sessions.filter(start_time__date__gte=start_of_week)
    hours_week = sum(s.duration_minutes for s in sessions_week) / 60 if sessions_week else 0

    # Progresso por matéria
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

    # Flashcards / questões
    flashcards_total = Flashcard.objects.filter(user=user).count()
    flashcards_pending = Flashcard.objects.filter(
        user=user, proxima_revisao__lte=today
    ).count()
    questions_total = Question.objects.filter(user=user).count()

    # Meta semanal
    config = StudyConfig.objects.filter(user=user, is_active=True).first()
    target_hours = float(config.target_hours_week) if config and config.target_hours_week else 15.0

    last_sessions = sessions.order_by('-start_time')[:5]

    return {
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


# ============================================================
# CALENDÁRIO
# ============================================================
@login_required
def calendar_view(request):
    today = date.today()
    base_date_str = request.GET.get('date')
    if base_date_str:
        try:
            base_date = datetime.strptime(base_date_str, '%Y-%m-%d').date()
        except ValueError:
            base_date = today
    else:
        base_date = today

    start_of_week = base_date - timedelta(days=base_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    week_days = []
    current = start_of_week
    while current <= end_of_week:
        try:
            day_obj = StudyDay.objects.get(user=request.user, date=current)
            activity = day_obj.activity
            notes = day_obj.notes
        except StudyDay.DoesNotExist:
            activity = None
            notes = ''

        review = StudyContent.objects.filter(user=request.user, next_review=current).first()
        has_review = review is not None
        review_topic = review.topic.name if review else None

        week_days.append({
            'date': current,
            'day': current.day,
            'weekday': current.weekday(),
            'weekday_name': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][current.weekday()],
            'activity': activity,
            'notes': notes,
            'is_today': current == today,
            'is_past': current < today,
            'has_review': has_review,
            'review_topic': review_topic,
        })
        current += timedelta(days=1)

    prev_week = start_of_week - timedelta(days=7)
    next_week = start_of_week + timedelta(days=7)

    context = {
        'week_days': week_days,
        'week_start': start_of_week,
        'week_end': end_of_week,
        'prev_week': prev_week.strftime('%Y-%m-%d'),
        'next_week': next_week.strftime('%Y-%m-%d'),
        'today': today,
    }
    # Adiciona estatísticas ao contexto (fundidas)
    context.update(_build_stats_context(request.user))

    return render(request, 'calendar/calendar.html', context)


@login_required
def set_activity(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    date_str = request.POST.get('date')
    activity = request.POST.get('activity')
    notes = request.POST.get('notes', '')

    if not date_str or not activity:
        return JsonResponse({'error': 'Data e atividade são obrigatórias'}, status=400)

    try:
        day_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Data inválida'}, status=400)

    if activity == 'none':
        StudyDay.objects.filter(user=request.user, date=day_date).delete()
        StudyContent.objects.filter(user=request.user, next_review=day_date).delete()
        logger.info(f"Atividade e revisões removidas para {day_date}")
        return JsonResponse({'success': True, 'cleared': True})

    obj, created = StudyDay.objects.update_or_create(
        user=request.user,
        date=day_date,
        defaults={'activity': activity, 'notes': notes}
    )

    if activity == 'review':
        user = request.user
        existing_content = StudyContent.objects.filter(user=user).order_by('next_review').first()
        if existing_content:
            topic = existing_content.topic
        else:
            topic = Topic.objects.filter(subject__contest__user=user).first()
            if not topic:
                logger.warning(f"Usuário {user.username} não tem tópicos para revisão.")
                return JsonResponse({'success': True, 'warning': 'Nenhum tópico disponível para revisão.'})

        content, created = StudyContent.objects.get_or_create(
            user=user,
            topic=topic,
            defaults={'difficulty': 3, 'next_review': day_date, 'review_count': 0}
        )
        if not created:
            content.next_review = day_date
            content.review_count += 1
            content.save()
        logger.info(f"Revisão agendada para {day_date} - Tópico: {topic.name}")

    return JsonResponse({
        'success': True,
        'created': created,
        'activity': obj.get_activity_display(),
    })
