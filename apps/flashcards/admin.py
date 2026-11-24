from django.contrib import admin
from .models import Flashcard

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['pergunta', 'user', 'topic', 'proxima_revisao', 'vezes_revisado']
    list_filter = ['user', 'topic']
    search_fields = ['pergunta', 'resposta']
