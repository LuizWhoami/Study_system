from django.db import models
from django.conf import settings
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
