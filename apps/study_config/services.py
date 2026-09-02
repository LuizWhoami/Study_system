from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
from apps.learning.services import LearningEngine
from apps.study_config.models import StudyConfig, PlannedSession
from apps.subjects.models import Topic
from apps.contests.models import Contest
import random
import logging

logger = logging.getLogger(__name__)

class PlanningService:
    """
    Serviço de planejamento adaptativo.
    Integra Learning Engine, configuração e geração de plano.
    """

    def __init__(self, user):
        self.user = user
        self.config = StudyConfig.objects.filter(user=user, is_active=True).first()
        self.engine = LearningEngine(user)

    def generate_initial_plan(self):
        """Gera o plano inicial com base na configuração e no Learning Engine."""
        if not self.config:
            logger.error(f"Usuário {self.user} não tem configuração ativa.")
            return None

        contests = self.config.selected_contests.all()
        if not contests:
            logger.warning("Nenhuma matéria selecionada.")
            return None

        all_topics = Topic.objects.filter(subject__contest__in=contests)
        weak_topics = self.engine.identify_weak_topics(limit=10)

        strategy = self._generate_strategy(contests, weak_topics)

        sessions = self._generate_sessions(strategy, contests)

        self.config.strategy = strategy
        self.config.save()

        for session_data in sessions:
            PlannedSession.objects.create(
                user=self.user,
                contest=session_data['contest'],
                topic=session_data['topic'],
                date=session_data['date'],
                start_time=session_data['start_time'],
                end_time=session_data['end_time'],
                duration_minutes=session_data['duration_minutes'],
                session_type=session_data['session_type'],
                priority=session_data['priority'],
                reason=session_data['reason'],
                origin='system',
                status='planned'
            )

        return sessions

    def _generate_strategy(self, contests, weak_topics):
        strategy = {
            'focus': [],
            'allocation': {
                'study': 30,
                'questions': 35,
                'review': 20,
                'flashcards': 10,
                'simulated': 5,
            },
            'reasoning': []
        }

        for wt in weak_topics[:3]:
            strategy['focus'].append({
                'topic': wt['topic'].name,
                'subject': wt['topic'].subject.name,
                'mastery': wt['mastery'],
                'priority': wt['priority'],
                'reason': f"Domínio de {wt['mastery']}% – abaixo da média."
            })
            strategy['reasoning'].append(f"Aumentar atenção em {wt['topic'].name} (domínio: {wt['mastery']}%)")

        if not strategy['focus']:
            for contest in contests:
                strategy['focus'].append({
                    'topic': None,
                    'subject': contest.name,
                    'mastery': 'N/A',
                    'priority': 50,
                    'reason': 'Nova matéria'
                })

        if contests.exists():
            exam_date = contests.first().exam_date
            if exam_date:
                days_until = (exam_date - timezone.now().date()).days
                if days_until <= 30:
                    strategy['allocation']['questions'] = 50
                    strategy['allocation']['simulated'] = 15
                    strategy['allocation']['study'] = 20
                    strategy['reasoning'].append("Prova próxima – aumentando questões e simulados.")

        return strategy

    def _generate_sessions(self, strategy, contests):
        sessions = []
        today = timezone.now().date()
        weeks = 4
        days_to_plan = weeks * 7

        availability = self.config.availability or self._legacy_availability()
        if not availability:
            logger.warning("Nenhuma disponibilidade configurada.")
            return []

        for day_offset in range(days_to_plan):
            current_date = today + timedelta(days=day_offset)
            day_name = current_date.strftime('%a').lower()
            day_blocks = self._get_blocks_for_day(availability, day_name)
            if not day_blocks:
                continue

            topic = self._select_topic_for_day(contests, strategy, day_offset)

            for block in day_blocks:
                start = datetime.strptime(block['start'], '%H:%M').time()
                end = datetime.strptime(block['end'], '%H:%M').time()
                duration = (datetime.combine(today, end) - datetime.combine(today, start)).seconds // 60

                session_type = self._select_session_type(strategy['allocation'])

                if topic:
                    contest = topic.subject.contest
                    topic_obj = topic
                else:
                    contest = random.choice(contests)
                    topic_obj = None

                sessions.append({
                    'contest': contest,
                    'topic': topic_obj,
                    'date': current_date,
                    'start_time': start,
                    'end_time': end,
                    'duration_minutes': duration,
                    'session_type': session_type,
                    'priority': 50,
                    'reason': f"Planejado pelo sistema (estratégia: {strategy['reasoning'][0] if strategy['reasoning'] else 'Distribuição equilibrada'})",
                })

        for s in sessions:
            if s['topic']:
                priority = self.engine.calculate_topic_priority(s['topic'], s['contest'])
                s['priority'] = priority
            else:
                s['priority'] = 50

        return sessions

    def _legacy_availability(self):
        if not self.config.available_days:
            return []
        availability = []
        for day in self.config.available_days:
            start_hour = 19
            end_hour = 22
            hours = float(self.config.hours_per_day or 3.0)
            availability.append({
                'day': day,
                'periods': [{'start': f"{start_hour:02d}:00", 'end': f"{start_hour + int(hours):02d}:00"}]
            })
        return availability

    def _get_blocks_for_day(self, availability, day_name):
        for entry in availability:
            if entry.get('day') == day_name:
                return entry.get('periods', [])
        return []

    def _select_topic_for_day(self, contests, strategy, day_offset):
        weak_topics = [item['topic'] for item in strategy['focus'] if item.get('topic')]
        if weak_topics:
            topic = random.choice(weak_topics)
            return topic

        topics = Topic.objects.filter(subject__contest__in=contests)
        if topics.exists():
            return random.choice(topics)
        return None

    def _select_session_type(self, allocation):
        types = []
        weights = []
        for t, w in allocation.items():
            types.append(t)
            weights.append(w)
        return random.choices(types, weights=weights, k=1)[0]

    def recalculate_plan(self):
        future_sessions = PlannedSession.objects.filter(
            user=self.user,
            date__gte=timezone.now().date(),
            status__in=['planned', 'in_progress']
        ).order_by('date', 'start_time')

        next_activity = self.engine.recommend_next_activity()

        for session in future_sessions:
            if session.topic:
                priority = self.engine.calculate_topic_priority(session.topic, session.contest)
                session.priority = priority
                if priority > 70:
                    session.reason = f"Prioridade alta: baixo domínio ({priority}%)"
                elif priority < 30:
                    session.reason = f"Prioridade baixa: domínio consolidado ({priority}%)"
                else:
                    session.reason = "Manutenção"
                session.save()

        if next_activity:
            today = timezone.now().date()
            existing = PlannedSession.objects.filter(
                user=self.user,
                date=today,
                topic=next_activity['topic'],
                status='planned'
            ).exists()
            if not existing:
                availability = self.config.availability or self._legacy_availability()
                today_name = today.strftime('%a').lower()
                blocks = self._get_blocks_for_day(availability, today_name)
                if blocks:
                    block = blocks[0]
                    start = datetime.strptime(block['start'], '%H:%M').time()
                    end = datetime.strptime(block['end'], '%H:%M').time()
                    duration = (datetime.combine(today, end) - datetime.combine(today, start)).seconds // 60
                    PlannedSession.objects.create(
                        user=self.user,
                        contest=next_activity['topic'].subject.contest,
                        topic=next_activity['topic'],
                        date=today,
                        start_time=start,
                        end_time=end,
                        duration_minutes=min(duration, 30),
                        session_type='study',
                        priority=80,
                        reason=next_activity['reason'],
                        origin='learning_engine',
                        status='planned'
                    )

        return {"updated": future_sessions.count(), "created": 1 if next_activity else 0}
