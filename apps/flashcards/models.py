from django.db import models
from django.conf import settings
from apps.subjects.models import Topic
from datetime import date, timedelta

class Flashcard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flashcards', verbose_name="Usuário")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='flashcards', verbose_name="Tópico")
    pergunta = models.TextField(verbose_name="Pergunta")
    resposta = models.TextField(verbose_name="Resposta")
    nivel = models.PositiveSmallIntegerField(
        choices=[(1, 'Muito fácil'), (2, 'Fácil'), (3, 'Médio'), (4, 'Difícil'), (5, 'Muito difícil')],
        default=3,
        verbose_name="Nível de dificuldade"
    )
    intervalo = models.PositiveIntegerField(default=1, verbose_name="Intervalo (dias)")
    facilidade = models.FloatField(default=2.5, verbose_name="Facilidade")
    proxima_revisao = models.DateField(default=date.today, verbose_name="Próxima revisão")
    vezes_revisado = models.PositiveIntegerField(default=0, verbose_name="Vezes revisado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Flashcard"
        verbose_name_plural = "Flashcards"
        ordering = ['proxima_revisao']

    def __str__(self):
        return self.pergunta[:50]

    def revisar(self, avaliacao):
        fatores = {
            'errei': 0.0,
            'dificil': 0.5,
            'bom': 1.0,
            'facil': 1.3
        }
        fator = fatores.get(avaliacao, 1.0)
        self.facilidade = max(1.3, self.facilidade + (0.1 * fator) - 0.1)
        if avaliacao == 'errei':
            self.intervalo = 1
        else:
            if self.vezes_revisado == 0:
                self.intervalo = 1
            elif self.vezes_revisado == 1:
                self.intervalo = 3
            else:
                self.intervalo = int(self.intervalo * self.facilidade)
        self.vezes_revisado += 1
        self.proxima_revisao = date.today() + timedelta(days=self.intervalo)
        self.save()
