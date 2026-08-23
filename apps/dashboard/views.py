from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from apps.study.models import StudySession, DailyProgress
from apps.subjects.models import Topic
from apps.calendar.models import StudyDay

@login_required
def index(request):
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Horas estudadas
    sessions_today = StudySession.objects.filter(user=user, start_time__date=today)
    hours_today = (sessions_today.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60

    sessions_week = StudySession.objects.filter(user=user, start_time__date__gte=week_ago)
    hours_week = (sessions_week.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60

    sessions_month = StudySession.objects.filter(user=user, start_time__date__gte=month_ago)
    hours_month = (sessions_month.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60

    # Questões
    progress_today = DailyProgress.objects.filter(user=user, date=today).first()
    questions_today = progress_today.questions_solved if progress_today else 0
    correct_today = progress_today.correct_answers if progress_today else 0
    accuracy = (correct_today / questions_today * 100) if questions_today > 0 else 0

    # Revisões pendentes
    reviews_pending = Topic.objects.filter(subject__contest__user=user, status='review_pending').count()

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

    # Progresso geral
    total_topics = Topic.objects.filter(subject__contest__user=user).count()
    mastered = Topic.objects.filter(subject__contest__user=user, status='mastered').count()
    progress_general = (mastered / total_topics * 100) if total_topics > 0 else 0

    # Últimas sessões
    last_sessions = StudySession.objects.filter(user=user).order_by('-start_time')[:5]

    # ===== DADOS DO CALENDÁRIO (PLANEJAMENTO DA SEMANA) =====
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
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

    # Contagem de atividades planejadas para a semana
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

    context = {
        'hours_today': round(hours_today, 2),
        'hours_week': round(hours_week, 2),
        'hours_month': round(hours_month, 2),
        'questions_today': questions_today,
        'accuracy': round(accuracy, 2),
        'reviews_pending': reviews_pending,
        'streak': streak,
        'progress_general': round(progress_general, 2),
        'last_sessions': last_sessions,
        'daily_goal_hours': user.daily_goal_hours,
        # Dados do calendário
        'week_plan': week_plan,
        'activities_count': activities_count,
        'has_plan': any(day['activity'] is not None for day in week_plan),
    }
    return render(request, 'dashboard/index.html', context)
