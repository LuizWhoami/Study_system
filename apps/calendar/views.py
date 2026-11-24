from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, timedelta, date
from .models import StudyDay
from apps.study.models import StudyContent
from apps.subjects.models import Topic
import logging

logger = logging.getLogger(__name__)

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

    # Se for 'none', remove o dia e também as revisões associadas
    if activity == 'none':
        StudyDay.objects.filter(user=request.user, date=day_date).delete()
        # Remove qualquer StudyContent com next_review nesta data
        StudyContent.objects.filter(user=request.user, next_review=day_date).delete()
        logger.info(f"Atividade e revisões removidas para {day_date}")
        return JsonResponse({'success': True, 'cleared': True})

    # Salva ou atualiza StudyDay
    obj, created = StudyDay.objects.update_or_create(
        user=request.user,
        date=day_date,
        defaults={'activity': activity, 'notes': notes}
    )

    # Se atividade for "review", cria/atualiza StudyContent com a data
    if activity == 'review':
        user = request.user
        # Busca um tópico que o usuário já tenha estudado ou qualquer tópico
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
