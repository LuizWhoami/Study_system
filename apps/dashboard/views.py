import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.study.models import StudySession, DailyProgress
from apps.subjects.models import Topic
from apps.calendar.models import StudyDay
from apps.learning.services import LearningEngine

logger = logging.getLogger(__name__)

@login_required
def index(request):
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Horas estudadas HOJE
    sessions_today = StudySession.objects.filter(
        user=user,
        start_time__date=today
    )
    total_minutes_today = sessions_today.aggregate(total=Sum('duration_minutes'))['total'] or 0
    hours_today = round(total_minutes_today / 60, 2) if total_minutes_today else 0.0

    # Horas estudadas na SEMANA
    sessions_week = StudySession.objects.filter(
        user=user,
        start_time__date__gte=week_ago
    )
    total_minutes_week = sessions_week.aggregate(total=Sum('duration_minutes'))['total'] or 0
    hours_week = round(total_minutes_week / 60, 2) if total_minutes_week else 0.0

    # Horas estudadas no MÊS
    sessions_month = StudySession.objects.filter(
        user=user,
        start_time__date__gte=month_ago
    )
    total_minutes_month = sessions_month.aggregate(total=Sum('duration_minutes'))['total'] or 0
    hours_month = round(total_minutes_month / 60, 2) if total_minutes_month else 0.0

    # Progresso diário (questões de hoje)
    progress_today = DailyProgress.objects.filter(user=user, date=today).first()
    questions_today = progress_today.questions_solved if progress_today else 0
    correct_today = progress_today.correct_answers if progress_today else 0
    accuracy = round((correct_today / questions_today) * 100, 2) if questions_today > 0 else 0.0

    # Revisões pendentes (tópicos com status review_pending)
    reviews_pending = Topic.objects.filter(
        subject__contest__user=user,
        status='review_pending'
    ).count()

    # Streak
    streak = 0
    current_date = today
    while True:
        daily = DailyProgress.objects.filter(user=user, date=current_date).first()
        if daily and daily.hours_studied > 0:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    # Progresso geral (tópicos concluídos)
    total_topics = Topic.objects.filter(subject__contest__user=user).count()
    mastered_topics = Topic.objects.filter(subject__contest__user=user, status='mastered').count()
    progress_general = round((mastered_topics / total_topics) * 100, 2) if total_topics > 0 else 0.0

    # Últimas 5 sessões
    last_sessions = StudySession.objects.filter(user=user).order_by('-start_time')[:5]

    # Dados do calendário
    start_of_week = today - timedelta(days=today.weekday())
    week_plan = []
    days_of_week = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    for i in range(7):
        current_date = start_of_week + timedelta(days=i)
        try:
            day_obj = StudyDay.objects.get(user=user, date=current_date)
            activity = day_obj.activity
        except StudyDay.DoesNotExist:
            activity = None
        week_plan.append({
            'day_name': days_of_week[i],
            'date': current_date,
            'activity': activity,
            'is_today': current_date == today,
        })

    # Contagem de atividades
    activities_count = {
        'study': 0,
        'review': 0,
        'questions': 0,
        'summary': 0,
        'rest': 0,
    }
    for day in week_plan:
        if day['activity'] in activities_count:
            activities_count[day['activity']] += 1

    has_plan = any(day['activity'] is not None for day in week_plan)

    # Learning Engine - Plano do dia
    try:
        engine = LearningEngine(user)
        today_plan = engine.get_today_plan()
    except Exception as e:
        logger.error(f'Erro ao carregar Learning Engine: {e}')
        today_plan = None

    # Meta diária do usuário
    daily_goal_hours = float(user.daily_goal_hours) if user.daily_goal_hours else 3.0

    context = {
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
        'week_plan': week_plan,
        'activities_count': activities_count,
        'has_plan': has_plan,
        'today_plan': today_plan,
    }
    return render(request, 'dashboard/index.html', context)
