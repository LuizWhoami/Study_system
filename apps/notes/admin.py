from django.contrib import admin
from .models import Tag, Note
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color']
    list_filter = ['user']
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'topic', 'is_favorite', 'updated_at']
    list_filter = ['user', 'topic', 'is_favorite']
    search_fields = ['title', 'content']
