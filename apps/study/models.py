from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.subjects.models import Topic


class StudySession(models.Model):
    """
    Sessão de estudo — fonte da verdade do cronômetro.

    Regras:
    - No máximo UMA sessão ativa por usuário (RUNNING ou PAUSED).
    - A duração NUNCA deve ser enviada pelo cliente; é calculada aqui.
    - A pausa acumula em `total_paused_seconds` e o tempo "vivo" sempre
      desconta esse valor.
    """

    STATUS_RUNNING = 'RUNNING'
    STATUS_PAUSED = 'PAUSED'
    STATUS_FINISHED = 'FINISHED'
    STATUS_CHOICES = [
        (STATUS_RUNNING, 'Em andamento'),
        (STATUS_PAUSED, 'Pausada'),
        (STATUS_FINISHED, 'Finalizada'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_sessions',
        verbose_name="Usuário",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        verbose_name="Tópico",
    )

    start_time = models.DateTimeField(verbose_name="Início")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Fim")
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name="Duração (min)")
    notes = models.TextField(blank=True, verbose_name="Observações")

    # === Novos campos — cronômetro global ===
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_RUNNING,
        db_index=True,
        verbose_name="Status",
    )
    paused_at = models.DateTimeField(null=True, blank=True, verbose_name="Pausada em")
    total_paused_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="Segundos pausados (acumulado)",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Sessão de estudo"
        verbose_name_plural = "Sessões de estudo"
        ordering = ['-start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(status__in=['RUNNING', 'PAUSED']),
                name='unique_active_session_per_user',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', '-start_time']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')} [{self.status}]"

    # ---------------------------------------------------------------
    # PROPERTIES
    # ---------------------------------------------------------------
    @property
    def is_active(self):
        return self.status in (self.STATUS_RUNNING, self.STATUS_PAUSED)

    @property
    def elapsed_seconds(self):
        """
        Segundos de estudo REAIS, já descontando pausas.

        - RUNNING: tempo desde start_time - pausas acumuladas
        - PAUSED: tempo até paused_at - pausas acumuladas
        - FINISHED: tempo até end_time - pausas acumuladas
        """
        if not self.start_time:
            return 0

        if self.status == self.STATUS_FINISHED and self.end_time:
            ref = self.end_time
        elif self.status == self.STATUS_PAUSED and self.paused_at:
            ref = self.paused_at
        else:
            ref = timezone.now()

        total = (ref - self.start_time).total_seconds()
        return max(0, int(total) - int(self.total_paused_seconds))

    @property
    def elapsed_minutes(self):
        return self.elapsed_seconds // 60

    # ---------------------------------------------------------------
    # CLASSMETHODS
    # ---------------------------------------------------------------
    @classmethod
    def get_active_for_user(cls, user):
        return cls.objects.filter(
            user=user,
            status__in=[cls.STATUS_RUNNING, cls.STATUS_PAUSED],
        ).first()


class DailyProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_progress',
        verbose_name="Usuário",
    )
    date = models.DateField(verbose_name="Data")
    hours_studied = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Horas estudadas")
    questions_solved = models.PositiveIntegerField(default=0, verbose_name="Questões resolvidas")
    correct_answers = models.PositiveIntegerField(default=0, verbose_name="Acertos")
    flashcards_reviewed = models.PositiveIntegerField(default=0, verbose_name="Flashcards revisados")
    notes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        unique_together = ['user', 'date']
        verbose_name = "Progresso diário"
        verbose_name_plural = "Progressos diários"

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals',
        verbose_name="Usuário",
    )
    PERIOD_CHOICES = [('daily', 'Diária'), ('weekly', 'Semanal'), ('monthly', 'Mensal')]
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='daily', verbose_name="Período")
    target_hours = models.DecimalField(max_digits=5, decimal_places=2, default=3.0, verbose_name="Meta horas")
    target_questions = models.PositiveIntegerField(default=30, verbose_name="Meta questões")
    target_flashcards = models.PositiveIntegerField(default=20, verbose_name="Meta flashcards")
    start_date = models.DateField(auto_now_add=True, verbose_name="Data de início")
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Meta"
        verbose_name_plural = "Metas"

    def __str__(self):
        return f"{self.user.username} - {self.period}"


class StudyContent(models.Model):
    """Conteúdo de estudo para revisão espaçada."""

    DIFFICULTY_CHOICES = [
        (1, 'Muito fácil'),
        (2, 'Fácil'),
        (3, 'Médio'),
        (4, 'Difícil'),
        (5, 'Muito difícil'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_contents',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='study_contents',
    )
    difficulty = models.PositiveSmallIntegerField(choices=DIFFICULTY_CHOICES, default=3)
    studied_at = models.DateTimeField(auto_now_add=True)
    next_review = models.DateField(null=True, blank=True)
    review_count = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conteúdo de estudo"
        verbose_name_plural = "Conteúdos de estudo"
        ordering = ['next_review']

    def __str__(self):
        return f"{self.topic.name} - {self.get_difficulty_display()}"

    def schedule_next_review(self):
        """Calcula a próxima data de revisão baseada na contagem de revisões e dificuldade."""
        intervals = {
            1: [1, 3, 7, 14, 30],
            2: [1, 3, 7, 14, 30],
            3: [1, 3, 7, 14, 30],
            4: [1, 2, 5, 10, 20],
            5: [1, 2, 5, 10, 20],
        }
        idx = min(self.review_count, 4)
        days = intervals.get(self.difficulty, [1, 3, 7, 14, 30])[idx]
        self.next_review = timezone.now().date() + timedelta(days=days)
        self.review_count += 1
        self.save()
