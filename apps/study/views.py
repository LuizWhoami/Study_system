import logging
import traceback
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from .models import StudySession, DailyProgress, StudyContent
from apps.subjects.models import Subject, Topic
from apps.contests.models import Contest

logger = logging.getLogger(__name__)

@login_required
def study_view(request):
    estudos = Contest.objects.filter(user=request.user)
    return render(request, 'study/study.html', {'estudos': estudos})

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

@login_required
def start_session(request):
    if request.method == 'POST':
        try:
            assunto_id = request.POST.get('topic')
            if not assunto_id:
                return JsonResponse({'error': 'Assunto não informado'}, status=400)
            assunto = get_object_or_404(Topic, id=assunto_id, subject__contest__user=request.user)
            session = StudySession.objects.create(
                user=request.user,
                topic=assunto,
                start_time=timezone.now()
            )
            logger.info(f'Sessão iniciada: {session.id}')
            return JsonResponse({'session_id': session.id})
        except Exception as e:
            logger.error(f'Erro ao iniciar sessão: {str(e)}\n{traceback.format_exc()}')
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método inválido'}, status=400)

@login_required
def end_session(request):
    if request.method == 'POST':
        try:
            session_id = request.POST.get('session_id')
            duration_minutes = request.POST.get('duration_minutes')
            logger.info(f'Dados recebidos: session_id={session_id}, duration={duration_minutes}')
            if not session_id or not duration_minutes:
                return JsonResponse({'error': 'Dados incompletos'}, status=400)
            try:
                duration_minutes = int(duration_minutes)
            except ValueError:
                return JsonResponse({'error': 'Duração inválida'}, status=400)
            session = get_object_or_404(StudySession, id=session_id, user=request.user)
            session.end_time = timezone.now()
            session.duration_minutes = duration_minutes
            session.save()
            today = timezone.now().date()
            hours = Decimal(str(duration_minutes)) / Decimal('60')
            progress, created = DailyProgress.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={
                    'hours_studied': Decimal('0'),
                    'questions_solved': 0,
                    'correct_answers': 0,
                    'flashcards_reviewed': 0
                }
            )
            progress.hours_studied += hours
            progress.save()
            logger.info(f'Sessão finalizada: {session.id} - {duration_minutes} min, horas={hours}')
            return JsonResponse({'success': True, 'hours': float(hours), 'duration': duration_minutes})
        except Exception as e:
            logger.error(f'Erro ao finalizar sessão: {str(e)}\n{traceback.format_exc()}')
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método inválido'}, status=400)

@login_required
def mark_studied(request):
    if request.method == 'POST':
        try:
            topic_id = request.POST.get('topic_id')
            difficulty = request.POST.get('difficulty', 3)
            if not topic_id:
                return JsonResponse({'error': 'Tópico não informado'}, status=400)
            topic = get_object_or_404(Topic, id=topic_id, subject__contest__user=request.user)
            content, created = StudyContent.objects.get_or_create(
                user=request.user,
                topic=topic,
                defaults={'difficulty': difficulty}
            )
            if not created:
                content.difficulty = difficulty
                content.save()
            content.schedule_next_review()
            return JsonResponse({
                'success': True,
                'next_review': content.next_review.strftime('%Y-%m-%d'),
                'review_count': content.review_count
            })
        except Exception as e:
            logger.error(f'Erro ao marcar estudado: {e}')
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def pending_reviews(request):
    try:
        today = timezone.now().date()
        contents = StudyContent.objects.filter(
            user=request.user,
            next_review__lte=today + timedelta(days=3)
        ).order_by('next_review')
        data = []
        for c in contents:
            data.append({
                'id': c.id,
                'topic': c.topic.name,
                'subject': c.topic.subject.name,
                'next_review': c.next_review.strftime('%d/%m/%Y'),
                'days_until': (c.next_review - today).days,
                'difficulty': c.get_difficulty_display(),
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f'Erro em pending_reviews: {e}')
        return JsonResponse({'error': str(e)}, status=500)
