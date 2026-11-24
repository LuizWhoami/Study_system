from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.contests.models import Contest
from apps.subjects.models import Topic

class StudyConfig(models.Model):
    """Configuração principal do plano de estudos (evoluída)."""
    
    # ===== OBJETIVO =====
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
    DIAGNOSTIC_CHOICES = [
        ('nunca', 'Nunca estudei'),
        ('pouca_base', 'Tenho pouca base'),
        ('conheco', 'Conheço o conteúdo'),
        ('boa_base', 'Tenho boa base'),
        ('domino', 'Domino'),
    ]
    INTENSITY_CHOICES = [
        ('leve', 'Leve'),
        ('equilibrada', 'Equilibrada'),
        ('intensa', 'Intensa'),
        ('maxima', 'Máxima'),
    ]
    SESSION_DURATION_CHOICES = [
        (15, '15 min'),
        (25, '25 min'),
        (40, '40 min'),
        (60, '60 min'),
        (90, '90 min'),
    ]
    ADAPTATION_CHOICES = [
        ('manual', 'Manual'),
        ('assistida', 'Assistida'),
        ('automatica', 'Automática'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_config')
    
    # Etapa 1: Objetivo
    objective = models.CharField(max_length=20, choices=OBJECTIVE_CHOICES, default='concurso')
    objective_custom = models.CharField(max_length=200, blank=True)
    level = models.CharField(max_length=15, choices=LEVEL_CHOICES, default='intermediario')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='alta')
    
    # Etapa 2: Matérias
    selected_contests = models.ManyToManyField(Contest, related_name='study_configs', blank=True)
    max_subjects = models.PositiveSmallIntegerField(default=3)
    
    # Etapa 3: Disponibilidade (evoluída para múltiplos períodos por dia)
    availability = models.JSONField(default=list)
    # Mantemos campos antigos para compatibilidade
    available_days = models.JSONField(default=list)
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=3.0)
    days_per_week = models.PositiveSmallIntegerField(default=5)
    study_weekend = models.BooleanField(default=False)
    
    # Etapa 4: Metas (mínima, ideal, desafio)
    min_hours_week = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    target_hours_week = models.DecimalField(max_digits=5, decimal_places=2, default=15.0)
    max_hours_week = models.DecimalField(max_digits=5, decimal_places=2, default=18.0)
    target_hours_month = models.DecimalField(max_digits=6, decimal_places=2, default=60.0)
    sessions_per_week = models.PositiveSmallIntegerField(default=5)
    daily_goal_hours = models.DecimalField(max_digits=4, decimal_places=2, default=2.0)
    target_questions_week = models.PositiveIntegerField(default=30)
    target_flashcards_week = models.PositiveIntegerField(default=20)
    
    # Etapa 5: Preferências
    preferred_methods = models.JSONField(default=list)
    session_duration = models.PositiveSmallIntegerField(choices=SESSION_DURATION_CHOICES, default=40)
    intensity = models.CharField(max_length=20, choices=INTENSITY_CHOICES, default='equilibrada')  # max_length ajustado
    rest_days = models.JSONField(default=list)
    
    # Etapa 6: Diagnóstico (opcional)
    diagnostic_level = models.CharField(max_length=20, choices=DIAGNOSTIC_CHOICES, blank=True)
    diagnostic_date = models.DateTimeField(null=True, blank=True)
    
    # Estratégia (gerada pelo Learning Engine)
    strategy = models.JSONField(default=dict)
    
    # Adaptação
    adaptation_mode = models.CharField(max_length=10, choices=ADAPTATION_CHOICES, default='assistida')
    
    # Estado
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de Estudos"
        verbose_name_plural = "Configurações de Estudos"

    def __str__(self):
        return f"Configuração de {self.user.username}"

class PlannedSession(models.Model):
    """Sessão planejada, com estados e motivos."""
    STATUS_CHOICES = [
        ('planned', 'Planejada'),
        ('in_progress', 'Em andamento'),
        ('completed', 'Concluída'),
        ('skipped', 'Pulada'),
        ('rescheduled', 'Reagendada'),
    ]
    SESSION_TYPE_CHOICES = [
        ('study', 'Estudo'),
        ('review', 'Revisão'),
        ('questions', 'Questões'),
        ('flashcards', 'Flashcards'),
        ('simulated', 'Simulado'),
        ('rest', 'Descanso'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='planned_sessions')
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='planned_sessions')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='planned_sessions', null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='study')
    priority = models.PositiveSmallIntegerField(default=0)
    reason = models.TextField(blank=True)
    origin = models.CharField(max_length=50, default='system')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = "Sessão Planejada"
        verbose_name_plural = "Sessões Planejadas"

    def __str__(self):
        return f"{self.date} - {self.get_session_type_display()} - {self.topic.name if self.topic else self.contest.name}"
