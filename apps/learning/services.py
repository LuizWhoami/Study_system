from django.db.models import Avg, Count, Q, Sum, F, Value, Case, When, FloatField, DecimalField, Max
from django.db.models.functions import Coalesce, Now
from django.utils import timezone
from datetime import timedelta, date
import math
from apps.questions.models import Question, QuestionAttempt, ErrorLog, QuestionReview
from apps.flashcards.models import Flashcard
from apps.study.models import StudySession, StudyContent, DailyProgress
from apps.subjects.models import Topic
from apps.contests.models import Contest
from decimal import Decimal

class LearningEngine:
    """
    Motor Inteligente de Aprendizagem.
    Calcula domínio (mastery), prioridade e recomendações usando regras determinísticas.
    """

    def __init__(self, user):
        self.user = user

    # ============================================================
    # MASTERY SCORE (0-100)
    # ============================================================
    def calculate_topic_mastery(self, topic):
        """
        Calcula o domínio de um tópico baseado em:
        - Questões (acertos, erros, dificuldade) -> 35%
        - Recência das atividades -> 15%
        - Revisões (flashcards/studycontent) -> 20%
        - Tempo de estudo -> 15%
        - Erros consecutivos -> 15% (penalidade)
        """
        user = self.user
        # 1. Questões
        attempts = QuestionAttempt.objects.filter(
            user=user,
            question__topic=topic
        )
        total = attempts.count()
        if total > 0:
            correct = attempts.filter(correta=True).count()
            acc = correct / total
            # peso por dificuldade (questões difíceis têm mais peso)
            avg_difficulty = attempts.aggregate(avg=Avg('question__dificuldade'))['avg'] or 3
            question_score = acc * 100 * (0.8 + 0.2 * (avg_difficulty / 5))
        else:
            question_score = 0

        # 2. Recência (última tentativa)
        last_attempt = attempts.order_by('-data').first()
        if last_attempt:
            days_since = (timezone.now() - last_attempt.data).days
            recency_score = max(0, 100 - days_since * 2)  # 100 se hoje, cai 2 por dia
        else:
            recency_score = 0

        # 3. Revisões (StudyContent e Flashcards)
        study_contents = StudyContent.objects.filter(user=user, topic=topic)
        flash_reviews = Flashcard.objects.filter(user=user, topic=topic)

        review_count = study_contents.count() + flash_reviews.count()
        if review_count > 0:
            # média de revisões por tópico (considerando número de revisões)
            review_score = min(100, review_count * 10)
        else:
            review_score = 0

        # 4. Tempo de estudo (sessões)
        sessions = StudySession.objects.filter(user=user, topic=topic)
        total_minutes = sessions.aggregate(total=Sum('duration_minutes'))['total'] or 0
        if total_minutes > 0:
            time_score = min(100, total_minutes / 60 * 10)  # 10% por hora, máximo 100
        else:
            time_score = 0

        # 5. Erros consecutivos (penalidade)
        error_logs = ErrorLog.objects.filter(user=user, question__topic=topic).order_by('-data')
        if error_logs.exists():
            consecutive_errors = error_logs.first().erro_consecutivo or 1
            penalty = min(30, consecutive_errors * 5)  # até 30 de penalidade
        else:
            penalty = 0

        # Cálculo final com pesos
        mastery = (
            question_score * 0.35 +
            recency_score * 0.15 +
            review_score * 0.20 +
            time_score * 0.15
        ) * (1 - penalty / 100)

        mastery = max(0, min(100, mastery))
        return round(mastery, 2)

    # ============================================================
    # PRIORITY SCORE (0-100)
    # ============================================================
    def calculate_topic_priority(self, topic, contest=None):
        """
        Prioridade é alta para:
        - Mastery baixo (fraqueza)
        - Revisão vencida
        - Muitos erros
        - Pouco estudo recente
        - Proximidade da prova (se contest fornecido)
        """
        mastery = self.calculate_topic_mastery(topic)
        priority = 0

        # 1. Fraqueza (quanto menor mastery, maior prioridade)
        weakness = 100 - mastery
        priority += weakness * 0.4

        # 2. Erros consecutivos (corrigido)
        error_logs = ErrorLog.objects.filter(user=self.user, question__topic=topic)
        top_error = error_logs.order_by('-erro_consecutivo').first()
        consecutive_errors = top_error.erro_consecutivo if top_error else 0
        priority += consecutive_errors * 2  # até 20

        # 3. Última atividade (estudo, questão, revisão)
        last_session = StudySession.objects.filter(user=self.user, topic=topic).order_by('-start_time').first()
        last_attempt = QuestionAttempt.objects.filter(user=self.user, question__topic=topic).order_by('-data').first()
        last_review = StudyContent.objects.filter(user=self.user, topic=topic).order_by('-next_review').first()
        # Última atividade recente?
        last_activity = None
        if last_session:
            last_activity = last_session.start_time
        elif last_attempt:
            last_activity = last_attempt.data
        elif last_review:
            last_activity = last_review.updated_at
        if last_activity:
            days_since = (timezone.now() - last_activity).days
            if days_since > 7:
                priority += min(20, days_since)  # até 20

        # 4. Revisão vencida (StudyContent)
        overdue_review = StudyContent.objects.filter(user=self.user, topic=topic, next_review__lt=timezone.now().date()).exists()
        if overdue_review:
            priority += 15

        # 5. Proximidade da prova (se contest fornecido e tiver exam_date)
        if contest and contest.exam_date:
            days_until = (contest.exam_date - timezone.now().date()).days
            if days_until <= 30:
                priority += max(0, (30 - days_until) * 0.5)  # até 15

        priority = min(100, priority)
        return round(priority, 2)

    # ============================================================
    # IDENTIFICAR PONTOS FRACOS
    # ============================================================
    def identify_weak_topics(self, contest=None, limit=5):
        """
        Retorna os tópicos com menor Mastery, excluindo os que já foram estudados recentemente.
        """
        topics = Topic.objects.filter(subject__contest__user=self.user)
        if contest:
            topics = topics.filter(subject__contest=contest)

        weak_topics = []
        for topic in topics:
            mastery = self.calculate_topic_mastery(topic)
            # Exclui tópicos com domínio alto (>70)
            if mastery < 70:
                weak_topics.append({
                    'topic': topic,
                    'mastery': mastery,
                    'priority': self.calculate_topic_priority(topic, contest)
                })

        # Ordena por menor mastery (maior prioridade)
        weak_topics.sort(key=lambda x: x['mastery'])
        return weak_topics[:limit]

    # ============================================================
    # RECOMENDAR PRÓXIMA ATIVIDADE
    # ============================================================
    def recommend_next_activity(self, contest=None):
        """
        Retorna a atividade mais prioritária com base em:
        - Tópicos fracos
        - Revisões vencidas
        - Erros recentes
        """
        # 1. Encontrar tópicos com revisão vencida (StudyContent)
        overdue_contents = StudyContent.objects.filter(
            user=self.user,
            next_review__lt=timezone.now().date()
        ).select_related('topic')
        if overdue_contents.exists():
            # Priorizar o mais atrasado
            content = overdue_contents.order_by('next_review').first()
            topic = content.topic
            return {
                'type': 'review',
                'topic': topic,
                'reason': f'Revisão vencida há {(timezone.now().date() - content.next_review).days} dias.',
                'estimated_time': 15,  # minutos
                'questions_count': 5,
            }

        # 2. Tópicos com muitos erros consecutivos
        error_logs = ErrorLog.objects.filter(user=self.user).order_by('-erro_consecutivo')
        if error_logs.exists():
            top_error = error_logs.first()
            if top_error.erro_consecutivo >= 2:
                topic = top_error.question.topic
                return {
                    'type': 'questions',
                    'topic': topic,
                    'reason': f'{top_error.erro_consecutivo} erros consecutivos neste tópico.',
                    'estimated_time': 20,
                    'questions_count': 10,
                }

        # 3. Tópicos fracos (Mastery < 50)
        weak_topics = self.identify_weak_topics(contest, limit=1)
        if weak_topics:
            weak = weak_topics[0]
            topic = weak['topic']
            return {
                'type': 'study',
                'topic': topic,
                'reason': f'Domínio de {weak["mastery"]}% – abaixo da média.',
                'estimated_time': 25,
                'questions_count': 8,
            }

        # 4. Se nada, sugerir estudo de qualquer tópico não visto
        topics = Topic.objects.filter(subject__contest__user=self.user)
        if contest:
            topics = topics.filter(subject__contest=contest)
        for topic in topics:
            if not QuestionAttempt.objects.filter(user=self.user, question__topic=topic).exists():
                return {
                    'type': 'study',
                    'topic': topic,
                    'reason': 'Este tópico ainda não foi estudado.',
                    'estimated_time': 30,
                    'questions_count': 5,
                }

        # 5. Fallback: qualquer tópico
        if topics.exists():
            topic = topics.first()
            return {
                'type': 'study',
                'topic': topic,
                'reason': 'Explore novos conteúdos.',
                'estimated_time': 20,
                'questions_count': 5,
            }

        return None

    # ============================================================
    # PLANO DO DIA (HOJE)
    # ============================================================
    def get_today_plan(self, contest=None):
        """
        Retorna um resumo do dia com progresso, meta e próximas atividades.
        """
        today = timezone.now().date()
        # Meta diária (do perfil ou configuração)
        from apps.study_config.models import StudyConfig
        config = StudyConfig.objects.filter(user=self.user, is_active=True).first()
        daily_goal_hours = self.user.daily_goal_hours or 3.0

        # Progresso de hoje
        progress_today = DailyProgress.objects.filter(user=self.user, date=today).first()
        hours_done = progress_today.hours_studied if progress_today else Decimal('0')

        # Próxima atividade
        next_activity = self.recommend_next_activity(contest)

        # Pontos fracos
        weak_topics = self.identify_weak_topics(contest, limit=3)

        # Revisões pendentes (questões e flashcards)
        pending_question_reviews = QuestionReview.objects.filter(user=self.user, proxima_revisao__lte=today).count()
        pending_flashcards = Flashcard.objects.filter(user=self.user, proxima_revisao__lte=today).count()

        return {
            'date': today,
            'daily_goal_hours': float(daily_goal_hours),
            'hours_done': float(hours_done),
            'progress_percent': min(100, float(hours_done) / float(daily_goal_hours) * 100),
            'next_activity': next_activity,
            'weak_topics': weak_topics,
            'pending_question_reviews': pending_question_reviews,
            'pending_flashcards': pending_flashcards,
        }
