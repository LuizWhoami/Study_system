from django.db import models
from django.conf import settings

class Contest(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planejando'),
        ('studying', 'Estudando'),
        ('review', 'Revisão'),
        ('intensive', 'Intensivo'),
        ('finished', 'Finalizado'),
        ('archived', 'Arquivado'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contests', verbose_name="Usuário")
    name = models.CharField(max_length=200, verbose_name="Nome do Estudo")
    organization = models.CharField(max_length=200, blank=True, verbose_name="Instituição/Curso")
    position = models.CharField(max_length=200, blank=True, verbose_name="Objetivo")
    start_date = models.DateField(blank=True, null=True, verbose_name="Data de Início")
    exam_date = models.DateField(blank=True, null=True, verbose_name="Data da Prova/Meta")
    expected_date = models.DateField(blank=True, null=True, verbose_name="Data Prevista (opcional)")
    board = models.CharField(max_length=100, blank=True, verbose_name="Banca/Instituição")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning', verbose_name="Status")
    notes = models.TextField(blank=True, verbose_name="Observações")
    goal_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Meta de Horas")
    goal_questions = models.IntegerField(default=0, verbose_name="Meta de Questões")
    priority = models.PositiveSmallIntegerField(default=0, verbose_name="Prioridade")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['-priority', 'exam_date']
        unique_together = ['user', 'name']
        verbose_name = "Estudo"
        verbose_name_plural = "Estudos"

    def __str__(self):
        return self.name

    def get_progress(self):
        # Calcula progresso baseado em tópicos concluídos (status 'mastered' ou 'studied')
        total_topics = self.subjects.aggregate(total=models.Count('topics'))['total'] or 0
        if total_topics == 0:
            return 0
        mastered = self.subjects.aggregate(
            mastered=models.Count('topics', filter=models.Q(topics__status='mastered'))
        )['mastered'] or 0
        return int((mastered / total_topics) * 100)
