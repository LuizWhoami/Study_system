from django.contrib import admin
from .models import Tag, Note, NoteFolder


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color']
    list_filter = ['user']


@admin.register(NoteFolder)
class NoteFolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'note_count', 'updated_at']
    list_filter = ['user']
    search_fields = ['name', 'description']

    def note_count(self, obj):
        return obj.notes.count()
    note_count.short_description = "Notas"


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'folder', 'topic', 'is_favorite', 'updated_at']
    list_filter = ['user', 'folder', 'topic', 'is_favorite']
    search_fields = ['title', 'content']
