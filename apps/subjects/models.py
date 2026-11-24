from django.db import models
from django.conf import settings
from apps.contests.models import Contest

class Subject(models.Model):
    STATUS_CHOICES = [
        ('not_started', '⚪ Não iniciado'),
        ('studying', '🔵 Estudando'),
        ('studied', '🟡 Estudado'),
        ('review_pending', '🟠 Revisão pendente'),
        ('needs_reinforcement', '🔴 Precisa reforço'),
        ('mastered', '🟢 Dominado'),
    ]
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='subjects', verbose_name="Concurso")
    name = models.CharField(max_length=200, verbose_name="Nome")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name="Status")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['contest', 'name']
        verbose_name = "Matéria"
        verbose_name_plural = "Matérias"

    def __str__(self):
        return self.name

class Topic(models.Model):
    STATUS_CHOICES = [
        ('not_started', '⚪ Não iniciado'),
        ('studying', '🔵 Estudando'),
        ('studied', '🟡 Estudado'),
        ('review_pending', '🟠 Revisão pendente'),
        ('needs_reinforcement', '🔴 Precisa reforço'),
        ('mastered', '🟢 Dominado'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics', verbose_name="Matéria")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="Tópico pai")
    name = models.CharField(max_length=200, verbose_name="Nome")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name="Status")
    priority = models.PositiveSmallIntegerField(default=0, verbose_name="Prioridade")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")
    tags = models.ManyToManyField('notes.Tag', blank=True, related_name='topics', verbose_name="Tags")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['subject', 'parent', 'name']
        verbose_name = "Tópico"
        verbose_name_plural = "Tópicos"

    def __str__(self):
        return self.name

    def get_full_path(self):
        names = [self.name]
        parent = self.parent
        while parent:
            names.append(parent.name)
            parent = parent.parent
        return ' → '.join(reversed(names))
