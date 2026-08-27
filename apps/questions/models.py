from django.db import models
from django.conf import settings
from apps.subjects.models import Topic

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
    enunciado = models.TextField(verbose_name="Enunciado")
    alternativa_a = models.CharField(max_length=500, verbose_name="Alternativa A", default='')
    alternativa_b = models.CharField(max_length=500, verbose_name="Alternativa B", default='')
    alternativa_c = models.CharField(max_length=500, verbose_name="Alternativa C", default='')
    alternativa_d = models.CharField(max_length=500, verbose_name="Alternativa D", default='')
    alternativa_correta = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')], verbose_name="Alternativa Correta")
    explicacao = models.TextField(blank=True, verbose_name="Explicação")
    dificuldade = models.PositiveSmallIntegerField(choices=DIFFICULTY_CHOICES, default=3, verbose_name="Dificuldade")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Questão"
        verbose_name_plural = "Questões"
        ordering = ['-created_at']

    def __str__(self):
        return self.enunciado[:50]

    def get_alternativas_dict(self):
        return {
            'a': self.alternativa_a,
            'b': self.alternativa_b,
            'c': self.alternativa_c,
            'd': self.alternativa_d,
        }

    def get_correta_letra(self):
        """Retorna a letra da alternativa correta (a, b, c, d)"""
        return self.alternativa_correta

    def get_correta_texto(self):
        """Retorna o texto da alternativa correta"""
        alternativas = {
            'a': self.alternativa_a,
            'b': self.alternativa_b,
            'c': self.alternativa_c,
            'd': self.alternativa_d,
        }
        return alternativas.get(self.alternativa_correta, '')
