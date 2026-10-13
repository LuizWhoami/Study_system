import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from apps.study.models import StudySession, DailyProgress
from apps.subjects.models import Topic
from apps.study_config.models import PlannedSession
from apps.learning.services import LearningEngine

logger = logging.getLogger(__name__)

# Dias da semana em português — usado na agenda do dashboard.
WEEKDAYS_PT = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']


@login_required
def index(request):
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # ===== Horas estudadas (hoje / semana / mês) =====
    sessions_today = StudySession.objects.filter(user=user, start_time__date=today)
    total_minutes_today = sessions_today.aggregate(total=Sum('duration_minutes'))['total'] or 0
    hours_today = round(total_minutes_today / 60, 2) if total_minutes_today else 0.0

    sessions_week = StudySession.objects.filter(user=user, start_time__date__gte=week_ago)
    total_minutes_week = sessions_week.aggregate(total=Sum('duration_minutes'))['total'] or 0
    hours_week = round(total_minutes_week / 60, 2) if total_minutes_week else 0.0

    sessions_month = StudySession.objects.filter(user=user, start_time__date__gte=month_ago)
    total_minutes_month = sessions_month.aggregate(total=Sum('duration_minutes'))['total'] or 0
    hours_month = round(total_minutes_month / 60, 2) if total_minutes_month else 0.0

    # ===== Progresso diário (questões) =====
    progress_today = DailyProgress.objects.filter(user=user, date=today).first()
    questions_today = progress_today.questions_solved if progress_today else 0
    correct_today = progress_today.correct_answers if progress_today else 0
    accuracy = round((correct_today / questions_today) * 100, 2) if questions_today > 0 else 0.0

    # ===== Revisões pendentes =====
    reviews_pending = Topic.objects.filter(
        subject__contest__user=user,
        status='review_pending'
    ).count()

    # ===== Streak =====
    streak = 0
    current_date = today
    while True:
        daily = DailyProgress.objects.filter(user=user, date=current_date).first()
        if daily and daily.hours_studied > 0:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    # ===== Progresso geral =====
    total_topics = Topic.objects.filter(subject__contest__user=user).count()
    mastered_topics = Topic.objects.filter(
        subject__contest__user=user, status='mastered'
    ).count()
    progress_general = round((mastered_topics / total_topics) * 100, 2) if total_topics > 0 else 0.0

    # ===== Últimas 5 sessões =====
    last_sessions = (
        StudySession.objects
        .filter(user=user)
        .select_related('topic', 'topic__subject')
        .order_by('-start_time')[:5]
    )

    # ===== Sessões PLANEJADAS de HOJE (fonte: PlannedSession) =====
    today_sessions = (
        PlannedSession.objects
        .filter(user=user, date=today)
        .select_related('contest', 'topic', 'topic__subject')
        .order_by('start_time')
    )

    # ===== Agenda da semana (Seg → Dom) =====
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    week_sessions = (
        PlannedSession.objects
        .filter(user=user, date__gte=start_of_week, date__lte=end_of_week)
        .select_related('contest', 'topic', 'topic__subject')
        .order_by('date', 'start_time')
    )

    # Inicializa o dicionário dos 7 dias
    week_by_day = []
    for i in range(7):
        d = start_of_week + timedelta(days=i)
        week_by_day.append({
            'date': d,
            'day_name': WEEKDAYS_PT[i],
            'is_today': d == today,
            'sessions': [],
            'planned_minutes': 0,
            'completed_minutes': 0,
        })

    # Distribui as sessões por dia
    for s in week_sessions:
        for dia in week_by_day:
            if dia['date'] == s.date:
                dia['sessions'].append(s)
                if s.status != 'skipped':
                    dia['planned_minutes'] += s.duration_minutes
                if s.status == 'completed':
                    dia['completed_minutes'] += s.duration_minutes
                break

    # ===== Stats agregados da semana =====
    planned_minutes_wk = sum(
        s.duration_minutes for s in week_sessions if s.status != 'skipped'
    )
    completed_minutes_wk = sum(
        s.duration_minutes for s in week_sessions if s.status == 'completed'
    )
    weekly_stats = {
        'planned_count': sum(1 for s in week_sessions if s.status != 'skipped'),
        'completed_count': sum(1 for s in week_sessions if s.status == 'completed'),
        'skipped_count': sum(1 for s in week_sessions if s.status == 'skipped'),
        'planned_minutes': planned_minutes_wk,
        'completed_minutes': completed_minutes_wk,
        'planned_hours': round(planned_minutes_wk / 60, 1),
        'completed_hours': round(completed_minutes_wk / 60, 1),
        'percent': (
            int(completed_minutes_wk / planned_minutes_wk * 100)
            if planned_minutes_wk > 0 else 0
        ),
    }

    # ===== LearningEngine (sugestão inteligente) =====
    try:
        engine = LearningEngine(user)
        today_plan = engine.get_today_plan()
    except Exception as e:
        logger.error(f'Erro ao carregar Learning Engine: {e}')
        today_plan = None

    # ===== Meta diária =====
    daily_goal_hours = float(user.daily_goal_hours) if user.daily_goal_hours else 3.0

    context = {
        # métricas existentes
        'hours_today': hours_today,
        'hours_week': hours_week,
        'hours_month': hours_month,
        'questions_today': questions_today,
        'accuracy': accuracy,
        'reviews_pending': reviews_pending,
        'streak': streak,
        'progress_general': progress_general,
        'last_sessions': last_sessions,
        'daily_goal_hours': daily_goal_hours,
        'today_plan': today_plan,
        # novos (Fase 2)
        'today': today,
        'today_sessions': today_sessions,
        'week_by_day': week_by_day,
        'weekly_stats': weekly_stats,
    }
    return render(request, 'dashboard/index.html', context)
