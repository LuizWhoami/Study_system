from django.db import models
from django.conf import settings
from datetime import date

class StudyDay(models.Model):
    ACTIVITY_CHOICES = [
        ('study', '📚 Estudo'),
        ('review', '🔄 Revisão'),
        ('questions', '❓ Questões'),
        ('summary', '📝 Resumo'),
        ('rest', '😴 Descanso'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_days')
    date = models.DateField(verbose_name="Data")
    activity = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, verbose_name="Atividade")
    notes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['date']
        verbose_name = "Dia de estudo"
        verbose_name_plural = "Dias de estudo"

    def __str__(self):
        return f"{self.date} - {self.get_activity_display()}"
