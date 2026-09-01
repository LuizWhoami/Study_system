from django.db import models
from django.conf import settings
from apps.subjects.models import Topic
from apps.contests.models import Contest

class Question(models.Model):
    DIFFICULTY_CHOICES = [
        (1, 'Muito fácil'),
        (2, 'Fácil'),
        (3, 'Médio'),
        (4, 'Difícil'),
        (5, 'Muito difícil'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions', verbose_name="Usuário")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions', verbose_name="Assunto")
    contest = models.ForeignKey(Contest, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Concurso/Estudo")
    enunciado = models.TextField(verbose_name="Enunciado")
    alternativa_a = models.CharField(max_length=500, verbose_name="Alternativa A", default='')
    alternativa_b = models.CharField(max_length=500, verbose_name="Alternativa B", default='')
    alternativa_c = models.CharField(max_length=500, verbose_name="Alternativa C", default='')
    alternativa_d = models.CharField(max_length=500, verbose_name="Alternativa D", default='')
    alternativa_correta = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')], verbose_name="Alternativa Correta")
    explicacao = models.TextField(blank=True, verbose_name="Explicação")
    dificuldade = models.PositiveSmallIntegerField(choices=DIFFICULTY_CHOICES, default=3, verbose_name="Dificuldade")
    # Novos campos
    banca = models.CharField(max_length=100, blank=True, verbose_name="Banca")
    ano = models.PositiveIntegerField(null=True, blank=True, verbose_name="Ano")
    fonte = models.CharField(max_length=200, blank=True, verbose_name="Fonte")
    status = models.BooleanField(default=True, verbose_name="Ativa")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Questão"
        verbose_name_plural = "Questões"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['topic', 'dificuldade']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['banca', 'ano']),
        ]

    def __str__(self):
        return self.enunciado[:50]

    def get_alternativas_dict(self):
        return {
            'a': self.alternativa_a,
            'b': self.alternativa_b,
            'c': self.alternativa_c,
            'd': self.alternativa_d,
        }

# ============================
# MODELOS DE HISTÓRICO, REVISÃO, ERROS E SIMULADOS
# ============================

class QuestionAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    resposta_escolhida = models.CharField(max_length=1)
    correta = models.BooleanField()
    data = models.DateTimeField(auto_now_add=True)
    tempo_gasto = models.PositiveIntegerField(help_text="Tempo em segundos", default=0)
    modo = models.CharField(max_length=20, choices=[('treino', 'Treino'), ('simulado', 'Simulado')], default='treino')
    contest = models.ForeignKey(Contest, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-data']
        indexes = [
            models.Index(fields=['user', 'question']),
            models.Index(fields=['user', 'correta']),
            models.Index(fields=['user', 'data']),
        ]

class QuestionReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    proxima_revisao = models.DateField()
    intervalo = models.PositiveIntegerField(default=1)
    vezes_revisado = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'proxima_revisao']),
        ]

class ErrorLog(models.Model):
    REASON_CHOICES = [
        ('desconhecido', 'Não conhecia o conteúdo'),
        ('esqueci', 'Esqueci'),
        ('confundi', 'Confundi conceitos'),
        ('interpretacao', 'Errei por interpretação'),
        ('desatencao', 'Desatenção'),
        ('chute', 'Chutei'),
        ('outro', 'Outro'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    motivo = models.CharField(max_length=20, choices=REASON_CHOICES, default='desconhecido')
    data = models.DateTimeField(auto_now_add=True)
    erro_consecutivo = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['-data']
        indexes = [
            models.Index(fields=['user', 'question']),
        ]

class Simulated(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('in_progress', 'Em andamento'),
        ('finished', 'Finalizado'),
        ('cancelled', 'Cancelado'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.SET_NULL, null=True, blank=True)
    titulo = models.CharField(max_length=200, blank=True)
    quantidade = models.PositiveIntegerField()
    tempo_limite = models.PositiveIntegerField(help_text="Tempo em minutos")
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_inicio']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

class SimulatedQuestion(models.Model):
    simulated = models.ForeignKey(Simulated, on_delete=models.CASCADE, related_name='questoes')
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField()
    resposta_escolhida = models.CharField(max_length=1, blank=True, null=True)
    correta = models.BooleanField(null=True, blank=True)
    tempo_gasto = models.PositiveIntegerField(default=0)
    marcada = models.BooleanField(default=False)

    class Meta:
        ordering = ['ordem']
        unique_together = ['simulated', 'question']

class QuestionAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    resposta_escolhida = models.CharField(max_length=1)
    correta = models.BooleanField()
    data = models.DateTimeField(auto_now_add=True)
    tempo_gasto = models.PositiveIntegerField(help_text="Tempo em segundos", default=0)
    modo = models.CharField(max_length=20, choices=[('treino', 'Treino'), ('simulado', 'Simulado')], default='treino')
    contest = models.ForeignKey('contests.Contest', on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey('subjects.Topic', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-data']
        indexes = [
            models.Index(fields=['user', 'question']),
            models.Index(fields=['user', 'correta']),
            models.Index(fields=['user', 'data']),
        ]

class QuestionReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    proxima_revisao = models.DateField()
    intervalo = models.PositiveIntegerField(default=1)
    vezes_revisado = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'proxima_revisao']),
        ]

class ErrorLog(models.Model):
    REASON_CHOICES = [
        ('desconhecido', 'Não conhecia o conteúdo'),
        ('esqueci', 'Esqueci'),
        ('confundi', 'Confundi conceitos'),
        ('interpretacao', 'Errei por interpretação'),
        ('desatencao', 'Desatenção'),
        ('chute', 'Chutei'),
        ('outro', 'Outro'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    motivo = models.CharField(max_length=20, choices=REASON_CHOICES, default='desconhecido')
    data = models.DateTimeField(auto_now_add=True)
    erro_consecutivo = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['-data']
        indexes = [
            models.Index(fields=['user', 'question']),
        ]

class Simulated(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('in_progress', 'Em andamento'),
        ('finished', 'Finalizado'),
        ('cancelled', 'Cancelado'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contest = models.ForeignKey('contests.Contest', on_delete=models.SET_NULL, null=True, blank=True)
    titulo = models.CharField(max_length=200, blank=True)
    quantidade = models.PositiveIntegerField()
    tempo_limite = models.PositiveIntegerField(help_text="Tempo em minutos")
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_inicio']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

class SimulatedQuestion(models.Model):
    simulated = models.ForeignKey(Simulated, on_delete=models.CASCADE, related_name='questoes')
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField()
    resposta_escolhida = models.CharField(max_length=1, blank=True, null=True)
    correta = models.BooleanField(null=True, blank=True)
    tempo_gasto = models.PositiveIntegerField(default=0)
    marcada = models.BooleanField(default=False)

    class Meta:
        ordering = ['ordem']
        unique_together = ['simulated', 'question']
