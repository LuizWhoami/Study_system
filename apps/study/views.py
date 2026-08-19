import logging
import traceback
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from .models import StudySession, DailyProgress
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
def api_topicos_por_materia(request, materia_id):
    materia = get_object_or_404(Subject, id=materia_id, contest__user=request.user)
    topicos = Topic.objects.filter(subject=materia).values('id', 'name')
    return JsonResponse(list(topicos), safe=False)

@login_required
def start_session(request):
    if request.method == 'POST':
        try:
            topic_id = request.POST.get('topic')
            if not topic_id:
                return JsonResponse({'error': 'Tópico não informado'}, status=400)
            topic = get_object_or_404(Topic, id=topic_id, subject__contest__user=request.user)
            session = StudySession.objects.create(
                user=request.user,
                topic=topic,
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
            
            # Converte para inteiro
            try:
                duration_minutes = int(duration_minutes)
            except ValueError:
                return JsonResponse({'error': 'Duração inválida'}, status=400)
            
            # Busca a sessão
            session = get_object_or_404(StudySession, id=session_id, user=request.user)
            session.end_time = timezone.now()
            session.duration_minutes = duration_minutes
            session.save()
            
            # Atualiza progresso diário
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
            return JsonResponse({'success': True, 'hours': float(hours)})
            
        except Exception as e:
            logger.error(f'Erro ao finalizar sessão: {str(e)}\n{traceback.format_exc()}')
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método inválido'}, status=400)
