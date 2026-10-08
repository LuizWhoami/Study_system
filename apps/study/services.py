"""
Regras de negócio do cronômetro de estudo.

A view NUNCA deve:
- aceitar duração vinda do cliente
- criar sessão sem checar se já existe ativa
- finalizar sessão sem calcular tempo real

Todo esse fluxo vive aqui.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import StudySession, DailyProgress

logger = logging.getLogger(__name__)


# ============================================================
# EXCEÇÕES DE DOMÍNIO
# ============================================================
class StudySessionError(Exception):
    """Erro base para operações do cronômetro."""


class ActiveSessionExists(StudySessionError):
    """Já existe uma sessão ativa para o usuário."""
    def __init__(self, session):
        self.session = session
        super().__init__(
            f'Já existe uma sessão ativa (id={session.id}, status={session.status}).'
        )


class NoActiveSession(StudySessionError):
    """Não há sessão ativa para operar."""
    def __init__(self, message='Nenhuma sessão ativa encontrada.'):
        super().__init__(message)


# ============================================================
# LEITURA
# ============================================================
def get_current_session(user):
    """Retorna a sessão ativa do usuário (RUNNING ou PAUSED) ou None."""
    return StudySession.get_active_for_user(user)


def serialize_session(session):
    """Formato padrão para a API do timer."""
    if session is None:
        return {'active': False}
    return {
        'active': True,
        'id': session.id,
        'status': session.status,
        'topic_id': session.topic_id,
        'topic_name': session.topic.name if session.topic else None,
        'subject_name': session.topic.subject.name if session.topic else None,
        'contest_name': session.topic.subject.contest.name if session.topic else None,
        'start_time': session.start_time.isoformat(),
        'paused_at': session.paused_at.isoformat() if session.paused_at else None,
        'elapsed_seconds': session.elapsed_seconds,
        'elapsed_minutes': session.elapsed_minutes,
        'total_paused_seconds': session.total_paused_seconds,
    }


# ============================================================
# ESCRITA
# ============================================================
@transaction.atomic
def start_session(user, topic):
    """
    Inicia uma nova sessão. Levanta ActiveSessionExists se já houver uma.
    """
    existing = StudySession.get_active_for_user(user)
    if existing:
        raise ActiveSessionExists(existing)

    session = StudySession.objects.create(
        user=user,
        topic=topic,
        start_time=timezone.now(),
        status=StudySession.STATUS_RUNNING,
    )
    logger.info('Sessão iniciada: id=%s user=%s topic=%s', session.id, user.id, getattr(topic, 'id', None))
    return session


@transaction.atomic
def pause_session(user):
    """Pausa a sessão ativa. Idempotente: se já estiver pausada, devolve a mesma."""
    session = StudySession.get_active_for_user(user)
    if not session:
        raise NoActiveSession()

    if session.status == StudySession.STATUS_PAUSED:
        return session

    session.status = StudySession.STATUS_PAUSED
    session.paused_at = timezone.now()
    session.save()
    logger.info('Sessão pausada: id=%s', session.id)
    return session


@transaction.atomic
def resume_session(user):
    """Retoma a sessão pausada. Idempotente: se já estiver rodando, devolve a mesma."""
    session = StudySession.get_active_for_user(user)
    if not session:
        raise NoActiveSession()

    if session.status == StudySession.STATUS_RUNNING:
        return session

    # Acumula tempo pausado
    if session.paused_at:
        delta = (timezone.now() - session.paused_at).total_seconds()
        session.total_paused_seconds = int(session.total_paused_seconds) + int(delta)

    session.status = StudySession.STATUS_RUNNING
    session.paused_at = None
    session.save()
    logger.info('Sessão retomada: id=%s', session.id)
    return session


@transaction.atomic
def finish_session(user):
    """
    Finaliza a sessão ativa.

    - Calcula a duração REAL no servidor (ignora qualquer valor do cliente).
    - Atualiza DailyProgress do dia.
    - Retorna a sessão finalizada.
    """
    session = StudySession.get_active_for_user(user)
    if not session:
        raise NoActiveSession()

    now = timezone.now()

    # Se estava pausada, fechar a pausa atual antes de calcular
    if session.status == StudySession.STATUS_PAUSED and session.paused_at:
        delta = (now - session.paused_at).total_seconds()
        session.total_paused_seconds = int(session.total_paused_seconds) + int(delta)
        session.paused_at = None

    session.end_time = now
    session.status = StudySession.STATUS_FINISHED

    # Cálculo server-side
    real_seconds = session.elapsed_seconds
    session.duration_minutes = real_seconds // 60

    session.save()

    # Atualizar progresso diário (se pelo menos 1 minuto registrado)
    if session.duration_minutes >= 1:
        _add_to_daily_progress(user, session.duration_minutes)

    logger.info(
        'Sessão finalizada: id=%s duracao=%s min (reais=%ss)',
        session.id, session.duration_minutes, real_seconds,
    )
    return session


def _add_to_daily_progress(user, minutes):
    """Incrementa horas estudadas do dia de forma atômica."""
    today = timezone.now().date()
    hours = Decimal(minutes) / Decimal('60')

    progress, _ = DailyProgress.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            'hours_studied': Decimal('0'),
            'questions_solved': 0,
            'correct_answers': 0,
            'flashcards_reviewed': 0,
        },
    )
    DailyProgress.objects.filter(pk=progress.pk).update(
        hours_studied=F('hours_studied') + hours,
    )
