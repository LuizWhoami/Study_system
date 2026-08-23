from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.contests.models import Contest

class StudyConfig(models.Model):
    """Configuração principal do plano de estudos."""
    
    # Objetivo
    OBJECTIVE_CHOICES = [
        ('concurso', 'Preparação para concurso'),
        ('vestibular', 'Preparação para vestibular'),
        ('faculdade', 'Faculdade'),
        ('certificacao', 'Certificação'),
        ('habilidade', 'Aprender uma nova habilidade'),
        ('prova_especifica', 'Estudar para uma prova específica'),
        ('rotina', 'Criar uma rotina geral de estudos'),
        ('outro', 'Outro'),
    ]
    
    LEVEL_CHOICES = [
        ('iniciante', 'Iniciante'),
        ('intermediario', 'Intermediário'),
        ('avancado', 'Avançado'),
    ]
    
    PRIORITY_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_config')
    
    # Etapa 1: Objetivo
    objective = models.CharField(max_length=20, choices=OBJECTIVE_CHOICES, default='concurso')
    objective_custom = models.CharField(max_length=200, blank=True)
    level = models.CharField(max_length=15, choices=LEVEL_CHOICES, default='intermediario')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='alta')
    
    # Etapa 2: Matérias (Many-to-Many com Contest)
    selected_contests = models.ManyToManyField(Contest, related_name='study_configs', blank=True)
    max_subjects = models.PositiveSmallIntegerField(default=3, verbose_name="Quantidade de matérias")
    
    # Etapa 3: Disponibilidade
    available_days = models.JSONField(default=list)  # ['mon', 'tue', ...]
    available_hours_start = models.TimeField(default='19:00')
    available_hours_end = models.TimeField(default='22:00')
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=3.0)
    days_per_week = models.PositiveSmallIntegerField(default=5)
    study_weekend = models.BooleanField(default=False)
    
    # Etapa 4: Metas
    target_hours_week = models.DecimalField(max_digits=5, decimal_places=2, default=15.0)
    target_hours_month = models.DecimalField(max_digits=6, decimal_places=2, default=60.0)
    sessions_per_week = models.PositiveSmallIntegerField(default=5)
    daily_goal_hours = models.DecimalField(max_digits=4, decimal_places=2, default=2.0)
    
    # Etapa 5: Método de estudo
    active_recall = models.BooleanField(default=True, verbose_name="Recuperação ativa")
    spaced_repetition = models.BooleanField(default=True, verbose_name="Repetição espaçada")
    practice_questions = models.BooleanField(default=True, verbose_name="Prática com questões")
    flashcards_active = models.BooleanField(default=True, verbose_name="Flashcards")
    interleaving = models.BooleanField(default=True, verbose_name="Intercalação")
    active_review = models.BooleanField(default=True, verbose_name="Revisão ativa")
    
    # Etapa 6: Revisões
    review_intervals = models.JSONField(default=[1, 3, 7, 14, 30])
    review_intensity = models.PositiveSmallIntegerField(default=3, choices=[
        (1, 'Leve (menos revisões)'),
        (2, 'Moderado'),
        (3, 'Intenso (mais revisões)'),
    ])
    
    # Configuração ativa
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração de Estudos"
        verbose_name_plural = "Configurações de Estudos"
    
    def __str__(self):
        return f"Configuração de {self.user.username}"

class PlannedSession(models.Model):
    """Sessões planejadas automaticamente com base na configuração."""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='planned_sessions')
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='planned_sessions')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    subject_name = models.CharField(max_length=200)
    session_type = models.CharField(max_length=20, choices=[
        ('study', 'Estudo'),
        ('review', 'Revisão'),
        ('questions', 'Questões'),
        ('flashcards', 'Flashcards'),
        ('rest', 'Descanso'),
    ])
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = "Sessão Planejada"
        verbose_name_plural = "Sessões Planejadas"
    
    def __str__(self):
        return f"{self.date} - {self.subject_name} ({self.duration_minutes}min)"
