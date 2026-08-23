from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.subjects.models import Topic

class StudySession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions', verbose_name="Usuário")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions', verbose_name="Tópico")
    start_time = models.DateTimeField(verbose_name="Início")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Fim")
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name="Duração (min)")
    notes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Sessão de estudo"
        verbose_name_plural = "Sessões de estudo"

    def __str__(self):
        return f"{self.user.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

class DailyProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_progress', verbose_name="Usuário")
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals', verbose_name="Usuário")
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

# NOVO MODELO: Conteúdo de estudo para revisão espaçada
class StudyContent(models.Model):
    DIFFICULTY_CHOICES = [
        (1, 'Muito fácil'),
        (2, 'Fácil'),
        (3, 'Médio'),
        (4, 'Difícil'),
        (5, 'Muito difícil'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_contents')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='study_contents')
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
