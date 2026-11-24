from django.db import models
from django.conf import settings
from apps.subjects.models import Topic

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nome")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags', verbose_name="Usuário")
    color = models.CharField(max_length=7, default='#6c757d', verbose_name="Cor")

    class Meta:
        unique_together = ['user', 'name']
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name

class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes', verbose_name="Usuário")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes', verbose_name="Tópico")
    title = models.CharField(max_length=200, verbose_name="Título")
    content = models.TextField(verbose_name="Conteúdo")
    tags = models.ManyToManyField(Tag, blank=True, related_name='notes', verbose_name="Tags")
    is_favorite = models.BooleanField(default=False, verbose_name="Favorito")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Nota"
        verbose_name_plural = "Notas"

    def __str__(self):
        return self.title
