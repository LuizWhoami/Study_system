from django.contrib import admin
from .models import Question

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['enunciado', 'topic', 'user', 'dificuldade', 'created_at']
    list_filter = ['user', 'topic', 'dificuldade']
    search_fields = ['enunciado', 'explicacao']
